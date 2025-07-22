# services/memory_manager_with_validation.py
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func
from datetime import datetime
import json
import numpy as np

from sparkjar_crew.shared.database.models import MemoryEntities, MemoryRelations, ObjectSchemas, MemoryObservations
from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate, RelationCreate, ObservationAdd
from .embeddings import EmbeddingService
from .actor_validator import ActorValidator, InvalidActorError
import jsonschema
from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db_session: Session, embedding_service: EmbeddingService, actor_validator: Optional[ActorValidator] = None):
        self.db = db_session
        self.embedding_service = embedding_service
        self.actor_validator = actor_validator
        self._schema_cache = {}  # Cache schemas for performance

    async def _validate_actor(self, actor_type: str, actor_id: UUID) -> None:
        """Validate actor reference if validator is available."""
        if self.actor_validator:
            is_valid = await self.actor_validator.validate_actor(actor_type, actor_id)
            if not is_valid:
                raise InvalidActorError(
                    actor_type=actor_type,
                    actor_id=actor_id,
                    message=f"Actor {actor_id} of type {actor_type} does not exist"
                )

    def _get_base_filter(self, client_id: UUID, actor_type: str, actor_id: UUID):
        """Base filter for multi-tenant + actor scoping"""
        return and_(
            MemoryEntities.client_id == client_id,
            MemoryEntities.actor_type == actor_type,
            MemoryEntities.actor_id == actor_id,
            MemoryEntities.deleted_at.is_(None)
        )

    def _get_schema(self, schema_name: str) -> Dict[str, Any]:
        """Get schema from object_schemas table with caching"""
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]
        
        # Query based on your actual table structure
        query = text("""
            SELECT schema 
            FROM object_schemas 
            WHERE name = :schema_name 
            AND object_type IN ('memory_observation', 'memory_entity_metadata')
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = self.db.execute(query, {"schema_name": schema_name}).first()
        
        if result:
            schema = result[0]  # schema_definition is JSONB
            self._schema_cache[schema_name] = schema
            return schema
        
        # Return None to indicate schema not found
        return None

    def _validate_observations(self, observations: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """Validate observations against schemas from object_schemas table"""
        validated_observations = []
        
        for obs in observations:
            try:
                # Determine schema name based on observation type
                obs_type = obs.get('type', 'general')
                
                # Map observation types to schema names
                schema_mapping = {
                    'skill': 'skill_observation',
                    'database_ref': 'database_ref_observation',
                    'writing_pattern': 'writing_pattern_observation',
                    'general': 'base_observation',
                    'fact': 'base_observation'
                }
                
                schema_name = schema_mapping.get(obs_type, 'base_observation')
                schema = self._get_schema(schema_name)
                
                if not schema:
                    # Fallback to base_observation
                    schema = self._get_schema('base_observation')
                    schema_name = 'base_observation'
                
                if not schema:
                    # If even base_observation is not found, use a minimal schema
                    schema = {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "source": {"type": "string"},
                            "timestamp": {"type": "string"},
                        },
                        "required": ["content"]
                    }
                
                # Transform observation to match schema structure
                # Your schemas expect 'content' field, but observations have 'value'
                timestamp = obs.get('timestamp', datetime.utcnow())
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()
                
                obs_for_validation = {
                    "content": str(obs.get('value', '')),
                    "source": obs.get('source', 'unknown'),
                    "timestamp": timestamp
                }
                
                # Add additional fields based on observation type
                if obs_type == 'skill':
                    obs_for_validation["proficiency_level"] = obs.get('proficiency_level', 'intermediate')
                    obs_for_validation["years_experience"] = obs.get('years_experience', 0)
                    obs_for_validation["last_used"] = obs.get('last_used', timestamp)
                elif obs_type == 'database_ref':
                    obs_for_validation["table_name"] = obs.get('table_name', '')
                    obs_for_validation["column_name"] = obs.get('column_name', '')
                    obs_for_validation["record_id"] = obs.get('record_id', '')
                    obs_for_validation["relationship_type"] = obs.get('relationship_type', '')
                
                # Validate against schema
                validate(instance=obs_for_validation, schema=schema)
                
                # Add the validated observation with metadata
                validated_observations.append({
                    **obs,
                    '_schema_name': schema_name,
                    '_validated_at': datetime.utcnow().isoformat(),
                    '_validation_passed': True
                })
                
            except ValidationError as e:
                # Log validation error but continue processing
                logger.error(f"Observation validation error for type {obs_type}: {e.message}")
                validated_observations.append({
                    **obs,
                    '_schema_name': schema_name if 'schema_name' in locals() else 'unknown',
                    '_validated_at': datetime.utcnow().isoformat(),
                    '_validation_passed': False,
                    '_validation_error': str(e.message)
                })
        
        return validated_observations

    def _validate_entity_metadata(self, metadata: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Validate entity metadata against schemas"""
        try:
            # Get metadata schema based on entity type
            schema_name = f"{entity_type}_metadata"
            schema = self._get_schema(schema_name)
            
            if not schema:
                # Fallback to generic entity metadata schema
                schema = self._get_schema('entity_metadata')
            
            if schema:
                validate(instance=metadata, schema=schema)
                metadata['_validation'] = {
                    'schema_name': schema_name,
                    'validated_at': datetime.utcnow().isoformat(),
                    'passed': True
                }
            
        except ValidationError as e:
            # Log but don't fail - add validation metadata
            logger.error(f"Metadata validation error for entity type {entity_type}: {e.message}")
            metadata['_validation'] = {
                'schema_name': schema_name if 'schema_name' in locals() else 'unknown',
                'validated_at': datetime.utcnow().isoformat(),
                'passed': False,
                'error': str(e.message)
            }
        
        return metadata

    async def create_entities(
        self, 
        client_id: UUID, 
        actor_type: str, 
        actor_id: UUID, 
        entities: List[EntityCreate]
    ) -> List[Dict[str, Any]]:
        """Create multiple entities with observations, with actor validation"""
        
        # Validate actor before proceeding
        await self._validate_actor(actor_type, actor_id)
        
        created_entities = []
        
        for entity_data in entities:
            # Check if entity already exists
            existing = self.db.query(MemoryEntities).filter(
                and_(
                    MemoryEntities.client_id == client_id,
                    MemoryEntities.actor_type == actor_type,
                    MemoryEntities.actor_id == actor_id,
                    MemoryEntities.entity_name == entity_data.name,
                    MemoryEntities.entity_type == entity_data.entityType,
                    MemoryEntities.deleted_at.is_(None)
                )
            ).first()
            
            if existing:
                # Get existing observations
                existing_obs = self.db.query(MemoryObservations).filter(
                    MemoryObservations.entity_id == existing.id
                ).all()
                
                # Create new observations
                for obs in entity_data.observations:
                    obs_value = obs.value if isinstance(obs.value, dict) else {"value": obs.value}
                    for key, value in obs_value.items():
                        if isinstance(value, datetime):
                            obs_value[key] = value.isoformat()
                    
                    observation = MemoryObservations(
                        id=uuid4(),
                        entity_id=existing.id,
                        observation_type=obs.type,
                        observation_value=obs_value,
                        source=obs.source or 'api',
                        created_at=datetime.utcnow()
                    )
                    self.db.add(observation)
                
                # Regenerate embedding
                all_observations = []
                for o in existing_obs:
                    obs_dict = o.observation_value if isinstance(o.observation_value, dict) else {}
                    obs_dict['type'] = o.observation_type
                    obs_dict['source'] = o.source
                    all_observations.append(obs_dict)
                
                for obs in entity_data.observations:
                    obs_dict = obs.dict()
                    all_observations.append(obs_dict)
                
                text_content = self.embedding_service.prepare_entity_text_from_data(
                    entity_data.name, entity_data.entityType, all_observations
                )
                existing.embedding = await self.embedding_service.generate_embedding(text_content)
                existing.updated_at = datetime.utcnow()
                if getattr(entity_data, "aliasOf", None) is not None:
                    existing.alias_of = entity_data.aliasOf
                if getattr(entity_data, "identityConfidence", None) is not None:
                    existing.identity_confidence = entity_data.identityConfidence

                created_entities.append(self._entity_to_dict(existing))
                continue
            
            # Create new entity
            observations = [obs.model_dump() for obs in entity_data.observations]
            
            # Validate observations against schemas
            validated_observations = self._validate_observations(observations, entity_data.entityType)
            
            # Validate entity metadata
            validated_metadata = self._validate_entity_metadata(
                entity_data.metadata or {}, 
                entity_data.entityType
            )
            
            # Generate embedding
            text_content = self.embedding_service.prepare_entity_text_from_data(
                entity_data.name, entity_data.entityType, validated_observations
            )
            embedding = await self.embedding_service.generate_embedding(text_content)
            
            # Create entity record
            entity = MemoryEntities(
                id=uuid4(),
                client_id=client_id,
                actor_type=actor_type,
                actor_id=actor_id,
                entity_name=entity_data.name,
                entity_type=entity_data.entityType,
                embedding=embedding,
                metadata_json=validated_metadata,
                alias_of=getattr(entity_data, "aliasOf", None),
                identity_confidence=getattr(entity_data, "identityConfidence", None),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(entity)
            self.db.flush()  # Get the ID
            
            # Create observations for the entity
            if validated_observations:
                for obs in validated_observations:
                    # Convert any datetime objects in observation to strings
                    obs_value = obs.copy()
                    for key, value in obs_value.items():
                        if isinstance(value, datetime):
                            obs_value[key] = value.isoformat()
                    
                    observation = MemoryObservations(
                        id=uuid4(),
                        entity_id=entity.id,
                        observation_type=obs.get('type'),
                        observation_value=obs_value,
                        source=obs.get('source', 'api'),
                        created_at=datetime.utcnow()
                    )
                    self.db.add(observation)
            
            created_entities.append(self._entity_to_dict(entity))
        
        self.db.commit()
        return created_entities

    async def create_relation(
        self, 
        client_id: UUID, 
        actor_type: str, 
        actor_id: UUID,
        relation: RelationCreate
    ) -> Dict[str, Any]:
        """Create a relationship between entities, with actor validation"""
        
        # Validate actor before proceeding
        await self._validate_actor(actor_type, actor_id)
        
        # Verify both entities exist and belong to this actor
        from_entity = self.db.query(MemoryEntities).filter(
            and_(
                MemoryEntities.id == relation.fromId,
                MemoryEntities.client_id == client_id,
                MemoryEntities.actor_type == actor_type,
                MemoryEntities.actor_id == actor_id,
                MemoryEntities.deleted_at.is_(None)
            )
        ).first()
        
        to_entity = self.db.query(MemoryEntities).filter(
            and_(
                MemoryEntities.id == relation.toId,
                MemoryEntities.client_id == client_id,
                MemoryEntities.actor_type == actor_type,
                MemoryEntities.actor_id == actor_id,
                MemoryEntities.deleted_at.is_(None)
            )
        ).first()
        
        if not from_entity or not to_entity:
            raise ValueError("One or both entities not found or don't belong to this actor")
        
        # Check if relation already exists
        existing = self.db.query(MemoryRelations).filter(
            and_(
                MemoryRelations.from_entity_id == relation.fromId,
                MemoryRelations.to_entity_id == relation.toId,
                MemoryRelations.relation_type == relation.relationType,
                MemoryRelations.deleted_at.is_(None)
            )
        ).first()
        
        if existing:
            # Update confidence if provided
            if relation.confidence is not None:
                existing.confidence = relation.confidence
                existing.updated_at = datetime.utcnow()
                self.db.commit()
            return self._relation_to_dict(existing)
        
        # Create new relation
        new_relation = MemoryRelations(
            id=uuid4(),
            from_entity_id=relation.fromId,
            to_entity_id=relation.toId,
            relation_type=relation.relationType,
            confidence=relation.confidence or 1.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_relation)
        self.db.commit()
        
        return self._relation_to_dict(new_relation)

    def _entity_to_dict(self, entity: MemoryEntities) -> Dict[str, Any]:
        """Convert entity ORM object to dictionary"""
        return {
            "id": str(entity.id),
            "name": entity.entity_name,
            "entityType": entity.entity_type,
            "metadata": entity.metadata_json or {},
            "aliasOf": str(entity.alias_of) if entity.alias_of else None,
            "identityConfidence": entity.identity_confidence,
            "createdAt": entity.created_at.isoformat() if entity.created_at else None,
            "updatedAt": entity.updated_at.isoformat() if entity.updated_at else None
        }

    def _relation_to_dict(self, relation: MemoryRelations) -> Dict[str, Any]:
        """Convert relation ORM object to dictionary"""
        return {
            "id": str(relation.id),
            "fromId": str(relation.from_entity_id),
            "toId": str(relation.to_entity_id),
            "relationType": relation.relation_type,
            "confidence": relation.confidence,
            "createdAt": relation.created_at.isoformat() if relation.created_at else None,
            "updatedAt": relation.updated_at.isoformat() if relation.updated_at else None
        }

    async def upsert_entities(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        entities: List[EntityCreate],
        skill_module_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Upsert entities with skill module context support.
        
        This method creates new entities or updates existing ones based on entity_name.
        If skill_module_id is provided and actor is a synth, memories are created
        in the skill module context instead of the synth's direct context.
        
        Args:
            client_id: Client ID for multi-tenancy
            actor_type: Type of actor creating/updating the entities  
            actor_id: ID of the actor
            entities: List of entities to upsert
            skill_module_id: Optional skill module context for synth actors
            
        Returns:
            List of created/updated entities
        """
        # Validate the requesting actor
        await self._validate_actor(actor_type, actor_id)
        
        # If skill_module_id is provided, validate it and check permissions
        effective_actor_type = actor_type
        effective_actor_id = actor_id
        
        if skill_module_id:
            if actor_type != 'synth':
                raise ValueError("skill_module_id can only be used by synth actors")
            
            # Validate skill module exists
            await self._validate_actor('skill_module', skill_module_id)
            
            # Check if synth is subscribed to this skill module
            from sparkjar_crew.shared.database.models import SynthSkillSubscriptions
            subscription = self.db.query(SynthSkillSubscriptions).filter(
                SynthSkillSubscriptions.synth_id == actor_id,
                SynthSkillSubscriptions.skill_module_id == skill_module_id,
                SynthSkillSubscriptions.active == True
            ).first()
            
            if not subscription:
                raise ValueError(f"Synth {actor_id} is not subscribed to skill module {skill_module_id}")
            
            # Use skill module context for the entities
            effective_actor_type = 'skill_module'
            effective_actor_id = skill_module_id
        
        results = []
        
        for entity_data in entities:
            # Check if entity already exists
            existing = self.db.query(MemoryEntities).filter(
                MemoryEntities.client_id == client_id,
                MemoryEntities.actor_type == effective_actor_type,
                MemoryEntities.actor_id == effective_actor_id,
                MemoryEntities.entity_name == entity_data.entity_name,
                MemoryEntities.deleted_at.is_(None)
            ).first()
            
            if existing:
                # Update existing entity
                existing.entity_type = entity_data.entity_type
                
                # Validate and merge observations
                validated_observations = self._validate_observations(
                    entity_data.observations + (existing.observations or []),
                    entity_data.entity_type
                )
                existing.observations = validated_observations
                
                # Validate and update metadata
                validated_metadata = self._validate_entity_metadata(
                    entity_data.metadata or {},
                    entity_data.entity_type
                )
                existing.metadata_json = validated_metadata
                
                # Update embedding
                if entity_data.entity_name:
                    embedding = await self.embedding_service.generate_embedding(
                        f"{entity_data.entity_name} {entity_data.entity_type}"
                    )
                    existing.embedding = embedding
                
                existing.updated_at = datetime.utcnow()
                
                results.append(self._entity_to_dict(existing))
            else:
                # Create new entity
                validated_observations = self._validate_observations(
                    entity_data.observations,
                    entity_data.entity_type
                )
                
                validated_metadata = self._validate_entity_metadata(
                    entity_data.metadata or {},
                    entity_data.entity_type
                )
                
                # Generate embedding
                embedding = await self.embedding_service.generate_embedding(
                    f"{entity_data.entity_name} {entity_data.entity_type}"
                )
                
                entity = MemoryEntities(
                    client_id=client_id,
                    actor_type=effective_actor_type,
                    actor_id=effective_actor_id,
                    entity_name=entity_data.entity_name,
                    entity_type=entity_data.entity_type,
                    observations=validated_observations,
                    embedding=embedding,
                    metadata_json=validated_metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(entity)
                self.db.flush()
                
                results.append(self._entity_to_dict(entity))
        
        # Commit all changes
        self.db.commit()
        
        # Log the operation
        logger.info(
            f"Upserted {len(results)} entities for {actor_type} {actor_id}"
            f"{f' in skill_module context {skill_module_id}' if skill_module_id else ''}"
        )
        
        return results
    
    # Note: All other methods remain the same, just add actor validation
    # at the beginning of methods that create or update data
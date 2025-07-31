# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# services/memory_manager.py
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func
from datetime import datetime
import json
import numpy as np
import logging

from .actor_validator import ActorValidator, InvalidActorError

from sparkjar_crew.shared.database.models import MemoryEntities, MemoryRelations, MemoryObservations
from sparkjar_crew.shared.schemas.memory_schemas import EntityCreate, RelationCreate, ObservationAdd
from .embeddings import EmbeddingService

class MemoryManager:
    def __init__(
        self,
        db_session: Session,
        embedding_service: EmbeddingService,
        actor_validator: Optional[ActorValidator] = None,
    ) -> None:
        self.db = db_session
        self.embedding_service = embedding_service
        self.actor_validator = actor_validator
        self._schema_cache: Dict[str, Any] = {}
        self._synth_class_cache: Dict[str, Any] = {}
        self._cache_ttl = 300
        self._cache_timestamps: Dict[str, float] = {}

    async def _validate_actor(self, actor_type: str, actor_id: UUID) -> None:
        """Actor validation disabled."""
        return

    def _get_base_filter(self, client_id: UUID, actor_type: str, actor_id: UUID):
        """Base filter for multi-tenant + actor scoping"""
        return and_(
            MemoryEntities.client_id == client_id,
            MemoryEntities.actor_type == actor_type,
            MemoryEntities.actor_id == actor_id,
            MemoryEntities.deleted_at.is_(None)
        )

    def _get_schema(self, schema_name: str) -> Dict[str, Any]:
        """Schema lookup disabled."""
        return None

    def _get_synth_class_id(self, actor_type: str, actor_id: UUID) -> Optional[int]:
        """Get cached synth_class_id for a synth actor."""
        if actor_type != "synth":
            return None

        cache_key = f"synth_class:{actor_id}"
        if cache_key in self._synth_class_cache:
            ts = self._cache_timestamps.get(cache_key, 0)
            if (datetime.utcnow().timestamp() - ts) < self._cache_ttl:
                return self._synth_class_cache[cache_key]

        try:
            from services.crew_api.src.database.models import Synths

            synth = self.db.query(Synths).filter(Synths.id == actor_id).first()
            if synth and synth.synth_classes_id:
                self._synth_class_cache[cache_key] = synth.synth_classes_id
                self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
                return synth.synth_classes_id
        except Exception as exc:  # pragma: no cover - external optional dep
            logging.getLogger(__name__).error("Error fetching synth class", exc_info=exc)

        return None

    def _get_synth_skill_modules(self, actor_type: str, actor_id: UUID) -> List[UUID]:
        """Return IDs of skill modules a synth is subscribed to."""
        if actor_type != "synth":
            return []

        cache_key = f"skill_modules:{actor_id}"
        if cache_key in self._synth_class_cache:
            ts = self._cache_timestamps.get(cache_key, 0)
            if (datetime.utcnow().timestamp() - ts) < self._cache_ttl:
                return self._synth_class_cache[cache_key]

        try:
            from sparkjar_crew.shared.database.models import SynthSkillSubscriptions

            subs = (
                self.db.query(SynthSkillSubscriptions)
                .filter(SynthSkillSubscriptions.synth_id == actor_id, SynthSkillSubscriptions.active == True)
                .all()
            )
            ids = [sub.skill_module_id for sub in subs]
            self._synth_class_cache[cache_key] = ids
            self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
            return ids
        except Exception as exc:  # pragma: no cover
            logging.getLogger(__name__).error("Error fetching skill modules", exc_info=exc)
            return []

    def _build_hierarchical_filter(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        include_synth_class: bool = True,
        include_client: bool = False,
        include_skill_module: bool = True,
    ):
        filters = [
            and_(
                MemoryEntities.client_id == client_id,
                MemoryEntities.actor_type == actor_type,
                MemoryEntities.actor_id == actor_id,
                MemoryEntities.deleted_at.is_(None),
            )
        ]

        if actor_type == "synth" and include_synth_class:
            synth_class_id = self._get_synth_class_id(actor_type, actor_id)
            if synth_class_id:
                filters.append(
                    and_(
                        MemoryEntities.actor_type == "synth_class",
                        MemoryEntities.actor_id == str(synth_class_id),
                        MemoryEntities.deleted_at.is_(None),
                    )
                )

        if actor_type == "synth" and include_skill_module:
            module_ids = self._get_synth_skill_modules(actor_type, actor_id)
            for mid in module_ids:
                filters.append(
                    and_(
                        MemoryEntities.client_id == client_id,
                        MemoryEntities.actor_type == "skill_module",
                        MemoryEntities.actor_id == str(mid),
                        MemoryEntities.deleted_at.is_(None),
                    )
                )

        if include_client:
            filters.append(
                and_(
                    MemoryEntities.client_id == client_id,
                    MemoryEntities.actor_type == "client",
                    MemoryEntities.actor_id == str(client_id),
                    MemoryEntities.deleted_at.is_(None),
                )
            )

        return filters[0] if len(filters) == 1 else or_(*filters)

    async def search_hierarchical_memories(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        query: str,
        entity_types: Optional[List[str]] = None,
        include_synth_class: bool = True,
        include_client: bool = False,
        include_skill_module: bool = True,
        limit: int = 10,
        min_confidence: float = 0.0,
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding_service.generate_embedding(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        hierarchical_filter = self._build_hierarchical_filter(
            client_id,
            actor_type,
            actor_id,
            include_synth_class=include_synth_class,
            include_client=include_client,
            include_skill_module=include_skill_module,
        )

        base_query = (
            self.db.query(
                MemoryEntities,
                (1 - func.cosine_distance(MemoryEntities.embedding, embedding_str)).label("similarity"),
                MemoryEntities.actor_type.label("access_context"),
            )
            .filter(hierarchical_filter)
        )

        if entity_types:
            base_query = base_query.filter(MemoryEntities.entity_type.in_(entity_types))

        results = base_query.order_by(func.cosine_distance(MemoryEntities.embedding, embedding_str)).all()

        formatted_results = []
        for entity, similarity, access_context in results:
            if similarity is not None and float(similarity) < min_confidence:
                continue
            entity_dict = self._entity_to_dict(entity)
            entity_dict["similarity"] = float(similarity)
            entity_dict["access_context"] = access_context
            formatted_results.append(entity_dict)

        return formatted_results[:limit]

    def _validate_observations(self, observations: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """Validation disabled - return observations unchanged."""
        return observations

    def _validate_entity_metadata(self, metadata: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Validation disabled - return metadata unchanged."""
        return metadata

    async def create_entities(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        entities: List[EntityCreate]
    ) -> List[Dict[str, Any]]:
        """Create multiple entities with automatic embedding generation"""
        await self._validate_actor(actor_type, actor_id)
        created_entities = []
        
        for entity_data in entities:
            # Check for existing entity
            existing = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == entity_data.name
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

    async def upsert_entities(
        self,
        actor_type: str,
        actor_id: UUID,
        entities: List[EntityCreate],
    ) -> List[Dict[str, Any]]:
        """Create or update entities, merging observations and metadata."""
        await self._validate_actor(actor_type, actor_id)
        results = []

        for entity in entities:
            existing = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == entity.name,
                )
            ).first()

            if existing:
                if entity.metadata:
                    existing.metadata_json.update(entity.metadata)
                if getattr(entity, "aliasOf", None) is not None:
                    existing.alias_of = entity.aliasOf
                if getattr(entity, "identityConfidence", None) is not None:
                    existing.identity_confidence = entity.identityConfidence

                existing_obs = self.db.query(MemoryObservations).filter(
                    MemoryObservations.entity_id == existing.id
                ).all()
                existing_data = [
                    {
                        **(o.observation_value if isinstance(o.observation_value, dict) else {}),
                        "type": o.observation_type,
                    }
                    for o in existing_obs
                ]

                for obs in entity.observations:
                    obs_dict = obs.dict()
                    if not any(
                        d.get("type") == obs_dict.get("type") and d.get("value") == obs_dict.get("value")
                        for d in existing_data
                    ):
                        obs_val = obs.value if isinstance(obs.value, dict) else {"value": obs.value}
                        self.db.add(
                            MemoryObservations(
                                id=uuid4(),
                                entity_id=existing.id,
                                observation_type=obs.type,
                                observation_value=obs_val,
                                source=obs.source or "api",
                                created_at=datetime.utcnow(),
                            )
                        )
                existing.updated_at = datetime.utcnow()
                results.append(self._entity_to_dict(existing))
            else:
                created = await self.create_entities(actor_type, actor_id, [entity])
                results.extend(created)

        self.db.commit()
        return results

    async def create_relations(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        relations: List[RelationCreate]
    ) -> List[Dict[str, Any]]:
        """Create relationships between entities"""
        await self._validate_actor(actor_type, actor_id)
        created_relations = []
        
        for relation_data in relations:
            # Check for existing relation
            existing = self.db.query(MemoryRelations).filter(
                and_(
                    MemoryRelations.client_id == client_id,
                    MemoryRelations.actor_type == actor_type,
                    MemoryRelations.actor_id == actor_id,
                    MemoryRelations.from_entity_name == relation_data.from_entity_name,
                    MemoryRelations.to_entity_name == relation_data.to_entity_name,
                    MemoryRelations.relation_type == relation_data.relationType,
                    MemoryRelations.deleted_at.is_(None)
                )
            ).first()
            
            if existing:
                # Update metadata if provided
                if relation_data.metadata:
                    existing.metadata_json.update(relation_data.metadata)
                    existing.updated_at = datetime.utcnow()
                created_relations.append(self._relation_to_dict(existing))
                continue
            
            # Verify entities exist
            from_entity = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == relation_data.from_entity_name
                )
            ).first()
            
            to_entity = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == relation_data.to_entity_name
                )
            ).first()
            
            if not from_entity or not to_entity:
                continue  # Skip if entities don't exist
            
            # Create relation
            relation = MemoryRelations(
                id=uuid4(),
                client_id=client_id,
                actor_type=actor_type,
                actor_id=actor_id,
                from_entity_id=from_entity.id,
                to_entity_id=to_entity.id,
                relation_type=relation_data.relationType,
                metadata_json=relation_data.metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(relation)
            self.db.flush()
            created_relations.append(self._relation_to_dict(relation))
        
        self.db.commit()
        return created_relations

    async def add_observations(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        observations: List[ObservationAdd]
    ) -> List[Dict[str, Any]]:
        """Add observations to existing entities and regenerate embeddings"""
        await self._validate_actor(actor_type, actor_id)
        results = []
        
        for obs_data in observations:
            entity = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == obs_data.entityName
                )
            ).first()
            
            if not entity:
                raise ValueError(f"Entity '{obs_data.entityName}' not found")
            
            # Get existing observations
            existing_observations = self.db.query(MemoryObservations).filter(
                MemoryObservations.entity_id == entity.id
            ).all()
            
            # Convert existing observations to dicts for comparison
            existing_obs_list = []
            for obs in existing_observations:
                obs_dict = obs.observation_value if isinstance(obs.observation_value, dict) else {}
                obs_dict['type'] = obs.observation_type
                obs_dict['source'] = obs.source
                existing_obs_list.append(obs_dict)
            
            # Add new observations (avoid duplicates)
            new_obs = []
            added_observations = []
            for obs in obs_data.contents:
                obs_dict = obs.dict()
                # Check for duplicate observations
                if not any(
                    existing.get('type') == obs_dict.get('type') and 
                    existing.get('value') == obs_dict.get('value')
                    for existing in existing_obs_list
                ):
                    new_obs.append(obs_dict)
            
            # Validate and create new observations
            if new_obs:
                validated_new_obs = self._validate_observations(new_obs, entity.entity_type)
                for obs in validated_new_obs:
                    # Create new observation record
                    obs_value = obs.copy()
                    obs_type = obs_value.pop('type', 'general')
                    obs_source = obs_value.pop('source', 'api')
                    
                    # Convert datetime objects to strings
                    for key, value in obs_value.items():
                        if isinstance(value, datetime):
                            obs_value[key] = value.isoformat()
                    
                    observation = MemoryObservations(
                        id=uuid4(),
                        entity_id=entity.id,
                        observation_type=obs_type,
                        observation_value=obs_value,
                        source=obs_source,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(observation)
                    added_observations.append(obs)
                
                # Regenerate embedding with all observations
                all_observations = existing_obs_list + validated_new_obs
                text_content = self.embedding_service.prepare_entity_text_from_data(
                    entity.entity_name, entity.entity_type, all_observations
                )
                entity.embedding = await self.embedding_service.generate_embedding(text_content)
                entity.updated_at = datetime.utcnow()
            else:
                added_observations = []
            
            results.append({
                "entityName": obs_data.entityName,
                "addedObservations": len(added_observations),
                "totalObservations": len(existing_observations) + len(added_observations)
            })
        
        self.db.commit()
        return results

    async def search_nodes(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
        min_confidence: float = 0.0,
        include_hierarchy: bool = False,
    ) -> List[Dict[str, Any]]:
        """Semantic search using vector embeddings with optional hierarchy."""

        if include_hierarchy:
            return await self.search_hierarchical_memories(
                client_id,
                actor_type,
                actor_id,
                query,
                entity_types=entity_types,
                limit=limit,
                min_confidence=min_confidence,
            )
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Convert to SQL array format for pgvector (768 dimensions)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Build query with vector similarity
        base_query = self.db.query(
            MemoryEntities,
            (1 - func.cosine_distance(MemoryEntities.embedding, embedding_str)).label('similarity')
        ).filter(
            self._get_base_filter(client_id, actor_type, actor_id)
        )
        
        # Add entity type filter if specified
        if entity_types:
            base_query = base_query.filter(MemoryEntities.entity_type.in_(entity_types))
        
        results = base_query.order_by(
            func.cosine_distance(MemoryEntities.embedding, embedding_str)
        ).all()

        formatted_results = []
        for entity, similarity in results:
            if similarity is not None and float(similarity) < min_confidence:
                continue
            entity_dict = self._entity_to_dict(entity)
            entity_dict["similarity"] = float(similarity)
            formatted_results.append(entity_dict)

        return formatted_results[:limit]
    
    async def open_nodes(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        names: List[str]
    ) -> List[Dict[str, Any]]:
        """Get specific entities by name"""
        entities = self.db.query(MemoryEntities).filter(
            and_(
                self._get_base_filter(client_id, actor_type, actor_id),
                MemoryEntities.entity_name.in_(names)
            )
        ).all()
        
        return [self._entity_to_dict(entity) for entity in entities]
    
    async def read_graph(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID
    ) -> Dict[str, Any]:
        """Get all entities and relations for an actor"""
        # Get all entities
        entities = self.db.query(MemoryEntities).filter(
            self._get_base_filter(client_id, actor_type, actor_id)
        ).all()
        
        # Get all relations
        relations = self.db.query(MemoryRelations).filter(
            and_(
                MemoryRelations.client_id == client_id,
                MemoryRelations.actor_type == actor_type,
                MemoryRelations.actor_id == actor_id,
                MemoryRelations.deleted_at.is_(None)
            )
        ).all()
        
        return {
            "entities": [self._entity_to_dict(e) for e in entities],
            "relations": [self._relation_to_dict(r) for r in relations],
            "total_entities": len(entities),
            "total_relations": len(relations)
        }
    
    async def delete_entities(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        entity_names: List[str]
    ) -> Dict[str, Any]:
        """Soft delete entities and their relations"""
        now = datetime.utcnow()
        
        # Find entities to delete
        entities = self.db.query(MemoryEntities).filter(
            and_(
                self._get_base_filter(client_id, actor_type, actor_id),
                MemoryEntities.entity_name.in_(entity_names)
            )
        ).all()
        
        deleted_count = 0
        deleted_relations = 0
        
        for entity in entities:
            # Soft delete entity
            entity.deleted_at = now
            deleted_count += 1
            
            # Soft delete related relations
            relations = self.db.query(MemoryRelations).filter(
                and_(
                    MemoryRelations.client_id == client_id,
                    MemoryRelations.actor_type == actor_type,
                    MemoryRelations.actor_id == actor_id,
                    or_(
                        MemoryRelations.from_entity_id == entity.id,
                        MemoryRelations.to_entity_id == entity.id
                    ),
                    MemoryRelations.deleted_at.is_(None)
                )
            ).all()
            
            for relation in relations:
                relation.deleted_at = now
                deleted_relations += 1
        
        self.db.commit()
        
        return {
            "deleted_entities": deleted_count,
            "deleted_relations": deleted_relations
        }
    
    async def delete_relations(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        relations: List[Any]
    ) -> Dict[str, Any]:
        """Delete specific relations"""
        now = datetime.utcnow()
        deleted_count = 0
        
        for rel_spec in relations:
            relation = self.db.query(MemoryRelations).filter(
                and_(
                    MemoryRelations.client_id == client_id,
                    MemoryRelations.actor_type == actor_type,
                    MemoryRelations.actor_id == actor_id,
                    MemoryRelations.from_entity_name == rel_spec.from_entity_name,
                    MemoryRelations.to_entity_name == rel_spec.to_entity_name,
                    MemoryRelations.relation_type == rel_spec.relation_type,
                    MemoryRelations.deleted_at.is_(None)
                )
            ).first()
            
            if relation:
                relation.deleted_at = now
                deleted_count += 1
        
        self.db.commit()
        
        return {"deleted_relations": deleted_count}
    
    def _entity_to_dict(self, entity: MemoryEntities) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        # Load observations from the database
        observations = self.db.query(MemoryObservations).filter(
            MemoryObservations.entity_id == entity.id
        ).all()
        
        obs_list = []
        for obs in observations:
            obs_dict = obs.observation_value if isinstance(obs.observation_value, dict) else {}
            obs_dict['type'] = obs.observation_type
            obs_dict['source'] = obs.source
            obs_list.append(obs_dict)
        
        return {
            "id": str(entity.id),
            "entity_name": entity.entity_name,
            "entity_type": entity.entity_type,
            "observations": obs_list,
            "metadata": entity.metadata_json or {},
            "identity_confidence": getattr(entity, "identity_confidence", None),
            "alias_of": getattr(entity, "alias_of", None),
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }
    
    def _relation_to_dict(self, relation: MemoryRelations) -> Dict[str, Any]:
        """Convert relation to dictionary"""
        # Get entity names from the database
        from_entity = self.db.query(MemoryEntities).filter(
            MemoryEntities.id == relation.from_entity_id
        ).first()
        to_entity = self.db.query(MemoryEntities).filter(
            MemoryEntities.id == relation.to_entity_id
        ).first()
        
        return {
            "id": str(relation.id),
            "from_entity_name": from_entity.entity_name if from_entity else None,
            "from_entity_type": from_entity.entity_type if from_entity else None,
            "to_entity_name": to_entity.entity_name if to_entity else None,
            "to_entity_type": to_entity.entity_type if to_entity else None,
            "relation_type": relation.relation_type,
            "metadata": relation.metadata_json or {},
            "created_at": relation.created_at.isoformat() if relation.created_at else None
        }
    
    async def remember_conversation(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        conversation_text: str,
        participants: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and store knowledge from conversation transcripts.
        
        Analyzes conversation text to identify entities and relationships,
        extracts skills, insights, and patterns mentioned,
        creates or updates entities automatically,
        and links conversation participants and topics.
        """
        results = {
            "entities_created": [],
            "entities_updated": [],
            "relations_created": [],
            "observations_added": []
        }
        
        # First, ensure all participants exist as entities
        for participant_name in participants:
            existing = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == participant_name
                )
            ).first()
            
            if not existing:
                # Create participant entity
                participant_entity = await self.create_entities(
                    client_id, actor_type, actor_id,
                    [EntityCreate(
                        name=participant_name,
                        entityType="person",
                        observations=[Observation(
                            type="fact",
                            value=f"Participant in conversation on {context.get('date', datetime.utcnow().isoformat())}",
                            source="conversation"
                        )],
                        metadata={"created_from": "conversation"}
                    )]
                )
                results["entities_created"].extend(participant_entity)
        
        # Extract entities and skills from conversation
        # This is a simplified extraction - in production, you'd use NLP/LLM
        lines = conversation_text.split('\n')
        mentioned_skills = []
        mentioned_projects = []
        
        # Simple pattern matching for demonstration
        skill_keywords = ["knows", "expert", "skilled", "experience with", "worked with", "uses"]
        project_keywords = ["project", "working on", "building", "developing", "initiative"]
        
        for line in lines:
            line_lower = line.lower()
            
            # Extract skills
            for keyword in skill_keywords:
                if keyword in line_lower:
                    # Extract the skill after the keyword
                    parts = line_lower.split(keyword)
                    if len(parts) > 1:
                        skill_text = parts[1].strip()[:50]  # Limit length
                        if skill_text:
                            mentioned_skills.append(skill_text)
            
            # Extract projects
            for keyword in project_keywords:
                if keyword in line_lower:
                    parts = line_lower.split(keyword)
                    if len(parts) > 1:
                        project_text = parts[1].strip()[:50]
                        if project_text:
                            mentioned_projects.append(project_text)
        
        # Add skills as observations to participants
        if mentioned_skills and participants:
            for skill in mentioned_skills[:5]:  # Limit to 5 skills
                # Add to first participant for simplicity
                obs_result = await self.add_observations(
                    client_id, actor_type, actor_id,
                    [ObservationAdd(
                        entityName=participants[0],
                        contents=[ObservationContent(
                            type="skill",
                            value=skill,
                            source="conversation",
                            context={"meeting_type": context.get("meeting_type", "general")}
                        )]
                    )]
                )
                results["observations_added"].extend(obs_result)
        
        # Create event entity for the conversation
        event_name = f"Conversation_{context.get('date', datetime.utcnow().strftime('%Y%m%d_%H%M%S'))}"
        event_entity = await self.create_entities(
            client_id, actor_type, actor_id,
            [EntityCreate(
                name=event_name,
                entityType="event",
                observations=[Observation(
                    type="fact",
                    value=f"Conversation with {len(participants)} participants",
                    source="system",
                    context=context
                )],
                metadata={
                    "participants": participants,
                    "context": context,
                    "skills_discussed": mentioned_skills,
                    "projects_mentioned": mentioned_projects
                }
            )]
        )
        results["entities_created"].extend(event_entity)
        
        # Link participants to the event
        for participant in participants:
            relation = await self.create_relations(
                client_id, actor_type, actor_id,
                [RelationCreate(
                    from_entity_name=participant,
                    to_entity_name=event_name,
                    relationType="participated_in",
                    metadata={"role": "participant"}
                )]
            )
            results["relations_created"].extend(relation)
        
        return results
    
    async def find_connections(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        from_entity: str,
        to_entity: Optional[str] = None,
        max_hops: int = 3,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Find paths between entities using graph traversal.
        
        Finds shortest paths and all paths between entities,
        discovers indirect connections,
        and maps relationship strength and frequency.
        """
        if max_hops > 5:
            max_hops = 5  # Limit to prevent excessive computation
        
        # Verify from_entity exists
        from_entity_obj = self.db.query(MemoryEntities).filter(
            and_(
                self._get_base_filter(client_id, actor_type, actor_id),
                MemoryEntities.entity_name == from_entity
            )
        ).first()
        
        if not from_entity_obj:
            return {"error": f"Entity '{from_entity}' not found"}
        
        # If to_entity is specified, verify it exists
        if to_entity:
            to_entity_obj = self.db.query(MemoryEntities).filter(
                and_(
                    self._get_base_filter(client_id, actor_type, actor_id),
                    MemoryEntities.entity_name == to_entity
                )
            ).first()
            
            if not to_entity_obj:
                return {"error": f"Entity '{to_entity}' not found"}
        
        # Build relationship filter
        rel_filter = and_(
            MemoryRelations.client_id == client_id,
            MemoryRelations.actor_type == actor_type,
            MemoryRelations.actor_id == actor_id,
            MemoryRelations.deleted_at.is_(None)
        )
        
        if relationship_types:
            rel_filter = and_(
                rel_filter,
                MemoryRelations.relation_type.in_(relationship_types)
            )
        
        # Get all relations for graph traversal
        all_relations = self.db.query(MemoryRelations).filter(rel_filter).all()
        
        # Build adjacency list
        graph = {}
        for rel in all_relations:
            if rel.from_entity_name not in graph:
                graph[rel.from_entity_name] = []
            graph[rel.from_entity_name].append({
                "to": rel.to_entity_name,
                "type": rel.relation_type,
                "metadata": rel.metadata_json
            })
            
            # Add reverse edge for bidirectional traversal
            if rel.to_entity_name not in graph:
                graph[rel.to_entity_name] = []
            graph[rel.to_entity_name].append({
                "to": rel.from_entity_name,
                "type": f"reverse_{rel.relation_type}",
                "metadata": rel.metadata_json
            })
        
        # BFS to find paths
        paths = []
        visited = set()
        queue = [(from_entity, [from_entity], [])]
        
        while queue:
            current, path, relationships = queue.pop(0)
            
            if len(path) > max_hops + 1:
                continue
            
            if to_entity and current == to_entity:
                paths.append({
                    "path": path,
                    "relationships": relationships,
                    "length": len(path) - 1
                })
                continue
            
            if current in visited and to_entity:
                continue
            
            visited.add(current)
            
            # Explore neighbors
            if current in graph:
                for neighbor in graph[current]:
                    if neighbor["to"] not in path:  # Avoid cycles
                        new_path = path + [neighbor["to"]]
                        new_rels = relationships + [{
                            "from": current,
                            "to": neighbor["to"],
                            "type": neighbor["type"],
                            "metadata": neighbor["metadata"]
                        }]
                        
                        if not to_entity and len(new_path) <= max_hops + 1:
                            # If no target specified, collect all reachable entities
                            paths.append({
                                "path": new_path,
                                "relationships": new_rels,
                                "length": len(new_path) - 1
                            })
                        
                        queue.append((neighbor["to"], new_path, new_rels))
        
        # Sort paths by length
        paths.sort(key=lambda p: p["length"])
        
        # If finding all connections, group by target entity
        if not to_entity:
            connections_by_entity = {}
            for path_info in paths:
                target = path_info["path"][-1]
                if target != from_entity:
                    if target not in connections_by_entity:
                        connections_by_entity[target] = []
                    connections_by_entity[target].append(path_info)
            
            return {
                "from_entity": from_entity,
                "connections": connections_by_entity,
                "total_connected_entities": len(connections_by_entity)
            }
        
        return {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "paths": paths[:10],  # Limit to 10 paths
            "shortest_path_length": paths[0]["length"] if paths else None,
            "total_paths_found": len(paths)
        }
    
    async def get_client_insights(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID
    ) -> Dict[str, Any]:
        """Generate insights and analytics about the client's knowledge graph.
        
        Identifies knowledge gaps and clusters,
        shows skill distribution across people,
        highlights underutilized expertise,
        and suggests relationship opportunities.
        """
        insights = {
            "summary": {},
            "skill_distribution": {},
            "knowledge_gaps": [],
            "underutilized_expertise": [],
            "collaboration_opportunities": [],
            "entity_statistics": {},
            "relationship_statistics": {}
        }
        
        # Get all entities
        entities = self.db.query(MemoryEntities).filter(
            self._get_base_filter(client_id, actor_type, actor_id)
        ).all()
        
        # Get all relations
        relations = self.db.query(MemoryRelations).filter(
            and_(
                MemoryRelations.client_id == client_id,
                MemoryRelations.actor_type == actor_type,
                MemoryRelations.actor_id == actor_id,
                MemoryRelations.deleted_at.is_(None)
            )
        ).all()
        
        # Entity statistics
        entity_types = {}
        people_entities = []
        project_entities = []
        skill_observations = {}
        
        for entity in entities:
            entity_type = entity.entity_type
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
            
            if entity_type == "person":
                people_entities.append(entity)
                
                # Extract skills from observations
                for obs in entity.observations:
                    if obs.get("type") == "skill":
                        skill = obs.get("value", "")
                        if skill not in skill_observations:
                            skill_observations[skill] = []
                        skill_observations[skill].append({
                            "person": entity.entity_name,
                            "proficiency": obs.get("proficiency_level", "unknown")
                        })
            
            elif entity_type == "project":
                project_entities.append(entity)
        
        insights["entity_statistics"] = {
            "total_entities": len(entities),
            "by_type": entity_types
        }
        
        # Relationship statistics
        rel_types = {}
        entity_connections = {}
        
        for rel in relations:
            rel_type = rel.relation_type
            if rel_type not in rel_types:
                rel_types[rel_type] = 0
            rel_types[rel_type] += 1
            
            # Count connections per entity
            for entity_name in [rel.from_entity_name, rel.to_entity_name]:
                if entity_name not in entity_connections:
                    entity_connections[entity_name] = 0
                entity_connections[entity_name] += 1
        
        insights["relationship_statistics"] = {
            "total_relationships": len(relations),
            "by_type": rel_types
        }
        
        # Skill distribution
        insights["skill_distribution"] = {
            skill: {
                "count": len(people),
                "people": people
            }
            for skill, people in skill_observations.items()
        }
        
        # Identify knowledge gaps (skills with only 1 person)
        for skill, data in insights["skill_distribution"].items():
            if data["count"] == 1:
                insights["knowledge_gaps"].append({
                    "skill": skill,
                    "current_expert": data["people"][0]["person"],
                    "risk": "Single point of knowledge"
                })
        
        # Identify underutilized expertise (people with skills but few project connections)
        for person in people_entities:
            person_skills = []
            for obs in person.observations:
                if obs.get("type") == "skill":
                    person_skills.append(obs.get("value"))
            
            connections = entity_connections.get(person.entity_name, 0)
            if person_skills and connections < 2:
                insights["underutilized_expertise"].append({
                    "person": person.entity_name,
                    "skills": person_skills,
                    "current_connections": connections,
                    "recommendation": "Consider involving in more projects"
                })
        
        # Suggest collaboration opportunities
        # Find people with complementary skills who aren't connected
        if len(people_entities) > 1:
            for i, person1 in enumerate(people_entities):
                for person2 in people_entities[i+1:]:
                    # Check if they're connected
                    connected = any(
                        (rel.from_entity_name == person1.entity_name and rel.to_entity_name == person2.entity_name) or
                        (rel.from_entity_name == person2.entity_name and rel.to_entity_name == person1.entity_name)
                        for rel in relations
                    )
                    
                    if not connected:
                        # Check for complementary skills
                        person1_skills = set(
                            obs.get("value") for obs in person1.observations
                            if obs.get("type") == "skill"
                        )
                        person2_skills = set(
                            obs.get("value") for obs in person2.observations
                            if obs.get("type") == "skill"
                        )
                        
                        if person1_skills and person2_skills and not person1_skills.intersection(person2_skills):
                            insights["collaboration_opportunities"].append({
                                "person1": person1.entity_name,
                                "person1_skills": list(person1_skills)[:3],
                                "person2": person2.entity_name,
                                "person2_skills": list(person2_skills)[:3],
                                "reason": "Complementary skills, not currently connected"
                            })
        
        # Summary
        insights["summary"] = {
            "total_people": len(people_entities),
            "total_projects": len(project_entities),
            "unique_skills": len(skill_observations),
            "average_connections_per_entity": sum(entity_connections.values()) / len(entity_connections) if entity_connections else 0,
            "most_connected_entities": sorted(
                entity_connections.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
        
        return insights
    
    async def process_text_chunk(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        text: str,
        source: str = "text_chunk",
        extract_context: bool = True,
        context_preview_length: int = 500
    ) -> Dict[str, Any]:
        """
        Process a chunk of text into entities, observations, and relationships.
        Uses GPT-4.1-nano for extraction, then stores using existing methods.
        
        Args:
            client_id: Client UUID
            actor_type: Type of actor creating these memories
            actor_id: ID of the actor
            text: The text chunk to process
            source: Source identifier for tracking
            extract_context: Whether to search for context from existing memories
            context_preview_length: Length of text preview for context search
            
        Returns:
            Dict with created entities, observations, relationships
        """
        from openai import AsyncOpenAI
        import os
        import json
        from datetime import datetime
        
        start_time = datetime.utcnow()
        
        # Constants
        EXTRACTION_MODEL = os.getenv("GPT_MODEL", "gpt-4.1-nano")
        EXTRACTION_TEMPERATURE = 0.1
        EXTRACTION_MAX_TOKENS = 4000
        
        try:
            # Initialize OpenAI client
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            context_memories = []
            if extract_context:
                # Search for context from existing memories
                context_memories = await self._search_context_memories(
                    client_id, actor_type, actor_id,
                    text[:context_preview_length]
                )
            
            # Extract everything using GPT-4.1-nano WITH CONTEXT
            extraction = await self._extract_with_gpt(
                openai_client,
                text,
                context_memories,
                EXTRACTION_MODEL,
                EXTRACTION_TEMPERATURE,
                EXTRACTION_MAX_TOKENS
            )
            
            # Process extracted data
            result = await self._process_extraction(
                client_id, actor_type, actor_id,
                extraction, source
            )
            
            result["processing_time_ms"] = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            return result
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "processing_time_ms": int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )
            }
    
    async def _search_context_memories(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        text_preview: str
    ) -> List[Dict]:
        """
        Search existing memories for context based on a text preview.
        This gives each chunk awareness of all previous memories!
        """
        from openai import AsyncOpenAI
        import os
        import re
        
        try:
            # Initialize OpenAI client
            openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Extract key terms from the preview
            key_terms = await self._extract_key_terms(openai_client, text_preview)
            
            # Search for each key term
            all_results = []
            seen_ids = set()  # Avoid duplicates
            
            for term in key_terms:
                # Use existing search_nodes method
                search_results = await self.search_nodes(
                    client_id=client_id,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    query=term,
                    entity_type=None,
                    limit=10,
                    threshold=0.5
                )
                
                for result in search_results:
                    entity_id = result.get("id")
                    if entity_id and entity_id not in seen_ids:
                        seen_ids.add(entity_id)
                        all_results.append(result)
            
            # Sort by relevance and return top 20
            return all_results[:20]
            
        except Exception as e:
            # Fallback: extract capitalized words
            words = re.findall(r'\b[A-Z][a-z]+\b', text_preview)
            return []
    
    async def _extract_key_terms(self, openai_client, text_preview: str) -> List[str]:
        """
        Quickly extract key terms from text for context search.
        Using GPT-4.1-nano for speed.
        """
        try:
            response = await openai_client.chat.completions.create(
                model=os.getenv("GPT_MODEL", "gpt-4.1-nano"),
                messages=[
                    {
                        "role": "system", 
                        "content": "Extract 5-10 key names, places, or important terms from this text. Return only the terms, one per line."
                    },
                    {"role": "user", "content": text_preview}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            # Parse the response
            terms_text = response.choices[0].message.content
            terms = [term.strip() for term in terms_text.split("\n") if term.strip()]
            
            return terms[:10]  # Max 10 terms
            
        except Exception as e:
            # Fallback: extract capitalized words
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b', text_preview)
            return list(set(words))[:10]
    
    async def _extract_with_gpt(
        self,
        openai_client,
        text: str,
        context_memories: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Use GPT-4.1-nano to extract entities, events, relationships, and observations.
        WITH CONTEXT from previous memories!
        """
        
        # Build context section from existing memories
        context_section = ""
        if context_memories:
            context_section = "\n\nCONTEXT FROM EXISTING MEMORIES:\n"
            seen_entities = set()
            for mem in context_memories[:20]:  # Top 20 relevant memories
                entity_name = mem.get('entity_name', '')
                if entity_name and entity_name not in seen_entities:
                    seen_entities.add(entity_name)
                    entity_type = mem.get('entity_type', 'unknown')
                    metadata = mem.get('metadata', {})
                    
                    # Add entity info
                    context_section += f"- {entity_name} ({entity_type})"
                    
                    # Add key identifiers if present
                    if metadata.get('identifiers'):
                        ids = metadata['identifiers']
                        if ids.get('email'):
                            context_section += f" - email: {ids['email']}"
                        if ids.get('phone'):
                            context_section += f" - phone: {ids['phone']}"
                    
                    # Add description or other context
                    if metadata.get('description'):
                        context_section += f" - {metadata['description']}"
                    elif metadata.get('notes'):
                        context_section += f" - {metadata['notes']}"
                    
                    context_section += "\n"
            
            if seen_entities:
                context_section += "\nIMPORTANT: When you encounter similar names or references, check if they match any of the above known entities. For example, 'Carlos' might be the same person as 'El Jefe' if the context suggests they're the same person.\n"
        
        system_prompt = context_section + """Extract entities, events, relationships, and observations from the text.

ENTITIES:
- Extract people, places, organizations, and other notable entities
- For each entity, determine its grade:
  - absolute: has legal ID (SSN, EIN, passport, full address with postal code)
  - high: multiple strong identifiers (email + phone, or name + specific workplace)
  - medium: name with contextual information
  - low: name only
  - generic: non-specific references like "a person", "someone", "the company"
- Include any identifiers found (email, phone, address, etc.)

EVENTS:
- Extract meetings, calls, deadlines, milestones, or other time-based occurrences
- Include timestamp if mentioned (parse to ISO format)
- List participants and location

RELATIONSHIPS:
- Extract how entities relate to each other
- Include relationship type and confidence (0-1)

OBSERVATIONS:
- Extract important facts that don't fit the above categories
- Keep them factual and concise"""

        function_schema = {
            "name": "extract_memory_components",
            "parameters": {
                "type": "object",
                "required": ["entities", "events", "relationships", "observations"],
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "entity_type", "grade", "confidence"],
                            "properties": {
                                "name": {"type": "string"},
                                "entity_type": {"enum": ["person", "place", "organization", "thing", "concept"]},
                                "identifiers": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string"},
                                        "phone": {"type": "string"},
                                        "ssn": {"type": "string"},
                                        "ein": {"type": "string"},
                                        "address": {"type": "string"},
                                        "website": {"type": "string"},
                                        "employee_id": {"type": "string"}
                                    }
                                },
                                "attributes": {"type": "object"},
                                "grade": {"enum": ["absolute", "high", "medium", "low", "generic"]},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    },
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "event_type"],
                            "properties": {
                                "name": {"type": "string"},
                                "event_type": {"enum": ["meeting", "call", "deadline", "milestone", "decision", "incident", "other"]},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "duration_minutes": {"type": "integer"},
                                "participants": {"type": "array", "items": {"type": "string"}},
                                "location": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["source", "target", "relationship_type", "confidence"],
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "relationship_type": {"type": "string"},
                                "temporal_marker": {"enum": ["current", "former", "future", null]},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    },
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["content", "importance"],
                            "properties": {
                                "content": {"type": "string"},
                                "importance": {"enum": ["high", "medium", "low"]},
                                "tags": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                }
            }
        }

        # Make the GPT call
        response = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            functions=[function_schema],
            function_call={"name": "extract_memory_components"},
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Parse the structured response
        import json
        return json.loads(response.choices[0].message.function_call.arguments)
    
    async def _process_extraction(
        self,
        # client_id removed - use actor_id when actor_type="client"
        actor_type: str,
        actor_id: UUID,
        extraction: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        Process the extracted data using existing memory manager methods.
        """
        from datetime import datetime
        
        result = {
            "success": True,
            "entities_created": [],
            "events_created": [],
            "observations_created": [],
            "relationships_created": [],
            "errors": []
        }
        
        # Map to track entity names to IDs
        entity_map = {}
        
        # Step 1: Process entities (skip generics)
        for entity_data in extraction.get("entities", []):
            if entity_data["grade"] == "generic":
                # Store generic mentions as observations without entity
                continue
            
            try:
                # Check if entity exists using search
                search_results = await self.search_nodes(
                    client_id=client_id,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    query=entity_data["name"],
                    entity_type=entity_data["entity_type"],
                    limit=5
                )
                
                existing = None
                for res in search_results:
                    if res.get("entity_name", "").lower() == entity_data["name"].lower():
                        existing = res
                        break
                
                if existing:
                    entity_id = existing["id"]
                    entity_map[entity_data["name"]] = entity_id
                    result["entities_created"].append({
                        "entity_id": entity_id,
                        "action": "matched_existing",
                        "name": entity_data["name"]
                    })
                else:
                    # Create new entity with grade in metadata
                    metadata = entity_data.get("attributes", {})
                    metadata["grade"] = entity_data["grade"]
                    metadata["confidence"] = entity_data["confidence"]
                    metadata["identifiers"] = entity_data.get("identifiers", {})
                    metadata["created_from"] = source
                    metadata["last_reinforced"] = datetime.utcnow().isoformat()
                    
                    # Create entity
                    entities_result = await self.create_entities(
                        client_id, actor_type, actor_id,
                        [EntityCreate(
                            name=entity_data["name"],
                            entityType=entity_data["entity_type"],
                            observations=[Observation(
                                type="initial_extraction",
                                value=f"Extracted from {source}",
                                source=source,
                                context={"grade": entity_data["grade"]}
                            )],
                            metadata=metadata,
                            identityConfidence=entity_data["confidence"]
                        )]
                    )
                    
                    if entities_result and len(entities_result) > 0:
                        entity_id = entities_result[0]["id"]
                        entity_map[entity_data["name"]] = entity_id
                        result["entities_created"].append(entities_result[0])
                    
            except Exception as e:
                result["errors"].append({
                    "type": "entity_creation",
                    "entity": entity_data["name"],
                    "error": str(e)
                })
        
        # Step 2: Process events as entities
        for event_data in extraction.get("events", []):
            try:
                # Events are entities with type="event"
                metadata = {
                    "event_type": event_data["event_type"],
                    "timestamp": event_data.get("timestamp"),
                    "duration_minutes": event_data.get("duration_minutes"),
                    "participants": event_data.get("participants", []),
                    "location": event_data.get("location"),
                    "description": event_data.get("description"),
                    "created_from": source,
                    "grade": "high",  # Events typically have good identifiers
                    "last_reinforced": datetime.utcnow().isoformat()
                }
                
                events_result = await self.create_entities(
                    client_id, actor_type, actor_id,
                    [EntityCreate(
                        name=event_data["name"],
                        entityType="event",
                        observations=[Observation(
                            type="event_details",
                            value=event_data.get("description", f"Event: {event_data['name']}"),
                            source=source
                        )],
                        metadata=metadata
                    )]
                )
                
                if events_result and len(events_result) > 0:
                    event_id = events_result[0]["id"]
                    result["events_created"].append(events_result[0])
                    
                    # Create relationships to participants
                    for participant in event_data.get("participants", []):
                        if participant in entity_map:
                            try:
                                rel_result = await self.create_relations(
                                    client_id, actor_type, actor_id,
                                    [RelationCreate(
                                        from_entity_name=participant,
                                        to_entity_name=event_data["name"],
                                        relationType="participated_in",
                                        metadata={"role": "participant"}
                                    )]
                                )
                                if rel_result:
                                    result["relationships_created"].extend(rel_result)
                            except Exception as e:
                                pass  # Ignore relationship errors
                                
            except Exception as e:
                result["errors"].append({
                    "type": "event_creation",
                    "event": event_data["name"],
                    "error": str(e)
                })
        
        # Step 3: Process observations
        for obs_data in extraction.get("observations", []):
            try:
                # Try to associate with the most recently created entity
                entity_name = None
                if entity_map:
                    # Use the last created entity as context
                    entity_name = list(entity_map.keys())[-1]
                
                if entity_name:
                    obs_result = await self.add_observations(
                        client_id, actor_type, actor_id,
                        [ObservationAdd(
                            entityName=entity_name,
                            contents=[ObservationContent(
                                type="extracted_fact",
                                value=obs_data["content"],
                                source=source,
                                context={
                                    "importance": obs_data["importance"],
                                    "tags": obs_data.get("tags", [])
                                }
                            )]
                        )]
                    )
                    
                    if obs_result:
                        result["observations_created"].extend(obs_result)
                        
            except Exception as e:
                result["errors"].append({
                    "type": "observation_creation",
                    "content": obs_data["content"],
                    "error": str(e)
                })
        
        # Step 4: Process relationships
        for rel_data in extraction.get("relationships", []):
            try:
                if rel_data["source"] in entity_map or rel_data["target"] in entity_map:
                    metadata = {
                        "confidence": rel_data["confidence"],
                        "temporal_marker": rel_data.get("temporal_marker"),
                        "created_from": source
                    }
                    
                    rel_result = await self.create_relations(
                        client_id, actor_type, actor_id,
                        [RelationCreate(
                            from_entity_name=rel_data["source"],
                            to_entity_name=rel_data["target"],
                            relationType=rel_data["relationship_type"],
                            metadata=metadata
                        )]
                    )
                    
                    if rel_result:
                        result["relationships_created"].extend(rel_result)
                        
            except Exception as e:
                result["errors"].append({
                    "type": "relationship_creation",
                    "source": rel_data["source"],
                    "target": rel_data["target"],
                    "error": str(e)
                })
        
        return result
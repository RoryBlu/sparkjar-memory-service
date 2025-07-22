# services/memory_manager_hierarchical.py
"""
Enhanced MemoryManager with hierarchical memory access support.

This implementation enables synths to access their synth_class memories,
and optionally client-level memories, addressing the critical limitation
identified in the memory system audit.
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func
from datetime import datetime
import logging

from services.memory_manager import MemoryManager
from sparkjar_crew.shared.database.models import MemoryEntities, MemoryRelations, MemoryObservations
# Import crew models - adjust path as needed
import sys
from pathlib import Path
from services.crew_api.src.database.models import Synths, SynthClasses, Clients

logger = logging.getLogger(__name__)

class HierarchicalMemoryManager(MemoryManager):
    """
    Extended MemoryManager that supports hierarchical memory access.
    
    Enables the following hierarchy:
    - synth → skill_module → synth_class → client
    
    This allows synths to:
    - Access memories from skill modules they're subscribed to
    - Inherit procedural knowledge from their class templates
    - Access shared organizational knowledge
    """
    
    def __init__(self, db_session: Session, embedding_service: Any):
        super().__init__(db_session, embedding_service)
        self._synth_class_cache = {}  # Cache synth -> synth_class mappings
        self._cache_ttl = 300  # 5 minutes TTL
        self._cache_timestamps = {}
    
    def _get_synth_class_id(self, actor_type: str, actor_id: UUID) -> Optional[int]:
        """
        Get the synth_class_id for a synth actor.
        Uses caching to meet <50ms performance requirement.
        """
        if actor_type != 'synth':
            return None
        
        # Check cache first
        cache_key = f"synth_class:{actor_id}"
        if cache_key in self._synth_class_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if (datetime.utcnow().timestamp() - timestamp) < self._cache_ttl:
                return self._synth_class_cache[cache_key]
        
        # Query database
        try:
            synth = self.db.query(Synths).filter(
                Synths.id == actor_id
            ).first()
            
            if synth and synth.synth_classes_id:
                # Update cache
                self._synth_class_cache[cache_key] = synth.synth_classes_id
                self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
                return synth.synth_classes_id
        except Exception as e:
            logger.error(f"Error fetching synth_class_id for synth {actor_id}: {e}")
        
        return None
    
    def _get_synth_skill_modules(self, actor_type: str, actor_id: UUID) -> List[UUID]:
        """
        Get the skill module IDs that a synth is subscribed to.
        Uses caching to meet performance requirements.
        """
        if actor_type != 'synth':
            return []
        
        # Check cache first
        cache_key = f"skill_modules:{actor_id}"
        if cache_key in self._synth_class_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if (datetime.utcnow().timestamp() - timestamp) < self._cache_ttl:
                return self._synth_class_cache[cache_key]
        
        # Query database for skill module subscriptions
        try:
            # Import the model we need
            from sparkjar_crew.shared.database.models import SynthSkillSubscriptions
            
            subscriptions = self.db.query(SynthSkillSubscriptions).filter(
                SynthSkillSubscriptions.synth_id == actor_id,
                SynthSkillSubscriptions.active == True
            ).all()
            
            skill_module_ids = [sub.skill_module_id for sub in subscriptions]
            
            # Update cache
            self._synth_class_cache[cache_key] = skill_module_ids
            self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
            
            return skill_module_ids
        except Exception as e:
            logger.error(f"Error fetching skill modules for synth {actor_id}: {e}")
            return []
    
    def _build_hierarchical_filter(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        include_synth_class: bool = True,
        include_client: bool = False,
        include_skill_module: bool = True
    ):
        """
        Build a filter that includes hierarchical memory access.
        
        Args:
            client_id: The client ID for multi-tenancy
            actor_type: The type of actor (human, synth, synth_class, client, skill_module)
            actor_id: The actor's ID
            include_synth_class: Whether to include synth_class memories for synths
            include_client: Whether to include client-level memories
            include_skill_module: Whether to include skill_module memories for synths
        
        Returns:
            SQLAlchemy filter expression supporting hierarchical access
        """
        filters = []
        
        # Always include the actor's own memories
        filters.append(
            and_(
                MemoryEntities.client_id == client_id,
                MemoryEntities.actor_type == actor_type,
                MemoryEntities.actor_id == actor_id,
                MemoryEntities.deleted_at.is_(None)
            )
        )
        
        # Add synth_class memories for synths
        if actor_type == 'synth' and include_synth_class:
            synth_class_id = self._get_synth_class_id(actor_type, actor_id)
            if synth_class_id:
                filters.append(
                    and_(
                        MemoryEntities.actor_type == 'synth_class',
                        MemoryEntities.actor_id == str(synth_class_id),
                        MemoryEntities.deleted_at.is_(None)
                    )
                )
                logger.debug(f"Added synth_class filter for class ID: {synth_class_id}")
        
        # Add skill_module memories for synths
        if actor_type == 'synth' and include_skill_module:
            skill_module_ids = self._get_synth_skill_modules(actor_type, actor_id)
            for skill_module_id in skill_module_ids:
                filters.append(
                    and_(
                        MemoryEntities.client_id == client_id,
                        MemoryEntities.actor_type == 'skill_module',
                        MemoryEntities.actor_id == str(skill_module_id),
                        MemoryEntities.deleted_at.is_(None)
                    )
                )
            if skill_module_ids:
                logger.debug(f"Added skill_module filters for {len(skill_module_ids)} modules")
        
        # Add client-level memories if requested
        if include_client and client_id:
            filters.append(
                and_(
                    MemoryEntities.client_id == client_id,
                    MemoryEntities.actor_type == 'client',
                    MemoryEntities.actor_id == str(client_id),
                    MemoryEntities.deleted_at.is_(None)
                )
            )
            logger.debug(f"Added client-level filter for client ID: {client_id}")
        
        # Combine all filters with OR
        if len(filters) == 1:
            return filters[0]
        else:
            return or_(*filters)
    
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
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories with hierarchical access pattern.
        
        This method enables synths to search across their own memories,
        their synth_class templates, skill modules, and optionally client-level knowledge.
        
        Args:
            client_id: Client ID for multi-tenancy
            actor_type: Type of actor performing the search
            actor_id: ID of the actor
            query: Search query text
            entity_types: Optional list of entity types to filter
            include_synth_class: Include synth_class memories for synths
            include_client: Include client-level memories
            include_skill_module: Include skill_module memories for synths
            limit: Maximum number of results
        
        Returns:
            List of memory entities with similarity scores and access context
        """
        logger.info(f"Hierarchical search by {actor_type} {actor_id}: '{query}'")
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Convert to SQL array format for pgvector
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Build hierarchical query
        hierarchical_filter = self._build_hierarchical_filter(
            client_id, actor_type, actor_id,
            include_synth_class=include_synth_class,
            include_client=include_client,
            include_skill_module=include_skill_module
        )
        
        # Build query with vector similarity
        base_query = self.db.query(
            MemoryEntities,
            (1 - func.cosine_distance(MemoryEntities.embedding, embedding_str)).label('similarity'),
            MemoryEntities.actor_type.label('access_context')
        ).filter(hierarchical_filter)
        
        # Add entity type filter if specified
        if entity_types:
            base_query = base_query.filter(MemoryEntities.entity_type.in_(entity_types))
        
        # Order by similarity and limit
        results = base_query.order_by(
            func.cosine_distance(MemoryEntities.embedding, embedding_str)
        ).limit(limit).all()
        
        # Format results with access context
        formatted_results = []
        for entity, similarity, access_context in results:
            entity_dict = self._entity_to_dict(entity)
            entity_dict['similarity'] = float(similarity)
            entity_dict['access_context'] = access_context
            
            # Add access source information
            if access_context == actor_type:
                entity_dict['access_source'] = 'own'
            elif access_context == 'synth_class':
                entity_dict['access_source'] = 'inherited_template'
            elif access_context == 'skill_module':
                entity_dict['access_source'] = 'skill_module'
            elif access_context == 'client':
                entity_dict['access_source'] = 'organizational'
            else:
                entity_dict['access_source'] = 'unknown'
            
            formatted_results.append(entity_dict)
        
        logger.info(f"Found {len(formatted_results)} results across contexts")
        return formatted_results
    
    async def search_nodes(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
        include_hierarchy: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search_nodes with optional hierarchy support.
        
        Maintains backwards compatibility while adding hierarchy option.
        """
        if include_hierarchy:
            return await self.search_hierarchical_memories(
                client_id, actor_type, actor_id, query,
                entity_types=entity_types,
                include_synth_class=True,
                include_client=False,
                include_skill_module=True,
                limit=limit
            )
        else:
            # Use original strict search
            return await super().search_nodes(
                client_id, actor_type, actor_id, query,
                entity_types=entity_types,
                limit=limit
            )
    
    async def get_entities(
        self,
        client_id: UUID,
        actor_type: str,
        actor_id: UUID,
        entity_names: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        include_hierarchy: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get entities with optional hierarchical access.
        """
        if include_hierarchy:
            hierarchical_filter = self._build_hierarchical_filter(
                client_id, actor_type, actor_id,
                include_synth_class=True,
                include_client=False,
                include_skill_module=True
            )
        else:
            hierarchical_filter = self._get_base_filter(client_id, actor_type, actor_id)
        
        query = self.db.query(MemoryEntities).filter(hierarchical_filter)
        
        if entity_names:
            query = query.filter(MemoryEntities.entity_name.in_(entity_names))
        
        if entity_types:
            query = query.filter(MemoryEntities.entity_type.in_(entity_types))
        
        entities = query.all()
        return [self._entity_to_dict(entity) for entity in entities]
    
    async def access_context_memories(
        self,
        client_id: UUID,
        requesting_actor_type: str,
        requesting_actor_id: UUID,
        target_actor_type: str,
        target_actor_id: UUID,
        query: Optional[str] = None,
        permission_check: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Explicitly access memories from a different actor context.
        
        This method enables controlled cross-context access with audit logging.
        
        Args:
            client_id: Client ID for multi-tenancy
            requesting_actor_type: Type of actor making the request
            requesting_actor_id: ID of the requesting actor
            target_actor_type: Type of actor whose memories to access
            target_actor_id: ID of the target actor
            query: Optional search query
            permission_check: Whether to enforce permission checks
        
        Returns:
            List of memory entities from the target context
        """
        # Log cross-context access attempt
        logger.info(
            f"Cross-context access: {requesting_actor_type}:{requesting_actor_id} "
            f"requesting {target_actor_type}:{target_actor_id}"
        )
        
        # Permission check (simplified for now)
        if permission_check:
            if not self._check_cross_context_permission(
                requesting_actor_type, requesting_actor_id,
                target_actor_type, target_actor_id
            ):
                logger.warning(f"Permission denied for cross-context access")
                return []
        
        # Build filter for target context
        target_filter = and_(
            MemoryEntities.client_id == client_id,
            MemoryEntities.actor_type == target_actor_type,
            MemoryEntities.actor_id == target_actor_id,
            MemoryEntities.deleted_at.is_(None)
        )
        
        if query:
            # Perform semantic search in target context
            query_embedding = await self.embedding_service.generate_embedding(query)
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            results = self.db.query(
                MemoryEntities,
                (1 - func.cosine_distance(MemoryEntities.embedding, embedding_str)).label('similarity')
            ).filter(target_filter).order_by(
                func.cosine_distance(MemoryEntities.embedding, embedding_str)
            ).limit(10).all()
            
            formatted_results = []
            for entity, similarity in results:
                entity_dict = self._entity_to_dict(entity)
                entity_dict['similarity'] = float(similarity)
                entity_dict['cross_context_access'] = True
                formatted_results.append(entity_dict)
            
            return formatted_results
        else:
            # Get all entities from target context
            entities = self.db.query(MemoryEntities).filter(target_filter).all()
            return [
                {**self._entity_to_dict(entity), 'cross_context_access': True}
                for entity in entities
            ]
    
    def _check_cross_context_permission(
        self,
        requesting_actor_type: str,
        requesting_actor_id: UUID,
        target_actor_type: str,
        target_actor_id: UUID
    ) -> bool:
        """
        Check if cross-context access is permitted.
        
        Current rules:
        - Synths can access their subscribed skill_module memories
        - Synths can access their synth_class memories
        - Synths can access client memories
        - Humans can access all memories within their client
        """
        # Synths accessing their subscribed skill modules
        if requesting_actor_type == 'synth' and target_actor_type == 'skill_module':
            skill_module_ids = self._get_synth_skill_modules(requesting_actor_type, requesting_actor_id)
            return target_actor_id in skill_module_ids
        
        # Synths accessing their class templates
        if requesting_actor_type == 'synth' and target_actor_type == 'synth_class':
            synth_class_id = self._get_synth_class_id(requesting_actor_type, requesting_actor_id)
            return str(synth_class_id) == str(target_actor_id)
        
        # Synths accessing client memories
        if requesting_actor_type == 'synth' and target_actor_type == 'client':
            return True  # Could add more granular checks here
        
        # Humans have broader access
        if requesting_actor_type == 'human':
            return True
        
        return False
    
    def invalidate_cache(self, actor_id: Optional[UUID] = None):
        """Invalidate the synth_class and skill_module cache."""
        if actor_id:
            # Remove synth_class cache
            cache_key = f"synth_class:{actor_id}"
            self._synth_class_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            
            # Remove skill_modules cache
            cache_key = f"skill_modules:{actor_id}"
            self._synth_class_cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
        else:
            self._synth_class_cache.clear()
            self._cache_timestamps.clear()
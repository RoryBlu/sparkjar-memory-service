# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# services/memory_manager_hierarchical_fixed.py
"""
Enhanced MemoryManager with hierarchical memory access support.
Fixed to handle text actor_id fields (can store UUID or bigint as string).

This implementation enables synths to access their synth_class memories,
and optionally client-level memories, addressing the critical limitation
identified in the memory system audit.
"""
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, func
from datetime import datetime
import logging

from services.memory_manager import MemoryManager
from sparkjar_crew.shared.database.models import MemoryEntities, MemoryRelations, MemoryObservations

logger = logging.getLogger(__name__)

class HierarchicalMemoryManager(MemoryManager):
    """
    Extended MemoryManager that supports hierarchical memory access.
    
    Enables the following hierarchy:
    - synth → synth_class → client
    
    This allows synths to inherit procedural knowledge from their class templates
    and access shared organizational knowledge.
    """
    
    def __init__(self, db_session: Session, embedding_service: Any):
        super().__init__(db_session, embedding_service)
        self._synth_class_cache = {}  # Cache synth -> synth_class mappings
        self._cache_ttl = 300  # 5 minutes TTL
        self._cache_timestamps = {}
    
    def _convert_actor_id_to_string(self, actor_id: Union[UUID, str, int]) -> str:
        """
        Convert actor_id to string format for database storage.
        Handles UUID, string, or integer inputs.
        """
        if isinstance(actor_id, UUID):
            return str(actor_id)
        elif isinstance(actor_id, int):
            return str(actor_id)
        else:
            return str(actor_id)
    
    def _get_synth_class_id(self, actor_type: str, actor_id: Union[UUID, str]) -> Optional[str]:
        """
        Get the synth_class_id for a synth actor.
        Uses caching to meet <50ms performance requirement.
        Returns the class ID as a string.
        """
        if actor_type != 'synth':
            return None
        
        actor_id_str = self._convert_actor_id_to_string(actor_id)
        
        # Check cache first
        cache_key = f"synth_class:{actor_id_str}"
        if cache_key in self._synth_class_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if (datetime.utcnow().timestamp() - timestamp) < self._cache_ttl:
                return str(self._synth_class_cache[cache_key])
        
        # Query database using dynamic SQL to handle different database configurations
        try:
            result = self.db.execute(text("""
                SELECT synth_classes_id 
                FROM synths 
                WHERE id::text = :synth_id
                LIMIT 1
            """), {"synth_id": actor_id_str})
            
            row = result.fetchone()
            if row and row[0]:
                class_id = row[0]
                # Update cache
                self._synth_class_cache[cache_key] = class_id
                self._cache_timestamps[cache_key] = datetime.utcnow().timestamp()
                return str(class_id)
        except Exception as e:
            logger.error(f"Error fetching synth_class_id for synth {actor_id_str}: {e}")
        
        return None
    
    def _build_hierarchical_filter(
        self,
        client_id: Union[UUID, str],
        actor_type: str,
        actor_id: Union[UUID, str],
        include_synth_class: bool = True,
        include_client: bool = False
    ):
        """
        Build a filter that includes hierarchical memory access.
        
        Args:
            client_id: The client ID for multi-tenancy
            actor_type: The type of actor (human, synth, synth_class, client)
            actor_id: The actor's ID (can be UUID or string)
            include_synth_class: Whether to include synth_class memories for synths
            include_client: Whether to include client-level memories
        
        Returns:
            SQLAlchemy filter expression supporting hierarchical access
        """
        filters = []
        
        # Convert IDs to strings
        actor_id_str = self._convert_actor_id_to_string(actor_id)
        client_id_str = self._convert_actor_id_to_string(client_id)
        
        # Always include the actor's own memories
        filters.append(
            and_(
                MemoryEntities.actor_type == actor_type,
                MemoryEntities.actor_id == actor_id_str,
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
                        MemoryEntities.actor_id == synth_class_id,
                        MemoryEntities.deleted_at.is_(None)
                    )
                )
                logger.debug(f"Added synth_class filter for class ID: {synth_class_id}")
        
        # Add client-level memories if requested
        if include_client and client_id:
            filters.append(
                and_(
                    MemoryEntities.actor_type == 'client',
                    MemoryEntities.actor_id == client_id_str,
                    MemoryEntities.deleted_at.is_(None)
                )
            )
            logger.debug(f"Added client-level filter for client ID: {client_id_str}")
        
        # Combine all filters with OR
        if len(filters) == 1:
            return filters[0]
        else:
            return or_(*filters)
    
    async def search_hierarchical_memories(
        self,
        client_id: Union[UUID, str],
        actor_type: str,
        actor_id: Union[UUID, str],
        query: str,
        entity_types: Optional[List[str]] = None,
        include_synth_class: bool = True,
        include_client: bool = False,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories with hierarchical access pattern.
        
        This method enables synths to search across their own memories,
        their synth_class templates, and optionally client-level knowledge.
        
        Args:
            client_id: Client ID for multi-tenancy
            actor_type: Type of actor performing the search
            actor_id: ID of the actor (can be UUID or string)
            query: Search query text
            entity_types: Optional list of entity types to filter
            include_synth_class: Include synth_class memories for synths
            include_client: Include client-level memories
            limit: Maximum number of results
        
        Returns:
            List of memory entities with similarity scores and access context
        """
        actor_id_str = self._convert_actor_id_to_string(actor_id)
        logger.info(f"Hierarchical search by {actor_type} {actor_id_str}: '{query}'")
        
        # For now, use simple text search since embeddings were removed
        # This can be enhanced with vector search when embeddings are re-added
        
        # Build hierarchical filter
        hierarchical_filter = self._build_hierarchical_filter(
            client_id, actor_type, actor_id,
            include_synth_class=include_synth_class,
            include_client=include_client
        )
        
        # Build query with text search
        results = self.db.query(
            MemoryEntities,
            MemoryObservations
        ).join(
            MemoryObservations, 
            MemoryObservations.entity_id == MemoryEntities.id
        ).filter(
            hierarchical_filter,
            or_(
                MemoryEntities.entity_name.ilike(f'%{query}%'),
                MemoryObservations.observation_value.astext.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        # Format results
        formatted_results = []
        for entity, observation in results:
            formatted_results.append({
                'id': str(entity.id),
                'entity_name': entity.entity_name,
                'entity_type': entity.entity_type,
                'actor_type': entity.actor_type,
                'actor_id': entity.actor_id,
                'observation_type': observation.observation_type,
                'observation_value': observation.observation_value,
                '_score': 1.0,  # Placeholder score
                'access_context': entity.actor_type  # Shows where the memory came from
            })
        
        return formatted_results
    
    def create_memory_with_hierarchy(
        self,
        client_id: Union[UUID, str],
        actor_type: str,
        actor_id: Union[UUID, str],
        entity_name: str,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntities:
        """
        Create a memory entity with proper actor_id handling.
        """
        actor_id_str = self._convert_actor_id_to_string(actor_id)
        
        entity = MemoryEntities(
            actor_type=actor_type,
            actor_id=actor_id_str,
            entity_name=entity_name,
            entity_type=entity_type,
            metadata=metadata or {}
        )
        
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        
        return entity

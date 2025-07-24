"""
Actor validation service for memory system.

This module provides validation to ensure actor_id references exist in the 
appropriate tables based on actor_type, maintaining referential integrity.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
import logging
from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class CacheInterface(ABC):
    """Abstract interface for actor validation caching."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[bool]:
        """Get validation result from cache."""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: bool, ttl: int = 3600) -> None:
        """Store validation result in cache with TTL."""
        pass
        
    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern (for invalidation)."""
        pass

class InMemoryCache(CacheInterface):
    """Thread-safe in-memory cache implementation."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[bool, float]] = {}
        self._default_ttl = 3600  # 1 hour
        
    async def get(self, key: str) -> Optional[bool]:
        """Get validation result from cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                # Expired, remove it
                del self._cache[key]
        return None
        
    async def set(self, key: str, value: bool, ttl: int = 3600) -> None:
        """Store validation result in cache with TTL."""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
        
    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        # Simple pattern matching for actor_type:* patterns
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            # Exact match
            if pattern in self._cache:
                del self._cache[pattern]
                
    async def cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [k for k, (_, expiry) in self._cache.items() if expiry < current_time]
        for key in expired_keys:
            del self._cache[key]

class InvalidActorError(Exception):
    """Raised when an actor_id is invalid for the given actor_type."""
    
    def __init__(self, actor_type: str, actor_id: UUID, message: str):
        self.actor_type = actor_type
        self.actor_id = actor_id
        super().__init__(message)

class ActorValidator:
    """Validates actor_id references against appropriate tables based on actor_type."""
    
    # Mapping of actor_type to database table
    ACTOR_TYPE_MAPPING = {
        'human': 'client_users',
        'synth': 'synths',
        'synth_class': 'synth_classes',
        'client': 'clients',
        'skill_module': 'skill_modules'
    }
    
    def __init__(self, db_session: AsyncSession, cache: Optional[CacheInterface] = None):
        """
        Initialize the ActorValidator.
        
        Args:
            db_session: AsyncSession for database queries
            cache: Optional cache implementation (defaults to InMemoryCache)
        """
        self.db_session = db_session
        self.cache = cache or InMemoryCache()
        self._metrics_enabled = True
        
    def _get_cache_key(self, actor_type: str, actor_id: UUID) -> str:
        """Generate cache key for actor validation."""
        return f"{actor_type}:{actor_id}"
        
    async def _record_metric(
        self, 
        actor_type: str, 
        actor_id: UUID,
        validation_result: bool,
        validation_time_ms: float,
        cache_hit: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Record validation metric to database."""
        if not self._metrics_enabled:
            return
            
        try:
            await self.db_session.execute(
                text("""
                    INSERT INTO actor_validation_metrics 
                    (actor_type, actor_id, validation_result, validation_time_ms, cache_hit, error_message)
                    VALUES (:actor_type, :actor_id, :validation_result, :validation_time_ms, :cache_hit, :error_message)
                """),
                {
                    "actor_type": actor_type,
                    "actor_id": actor_id,
                    "validation_result": validation_result,
                    "validation_time_ms": validation_time_ms,
                    "cache_hit": cache_hit,
                    "error_message": error_message
                }
            )
            await self.db_session.commit()
        except Exception as e:
            # Don't fail validation if metrics recording fails
            logger.warning(f"Failed to record validation metric: {e}")
    
    async def validate_actor(self, actor_type: str, actor_id: UUID) -> bool:
        """
        Validates that an actor_id exists in the appropriate table.
        
        Args:
            actor_type: One of 'human', 'synth', 'synth_class', 'client', 'skill_module'
            actor_id: UUID of the actor to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValueError: If actor_type is not valid
        """
        start_time = time.time()
        cache_hit = False
        error_message = None
        
        try:
            # Validate actor_type
            if actor_type not in self.ACTOR_TYPE_MAPPING:
                raise ValueError(
                    f"Invalid actor_type '{actor_type}'. "
                    f"Valid types are: {', '.join(self.ACTOR_TYPE_MAPPING.keys())}"
                )
            
            # Check cache first
            cache_key = self._get_cache_key(actor_type, actor_id)
            cached_result = await self.cache.get(cache_key)
            
            if cached_result is not None:
                cache_hit = True
                validation_time_ms = (time.time() - start_time) * 1000
                await self._record_metric(
                    actor_type, actor_id, cached_result, 
                    validation_time_ms, cache_hit
                )
                return cached_result
            
            # Query database
            table_name = self.ACTOR_TYPE_MAPPING[actor_type]
            query = text(f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE id = :actor_id)")
            result = await self.db_session.execute(query, {"actor_id": actor_id})
            exists = result.scalar()
            
            # Cache the result
            await self.cache.set(cache_key, exists)
            
            validation_time_ms = (time.time() - start_time) * 1000
            await self._record_metric(
                actor_type, actor_id, exists, 
                validation_time_ms, cache_hit
            )
            
            return exists
            
        except Exception as e:
            error_message = str(e)
            validation_time_ms = (time.time() - start_time) * 1000
            await self._record_metric(
                actor_type, actor_id, False, 
                validation_time_ms, cache_hit, error_message
            )
            raise
    
    async def batch_validate_actors(
        self, 
        actors: List[Tuple[str, UUID]]
    ) -> Dict[Tuple[str, UUID], bool]:
        """
        Validates multiple actors in a single query for efficiency.
        
        Args:
            actors: List of (actor_type, actor_id) tuples
            
        Returns:
            Dict mapping (actor_type, actor_id) to validation result
        """
        results = {}
        actors_by_type = defaultdict(list)
        
        # Group actors by type for efficient querying
        for actor_type, actor_id in actors:
            if actor_type not in self.ACTOR_TYPE_MAPPING:
                results[(actor_type, actor_id)] = False
                continue
                
            # Check cache first
            cache_key = self._get_cache_key(actor_type, actor_id)
            cached_result = await self.cache.get(cache_key)
            
            if cached_result is not None:
                results[(actor_type, actor_id)] = cached_result
            else:
                actors_by_type[actor_type].append(actor_id)
        
        # Query database for uncached actors
        for actor_type, actor_ids in actors_by_type.items():
            if not actor_ids:
                continue
                
            table_name = self.ACTOR_TYPE_MAPPING[actor_type]
            query = text(f"SELECT id FROM {table_name} WHERE id = ANY(:actor_ids)")
            result = await self.db_session.execute(query, {"actor_ids": actor_ids})
            
            existing_ids = {row[0] for row in result}
            
            # Update results and cache
            for actor_id in actor_ids:
                exists = actor_id in existing_ids
                results[(actor_type, actor_id)] = exists
                
                # Cache the result
                cache_key = self._get_cache_key(actor_type, actor_id)
                await self.cache.set(cache_key, exists)
        
        return results
    
    async def get_actor_info(
        self, 
        actor_type: str, 
        actor_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves basic actor information if valid.
        
        Args:
            actor_type: Actor type
            actor_id: Actor UUID
            
        Returns:
            Dict with actor info or None if not found
        """
        if actor_type not in self.ACTOR_TYPE_MAPPING:
            return None
            
        table_name = self.ACTOR_TYPE_MAPPING[actor_type]
        
        # Define what fields to retrieve for each actor type
        if actor_type == 'human':
            query = text(f"""
                SELECT id, first_name, last_name, email, created_at 
                FROM {table_name} WHERE id = :actor_id
            """)
        elif actor_type == 'synth':
            query = text(f"""
                SELECT id, name, description, created_at 
                FROM {table_name} WHERE id = :actor_id
            """)
        elif actor_type == 'synth_class':
            query = text(f"""
                SELECT id, name, description, created_at 
                FROM {table_name} WHERE id = :actor_id
            """)
        elif actor_type == 'client':
            query = text(f"""
                SELECT id, name, description, created_at 
                FROM {table_name} WHERE id = :actor_id
            """)
        elif actor_type == 'skill_module':
            query = text(f"""
                SELECT id, name, module_type, vendor, version, metadata, created_at 
                FROM {table_name} WHERE id = :actor_id
            """)
        else:
            return None
            
        result = await self.db_session.execute(query, {"actor_id": actor_id})
        row = result.first()
        
        if row:
            return dict(row._mapping)
        return None
    
    async def invalidate_actor_cache(self, actor_type: Optional[str] = None) -> None:
        """
        Invalidate cache entries for a specific actor type or all actors.
        
        Args:
            actor_type: Optional actor type to invalidate (None invalidates all)
        """
        if actor_type:
            await self.cache.delete_pattern(f"{actor_type}:*")
        else:
            # Invalidate all actor types
            for atype in self.ACTOR_TYPE_MAPPING:
                await self.cache.delete_pattern(f"{atype}:*")
                
    def disable_metrics(self) -> None:
        """Disable metrics recording (useful for tests)."""
        self._metrics_enabled = False
        
    def enable_metrics(self) -> None:
        """Enable metrics recording."""
        self._metrics_enabled = True
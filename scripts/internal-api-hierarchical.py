# memory-service/internal_api_hierarchical.py
"""
Enhanced Internal Memory API with Hierarchical Access Support.

This API extends the standard memory service to support hierarchical memory access,
enabling synths to access their synth_class templates and client-level knowledge.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import sys
import os
import logging

# Add shared path for schemas

from database import get_db
from services.memory_manager_hierarchical import HierarchicalMemoryManager
from services.embeddings import EmbeddingService
from sparkjar_crew.shared.schemas.memory_schemas import *
from config import settings

logger = logging.getLogger(__name__)

# Internal API - High Performance IPv6/HTTP with Hierarchical Support
internal_app = FastAPI(
    title="SparkJar Memory Service - Internal (Hierarchical)",
    description="High-performance memory API with hierarchical access for internal services",
    version="2.0.0"
)

def get_memory_manager(db: Session = Depends(get_db)) -> HierarchicalMemoryManager:
    """Dependency to get hierarchical memory manager instance"""
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    return HierarchicalMemoryManager(db, embedding_service)

@internal_app.post("/entities", response_model=List[Dict[str, Any]])
async def create_entities_internal(
    request: CreateEntitiesRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """Create multiple entities - internal high-speed endpoint"""
    try:
        result = await memory_manager.create_entities(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            entities=request.entities
        )
        return result
    except Exception as e:
        logger.error(f"Entity creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Entity creation failed: {str(e)}")

@internal_app.post("/relations", response_model=List[Dict[str, Any]]) 
async def create_relations_internal(
    request: CreateRelationsRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """Create relationships between entities"""
    try:
        result = await memory_manager.create_relations(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            relations=request.relations
        )
        return result
    except Exception as e:
        logger.error(f"Relation creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Relation creation failed: {str(e)}")

@internal_app.post("/observations", response_model=List[Dict[str, Any]])
async def add_observations_internal(
    request: AddObservationsRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """Add observations to existing entities"""
    try:
        result = await memory_manager.add_observations(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            observations=request.observations
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Adding observations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Adding observations failed: {str(e)}")

@internal_app.post("/search", response_model=List[Dict[str, Any]])
async def search_nodes_internal(
    request: SearchRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager),
    include_hierarchy: bool = Query(False, description="Enable hierarchical memory access")
):
    """
    Semantic search of memory entities with optional hierarchy support.
    
    When include_hierarchy=true, synths can search across:
    - Their own memories
    - Their synth_class template memories
    - Optionally, client-level memories
    """
    try:
        result = await memory_manager.search_nodes(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            query=request.query,
            entity_types=request.entity_type,
            limit=request.limit,
            include_hierarchy=include_hierarchy
        )
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@internal_app.post("/hierarchical-search", response_model=List[Dict[str, Any]])
async def search_hierarchical_memories(
    request: SearchRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager),
    include_synth_class: bool = Query(True, description="Include synth_class memories"),
    include_client: bool = Query(False, description="Include client-level memories")
):
    """
    Dedicated hierarchical search endpoint with fine-grained control.
    
    This endpoint always uses hierarchical search and allows control over
    which memory contexts to include in the search.
    """
    try:
        result = await memory_manager.search_hierarchical_memories(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            query=request.query,
            entity_types=request.entity_type,
            include_synth_class=include_synth_class,
            include_client=include_client,
            limit=request.limit
        )
        return result
    except Exception as e:
        logger.error(f"Hierarchical search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hierarchical search failed: {str(e)}")

@internal_app.post("/get-entities", response_model=List[Dict[str, Any]])
async def get_entities_internal(
    request: GetEntitiesRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager),
    include_hierarchy: bool = Query(False, description="Enable hierarchical memory access")
):
    """Get specific entities by name with optional hierarchy support"""
    try:
        # Handle both old open_nodes method and new get_entities
        if hasattr(request, 'entity_names'):
            result = await memory_manager.get_entities(
                client_id=request.client_id,
                actor_type=request.actor_type,
                actor_id=request.actor_id,
                entity_names=request.entity_names,
                entity_types=request.entity_types if hasattr(request, 'entity_types') else None,
                include_hierarchy=include_hierarchy
            )
        else:
            # Fallback for legacy open_nodes
            result = await memory_manager.open_nodes(
                client_id=request.client_id,
                actor_type=request.actor_type,
                actor_id=request.actor_id,
                names=request.names
            )
        return result
    except Exception as e:
        logger.error(f"Get entities failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get entities failed: {str(e)}")

@internal_app.post("/cross-context-access", response_model=List[Dict[str, Any]])
async def access_cross_context_memories(
    request: CrossContextAccessRequest,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """
    Explicitly access memories from a different actor context.
    
    This endpoint enables controlled cross-context access with full audit logging
    and permission checks. Use cases include:
    - Synths accessing specific synth_class procedures
    - Admins accessing any memory for debugging
    - Cross-team knowledge sharing (with permissions)
    """
    try:
        result = await memory_manager.access_context_memories(
            client_id=request.client_id,
            requesting_actor_type=request.requesting_actor_type,
            requesting_actor_id=request.requesting_actor_id,
            target_actor_type=request.target_actor_type,
            target_actor_id=request.target_actor_id,
            query=request.query,
            permission_check=request.permission_check
        )
        return result
    except Exception as e:
        logger.error(f"Cross-context access failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cross-context access failed: {str(e)}")

@internal_app.get("/cache-stats")
async def get_cache_statistics(
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """Get cache statistics for monitoring performance"""
    return {
        "cache_size": len(memory_manager._synth_class_cache),
        "cache_ttl": memory_manager._cache_ttl,
        "cached_mappings": list(memory_manager._synth_class_cache.keys())
    }

@internal_app.post("/cache-invalidate")
async def invalidate_cache(
    actor_id: Optional[UUID] = None,
    memory_manager: HierarchicalMemoryManager = Depends(get_memory_manager)
):
    """Invalidate cache entries"""
    memory_manager.invalidate_cache(actor_id)
    return {"status": "cache invalidated", "actor_id": str(actor_id) if actor_id else "all"}

@internal_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-service-internal",
        "version": "2.0.0",
        "features": ["hierarchical-access", "cross-context", "caching"]
    }

# Configuration endpoint for feature flags
@internal_app.get("/config/hierarchy")
async def get_hierarchy_config():
    """Get current hierarchy configuration"""
    return {
        "hierarchy_enabled": settings.ENABLE_MEMORY_HIERARCHY 
            if hasattr(settings, 'ENABLE_MEMORY_HIERARCHY') else True,
        "default_include_synth_class": True,
        "default_include_client": False,
        "cache_ttl_seconds": 300
    }

if __name__ == "__main__":
    import uvicorn
    # IPv6 support - bind to all interfaces including IPv6
    uvicorn.run(
        internal_app,
        host="::",  # IPv6 all interfaces
        port=8002,
        log_level="info"
    )
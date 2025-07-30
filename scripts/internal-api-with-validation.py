# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# memory-service/internal_api_with_validation.py
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
import json
import sys
import os
import logging

# Add shared path for schemas

from database import get_db, get_async_db
from services.memory_manager import MemoryManager
from services.embeddings import EmbeddingService
from services.actor_validator import ActorValidator, InvalidActorError
from sparkjar_crew.shared.schemas.memory_schemas import *
from config import settings

logger = logging.getLogger(__name__)

# Internal API - High Performance IPv6/HTTP
internal_app = FastAPI(
    title="SparkJar Memory Service - Internal",
    description="High-performance memory API for internal services with actor validation",
    version="1.1.0"
)

# Dependency injection for services
async def get_actor_validator(db: AsyncSession = Depends(get_async_db)) -> ActorValidator:
    """Dependency to get actor validator instance"""
    return ActorValidator(db)

def get_memory_manager(
    db: Session = Depends(get_db),
    actor_validator: ActorValidator = Depends(get_actor_validator)
) -> MemoryManager:
    """Dependency to get memory manager instance with validation"""
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    return MemoryManager(db, embedding_service, actor_validator)

# Error response models
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Custom exception handlers
@internal_app.exception_handler(InvalidActorError)
async def invalid_actor_handler(request, exc: InvalidActorError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": "MEM-102",
            "message": str(exc),
            "details": {
                "actor_type": exc.actor_type,
                "actor_id": str(exc.actor_id)
            }
        }
    )

@internal_app.post("/entities/upsert", response_model=List[Dict[str, Any]])
async def upsert_entities_internal(
    request: CreateEntitiesRequest,
    skill_module_id: Optional[UUID] = None,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Upsert entities with optional skill module context - internal endpoint"""
    try:
        result = await memory_manager.upsert_entities(
            client_id=request.actor_id  # When actor_type="client", this is the client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            entities=request.entities,
            skill_module_id=skill_module_id
        )
        return result
    except InvalidActorError:
        # Re-raise for custom handler
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MEM-103",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Entity upsert failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity upsert failed: {str(e)}"
        )

@internal_app.post("/entities", response_model=List[Dict[str, Any]])
async def create_entities_internal(
    request: CreateEntitiesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create multiple entities - internal high-speed endpoint with validation"""
    try:
        result = await memory_manager.create_entities(
            client_id=request.actor_id  # When actor_type="client", this is the client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            entities=request.entities
        )
        return result
    except InvalidActorError:
        # Re-raise for custom handler
        raise
    except ValueError as e:
        if "Invalid actor_type" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MEM-101",
                    "message": str(e)
                }
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Entity creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Entity creation failed: {str(e)}"
        )

@internal_app.post("/relations", response_model=List[Dict[str, Any]]) 
async def create_relations_internal(
    request: CreateRelationsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create relationships between entities with validation"""
    try:
        result = await memory_manager.create_relations(
            client_id=request.actor_id  # When actor_type="client", this is the client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            relations=request.relations
        )
        return result
    except InvalidActorError:
        # Re-raise for custom handler
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Relation creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relation creation failed: {str(e)}"
        )

@internal_app.post("/observations", response_model=List[Dict[str, Any]])
async def add_observations_internal(
    request: AddObservationsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Add observations to existing entities with validation"""
    try:
        result = await memory_manager.add_observations(
            client_id=request.actor_id  # When actor_type="client", this is the client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            observations=request.observations
        )
        return result
    except InvalidActorError:
        # Re-raise for custom handler
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Adding observations failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adding observations failed: {str(e)}"
        )

@internal_app.post("/search", response_model=List[Dict[str, Any]])
async def search_nodes_internal(
    request: SearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Semantic search of memory entities - validation on write, not read"""
    try:
        # Note: We don't validate actor on search operations since we're just reading
        result = await memory_manager.search_nodes(
            client_id=request.actor_id  # When actor_type="client", this is the client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            query=request.query,
            entity_type=request.entity_type,
            limit=request.limit
        )
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@internal_app.get("/health")
async def health_check_internal():
    """Health check endpoint for internal API"""
    return {
        "status": "healthy",
        "service": "memory-service-internal",
        "version": "1.1.0",
        "features": ["actor_validation", "ipv6_ready"]
    }

@internal_app.get("/validation/stats")
async def get_validation_stats(
    actor_type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get validation statistics for monitoring"""
    try:
        from sqlalchemy import text
        
        query = """
            SELECT 
                actor_type,
                validation_result,
                COUNT(*) as count,
                AVG(validation_time_ms) as avg_time_ms,
                SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
            FROM actor_validation_metrics
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        
        if actor_type:
            query += " AND actor_type = :actor_type"
            result = await db.execute(text(query), {"actor_type": actor_type})
        else:
            query += " GROUP BY actor_type, validation_result"
            result = await db.execute(text(query))
        
        stats = []
        for row in result:
            stats.append({
                "actor_type": row.actor_type,
                "validation_result": row.validation_result,
                "count": row.count,
                "avg_time_ms": float(row.avg_time_ms) if row.avg_time_ms else 0,
                "cache_hits": row.cache_hits
            })
        
        return {"stats": stats, "period": "last_24_hours"}
        
    except Exception as e:
        logger.error(f"Failed to get validation stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve validation statistics"
        )

# Startup event to log IPv6 configuration
@internal_app.on_event("startup")
async def startup_event():
    """Log startup information including IPv6 status"""
    logger.info("Memory Service Internal API starting...")
    logger.info("Actor validation enabled")
    logger.info("IPv6 ready - binding to all interfaces (0.0.0.0)")
    
    # Test database connectivity
    try:
        async with get_async_db() as db:
            result = await db.execute(text("SELECT 1"))
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # Bind to 0.0.0.0 for IPv6 compatibility on Railway
    uvicorn.run(
        internal_app,
        host="0.0.0.0",  # Important for IPv6 on Railway
        port=8001,
        log_level="info"
    )
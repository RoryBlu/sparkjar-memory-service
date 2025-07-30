#!/usr/bin/env python3
"""Minimal working internal API for Railway deployment."""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from uuid import UUID
import os
import json
import logging
from datetime import datetime
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set!")
    # Use a dummy URL to prevent crashes during startup
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with error handling
try:
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    engine = None
    AsyncSessionLocal = None

# FastAPI app
internal_app = FastAPI(
    title="SparkJar Memory Service - Internal",
    description="Memory API for internal services",
    version="1.0.0"
)

# Pydantic models
class EntityCreate(BaseModel):
    name: str
    entityType: str
    metadata: Dict[str, Any] = {}
    client_id: Optional[str] = None
    actor_type: Optional[str] = "CLIENT"
    actor_id: Optional[str] = None
    observations: List[Dict] = []

class ObservationCreate(BaseModel):
    entityName: str
    contents: List[Dict[str, Any]]

# Dependency
async def get_db():
    if not AsyncSessionLocal:
        raise HTTPException(status_code=503, detail="Database not configured")
    async with AsyncSessionLocal() as session:
        yield session

@internal_app.get("/")
async def root():
    """Root endpoint for basic connectivity check."""
    return {
        "service": "memory-internal",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/health", "/entities", "/observations", "/search"]
    }

@internal_app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "service": "memory-internal",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "port": os.getenv("PORT", "unknown"),
            "has_database_url": bool(os.getenv("DATABASE_URL")),
            "environment": os.getenv("ENVIRONMENT", "unknown")
        }
    }
    
    if not AsyncSessionLocal:
        health_status.update({
            "status": "degraded",
            "database": "not configured",
            "message": "Service running without database"
        })
        return health_status
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        health_status.update({
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status.update({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        })
    
    return health_status

@internal_app.post("/entities")
async def create_entities(
    entities: List[EntityCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create memory entities."""
    created = []
    
    for entity in entities:
        try:
            # Insert entity
            result = await db.execute(
                text("""
                    INSERT INTO entities (
                        name, entity_type, metadata, 
                        client_id, actor_type, actor_id
                    ) VALUES (
                        :name, :entity_type, :metadata::jsonb,
                        :client_id, :actor_type, :actor_id
                    ) 
                    ON CONFLICT (name, client_id, actor_type, actor_id) 
                    DO UPDATE SET 
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, name, entity_type, created_at
                """),
                {
                    "name": entity.name,
                    "entity_type": entity.entityType,
                    "metadata": json.dumps(entity.metadata),
                    "client_id": entity.client_id or str(UUID(int=0)),
                    "actor_type": entity.actor_type,
                    "actor_id": entity.actor_id or str(UUID(int=0))
                }
            )
            
            row = result.fetchone()
            created.append({
                "id": str(row.id),
                "name": row.name,
                "entity_type": row.entity_type,
                "created_at": row.created_at.isoformat()
            })
            
            logger.info(f"Created entity: {entity.name} in {entity.actor_type} realm")
            
        except Exception as e:
            logger.error(f"Error creating entity {entity.name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    await db.commit()
    return created

@internal_app.post("/observations")
async def create_observations(
    observations: List[ObservationCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create observations."""
    created = []
    
    for obs in observations:
        # Find entity
        result = await db.execute(
            text("""
                SELECT id FROM entities 
                WHERE name = :name 
                LIMIT 1
            """),
            {"name": obs.entityName}
        )
        entity = result.fetchone()
        
        if not entity:
            logger.warning(f"Entity not found: {obs.entityName}")
            continue
        
        # Create observations
        for content in obs.contents:
            try:
                result = await db.execute(
                    text("""
                        INSERT INTO observations (
                            entity_id, observation_type, value, 
                            source, metadata
                        ) VALUES (
                            :entity_id, :type, :value,
                            :source, :metadata::jsonb
                        ) RETURNING id, created_at
                    """),
                    {
                        "entity_id": entity.id,
                        "type": content.get("type", "general"),
                        "value": content.get("value", ""),
                        "source": content.get("source", "api"),
                        "metadata": json.dumps(content.get("metadata", {}))
                    }
                )
                
                row = result.fetchone()
                created.append({
                    "id": str(row.id),
                    "entity_name": obs.entityName,
                    "created_at": row.created_at.isoformat()
                })
                
                logger.info(f"Added observation to {obs.entityName}")
                
            except Exception as e:
                logger.error(f"Error creating observation: {e}")
    
    await db.commit()
    return created

@internal_app.post("/search")
async def search_memories(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Search memories."""
    query = request.get("query", "")
    limit = request.get("limit", 10)
    
    try:
        result = await db.execute(
            text("""
                SELECT 
                    e.id, e.name, e.entity_type, e.metadata,
                    e.actor_type, e.client_id
                FROM entities e
                WHERE 
                    e.name ILIKE :query
                    OR e.metadata::text ILIKE :query
                ORDER BY e.created_at DESC
                LIMIT :limit
            """),
            {
                "query": f"%{query}%",
                "limit": limit
            }
        )
        
        entities = result.fetchall()
        
        results = []
        for entity in entities:
            results.append({
                "entity": {
                    "id": str(entity.id),
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "metadata": entity.metadata,
                    "actor_type": entity.actor_type
                },
                "score": 1.0,
                "context": entity.actor_type
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@internal_app.on_event("startup")
async def startup():
    """Startup event."""
    logger.info("Memory service starting up...")
    logger.info(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'not configured'}")

@internal_app.on_event("shutdown")
async def shutdown():
    """Shutdown event."""
    await engine.dispose()
    logger.info("Memory service shutting down...")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(internal_app, host="0.0.0.0", port=port)
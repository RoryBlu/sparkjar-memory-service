#!/usr/bin/env python3
"""Unified internal API with optional database support."""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends

from config import settings


internal_app = FastAPI(
    title="SparkJar Memory Service - Internal",
    description="Internal memory API for service-to-service communication",
    version="1.0.0",
)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logging.getLogger(__name__).info("Using database for storage")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@internal_app.get("/health")
async def health_check():
    status = {
        "service": "memory-internal",
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        status["status"] = "healthy"
        status["database"] = "connected"
    except Exception as e:
        logging.getLogger(__name__).error(f"Health check failed: {e}")
        status["status"] = "unhealthy"
        status["database"] = "disconnected"
    return status


@internal_app.post("/entities")
async def create_entities(
    entities: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
):
    created = []
    session: AsyncSession = db
    for entity in entities:
        result = await session.execute(
            text(
                """
                INSERT INTO entities (name, entity_type, metadata, client_id, actor_type, actor_id)
                VALUES (:name, :entity_type, :metadata::jsonb, :client_id, :actor_type, :actor_id)
                ON CONFLICT (name, client_id, actor_type, actor_id)
                DO UPDATE SET metadata = EXCLUDED.metadata, updated_at = CURRENT_TIMESTAMP
                RETURNING id, name, entity_type, created_at
                """
            ),
            {
                "name": entity.get("name"),
                "entity_type": entity.get("entityType"),
                "metadata": json.dumps(entity.get("metadata", {})),
                "client_id": entity.get("client_id", str(UUID(int=0))),
                "actor_type": entity.get("actor_type", "CLIENT"),
                "actor_id": entity.get("actor_id", str(UUID(int=0))),
            },
        )
        row = result.fetchone()
        created.append(
            {
                "id": str(row.id),
                "name": row.name,
                "entity_type": row.entity_type,
                "created_at": row.created_at.isoformat(),
            }
        )
    await session.commit()
    return created


@internal_app.post("/observations")
async def create_observations(
    observations: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
):
    created = []
    session: AsyncSession = db
    for obs in observations:
        result = await session.execute(
            text("SELECT id FROM entities WHERE name = :name LIMIT 1"),
            {"name": obs.get("entityName")},
        )
        entity = result.fetchone()
        if not entity:
            continue
        for content in obs.get("contents", []):
                result = await session.execute(
                    text(
                        """
                        INSERT INTO observations (entity_id, observation_type, value, source, metadata)
                        VALUES (:entity_id, :type, :value, :source, :metadata::jsonb)
                        RETURNING id, created_at
                        """
                    ),
                    {
                        "entity_id": entity.id,
                        "type": content.get("type", "general"),
                        "value": content.get("value", ""),
                        "source": content.get("source", "api"),
                        "metadata": json.dumps(content.get("metadata", {})),
                    },
                )
                row = result.fetchone()
                created.append(
                    {
                        "id": str(row.id),
                        "entity_name": obs.get("entityName"),
                        "created_at": row.created_at.isoformat(),
                    }
                )
        await session.commit()
    return created


@internal_app.post("/search")
async def search_memories(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    query = request.get("query", "")
    limit = request.get("limit", 10)
    session: AsyncSession = db
    result = await session.execute(
        text(
            """
            SELECT id, name, entity_type, metadata, actor_type
            FROM entities
            WHERE name ILIKE :query OR metadata::text ILIKE :query
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"query": f"%{query}%", "limit": limit},
    )
    entities = result.fetchall()
    return [
        {
            "entity": {
                "id": str(e.id),
                "name": e.name,
                "entity_type": e.entity_type,
                "metadata": e.metadata,
                "actor_type": e.actor_type,
            },
            "score": 1.0,
            "context": e.actor_type,
        }
        for e in entities
    ]


@internal_app.get("/debug/storage")
async def debug_storage():
    return {"detail": "Not available"}


@internal_app.on_event("shutdown")
async def shutdown():
    await engine.dispose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(internal_app, host="0.0.0.0", port=settings.INTERNAL_API_PORT)


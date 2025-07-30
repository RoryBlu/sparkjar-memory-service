#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""Seed relationship schemas into the object_schemas table."""

import asyncio
import json
from datetime import datetime

from services.crew_api.src.database.connection import get_direct_session
from sqlalchemy import text


async def seed_relationship_schemas():
    """Seed the object_schemas table with relationship schemas."""
    logger.info("🔗 Seeding relationship schemas...")

    schemas = [
        {
            "name": "memory_relationship_metadata",
            "object_type": "memory_relationship_metadata",
            "description": "Schema for memory relationship metadata",
            "schema": {
                "$id": "memory_relationship_metadata",
                "type": "object",
                "title": "Memory Relationship Metadata Schema",
                "properties": {
                    "strength": {"type": "number", "minimum": 0, "maximum": 1},
                    "frequency": {
                        "type": "string",
                        "enum": ["always", "usually", "sometimes", "rarely"],
                    },
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["strength", "frequency"],
                "additionalProperties": True,
            },
        }
    ]

    inserted = 0
    updated = 0
    async with get_direct_session() as session:
        for schema in schemas:
            result = await session.execute(
                text(
                    """
                        SELECT 1 FROM object_schemas
                        WHERE name = :name AND object_type = :object_type
                    """
                ),
                {"name": schema["name"], "object_type": schema["object_type"]},
            )
            existing = result.first()
            if existing:
                await session.execute(
                    text(
                        """
                        UPDATE object_schemas
                        SET schema = :schema,
                            description = :description,
                            updated_at = :updated_at
                        WHERE name = :name AND object_type = :object_type
                        """
                    ),
                    {
                        "name": schema["name"],
                        "object_type": schema["object_type"],
                        "schema": json.dumps(schema["schema"]),
                        "description": schema.get("description", ""),
                        "updated_at": datetime.utcnow(),
                    },
                )
                updated += 1
                logger.info(
                    f"✅ Updated: {schema['name']} ({schema['object_type']})"
                )
            else:
                await session.execute(
                    text(
                        """
                        INSERT INTO object_schemas
                        (name, object_type, schema, description, created_at, updated_at)
                        VALUES (:name, :object_type, :schema, :description, :created_at, :updated_at)
                        """
                    ),
                    {
                        "name": schema["name"],
                        "object_type": schema["object_type"],
                        "schema": json.dumps(schema["schema"]),
                        "description": schema.get("description", ""),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )
                inserted += 1
                logger.info(
                    f"✅ Inserted: {schema['name']} ({schema['object_type']})"
                )

        await session.commit()

        logger.info("\n🎉 Schema seeding complete!")
        logger.info(f"   Inserted: {inserted} schemas")
        logger.info(f"   Updated: {updated} schemas")


if __name__ == "__main__":
    asyncio.run(seed_relationship_schemas())

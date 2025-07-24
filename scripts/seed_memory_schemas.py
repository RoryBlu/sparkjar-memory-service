#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Seed memory observation schemas into the object_schemas table.
This needs to be run before using the memory service.
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path

from services.crew_api.src.database.connection import get_direct_session
from sqlalchemy import text

async def seed_memory_schemas():
    """Seed the object_schemas table with memory schemas"""
    logger.info("🌱 Seeding memory schemas...")
    
    schemas = [
        {
            "name": "base_observation",
            "object_type": "memory_observation",
            "description": "Base schema for all memory observations",
            "schema": {
                "$id": "base_observation",
                "type": "object",
                "title": "Base Observation Schema",
                "properties": {
                    "content": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 10000
                    },
                    "source": {
                        "type": "string"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    }
                },
                "required": ["content"],
                "additionalProperties": True
            }
        },
        {
            "name": "skill_observation",
            "object_type": "memory_observation",
            "description": "Schema for skill-related observations",
            "schema": {
                "$id": "skill_observation",
                "type": "object",
                "title": "Skill Observation Schema",
                "properties": {
                    "type": {
                        "type": "string",
                        "const": "skill"
                    },
                    "value": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "maxLength": 100
                            },
                            "category": {
                                "type": "string",
                                "enum": ["technical", "creative", "analytical", "communication", "leadership", "other"]
                            },
                            "level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced", "expert"]
                            },
                            "evidence": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": True
                    },
                    "source": {
                        "type": "string"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    }
                },
                "required": ["type", "value"],
                "additionalProperties": True
            }
        },
        {
            "name": "database_ref_observation",
            "object_type": "memory_observation",
            "description": "Schema for database reference observations",
            "schema": {
                "$id": "database_ref_observation",
                "type": "object",
                "title": "Database Reference Observation Schema",
                "properties": {
                    "type": {
                        "type": "string",
                        "const": "database_ref"
                    },
                    "value": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "maxLength": 100
                            },
                            "record_id": {
                                "type": "string",
                                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": ["created", "modified", "referenced", "derived_from", "related_to"]
                            },
                            "key_fields": {
                                "type": "object",
                                "additionalProperties": True
                            }
                        },
                        "required": ["table_name", "record_id", "relationship_type"],
                        "additionalProperties": True
                    },
                    "source": {
                        "type": "string"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    }
                },
                "required": ["type", "value"],
                "additionalProperties": True
            }
        },
        {
            "name": "writing_pattern_observation",
            "object_type": "memory_observation",
            "description": "Schema for writing pattern observations",
            "schema": {
                "$id": "writing_pattern_observation",
                "type": "object",
                "title": "Writing Pattern Observation Schema",
                "properties": {
                    "type": {
                        "type": "string",
                        "const": "writing_pattern"
                    },
                    "value": {
                        "type": "object",
                        "properties": {
                            "pattern_type": {
                                "type": "string",
                                "enum": ["style", "workflow", "structure", "habit", "preference"]
                            },
                            "content_type": {
                                "type": "string",
                                "enum": ["blog", "article", "email", "documentation", "social", "other"]
                            },
                            "frequency": {
                                "type": "string",
                                "enum": ["always", "usually", "sometimes", "rarely"]
                            },
                            "description": {
                                "type": "string",
                                "maxLength": 500
                            }
                        },
                        "required": ["pattern_type", "content_type"],
                        "additionalProperties": True
                    },
                    "source": {
                        "type": "string"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    }
                },
                "required": ["type", "value"],
                "additionalProperties": True
            }
        },
        {
            "name": "person_entity_metadata",
            "object_type": "memory_entity_metadata",
            "description": "Schema for person entity metadata",
            "schema": {
                "$id": "person_entity_metadata",
                "type": "object",
                "title": "Person Entity Metadata Schema",
                "properties": {
                    "role": {
                        "type": "string",
                        "maxLength": 100
                    },
                    "organization": {
                        "type": "string",
                        "maxLength": 200
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "relationship": {
                        "type": "string",
                        "enum": ["colleague", "client", "collaborator", "friend", "other"]
                    },
                    "last_contact": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "expertise": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "additionalProperties": True
            }
        },
        {
            "name": "synth_entity_metadata",
            "object_type": "memory_entity_metadata",
            "description": "Schema for synth/AI agent entity metadata",
            "schema": {
                "$id": "synth_entity_metadata",
                "type": "object",
                "title": "Synth Entity Metadata Schema",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["crewai_agent", "langchain_agent", "custom_agent", "ai_assistant", "other"]
                    },
                    "model_name": {
                        "type": "string"
                    },
                    "version": {
                        "type": "string"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "last_active": {
                        "type": "string",
                        "format": "date-time"
                    }
                },
                "required": ["agent_type"],
                "additionalProperties": True
            }
        }
    ]
    
    async with get_direct_session() as session:
        inserted = 0
        updated = 0
        
        for schema in schemas:
            # Check if schema already exists
            result = await session.execute(
                text("""
                    SELECT id FROM object_schemas 
                    WHERE name = :name AND object_type = :object_type
                """),
                {"name": schema["name"], "object_type": schema["object_type"]}
            )
            existing = result.first()
            
            if existing:
                # Update existing schema
                await session.execute(
                    text("""
                        UPDATE object_schemas 
                        SET schema = :schema,
                            description = :description,
                            updated_at = :updated_at
                        WHERE name = :name AND object_type = :object_type
                    """),
                    {
                        "name": schema["name"],
                        "object_type": schema["object_type"],
                        "schema": json.dumps(schema["schema"]),
                        "description": schema.get("description", ""),
                        "updated_at": datetime.utcnow()
                    }
                )
                updated += 1
                logger.info(f"✅ Updated: {schema['name']} ({schema['object_type']})")
            else:
                # Insert new schema
                await session.execute(
                    text("""
                        INSERT INTO object_schemas 
                        (name, object_type, schema, description, created_at, updated_at)
                        VALUES (:name, :object_type, :schema, :description, :created_at, :updated_at)
                    """),
                    {
                        "name": schema["name"],
                        "object_type": schema["object_type"],
                        "schema": json.dumps(schema["schema"]),
                        "description": schema.get("description", ""),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                )
                inserted += 1
                logger.info(f"✅ Inserted: {schema['name']} ({schema['object_type']})")
        
        await session.commit()
        
        logger.info(f"\n🎉 Schema seeding complete!")
        logger.info(f"   Inserted: {inserted} schemas")
        logger.info(f"   Updated: {updated} schemas")

if __name__ == "__main__":
    asyncio.run(seed_memory_schemas())
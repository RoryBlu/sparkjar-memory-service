#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Seed sequential thinking schemas into the object_schemas table.
This needs to be run before using the thinking service with schema validation.
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add src to path

from services.crew_api.src.database.connection import get_direct_session
from sqlalchemy import text

async def seed_thinking_schemas():
    """Seed the object_schemas table with thinking schemas"""
    logger.info("🧠 Seeding sequential thinking schemas...")
    
    schemas = [
        {
            "name": "thinking_session_metadata",
            "object_type": "thinking_metadata",
            "description": "Schema for thinking session metadata",
            "schema": {
                "$id": "thinking_session_metadata",
                "type": "object",
                "title": "Thinking Session Metadata Schema",
                "properties": {
                    "context": {
                        "type": "object",
                        "properties": {
                            "domain": {
                                "type": "string",
                                "maxLength": 100
                            },
                            "task_type": {
                                "type": "string",
                                "enum": ["problem_solving", "planning", "analysis", "creative", "decision_making", "other"]
                            },
                            "complexity": {
                                "type": "string",
                                "enum": ["simple", "moderate", "complex", "very_complex"]
                            },
                            "time_constraint": {
                                "type": "string",
                                "format": "duration"
                            }
                        },
                        "additionalProperties": True
                    },
                    "participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "entity_id": {
                                    "type": "string",
                                    "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                                }
                            },
                            "required": ["name", "role"]
                        }
                    },
                    "goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "resources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "reference": {"type": "string"},
                                "description": {"type": "string"}
                            },
                            "required": ["type", "reference"]
                        }
                    }
                },
                "additionalProperties": True
            }
        },
        {
            "name": "thought_metadata",
            "object_type": "thinking_metadata",
            "description": "Schema for individual thought metadata",
            "schema": {
                "$id": "thought_metadata",
                "type": "object",
                "title": "Thought Metadata Schema",
                "properties": {
                    "thought_type": {
                        "type": "string",
                        "enum": ["observation", "hypothesis", "question", "answer", "conclusion", "action", "reflection", "revision"]
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "reasoning_method": {
                        "type": "string",
                        "enum": ["deductive", "inductive", "abductive", "analogical", "causal", "probabilistic", "other"]
                    },
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "reference": {"type": "string"},
                                "strength": {
                                    "type": "string",
                                    "enum": ["weak", "moderate", "strong", "conclusive"]
                                }
                            },
                            "required": ["source"]
                        }
                    },
                    "assumptions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "alternatives_considered": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "alternative": {"type": "string"},
                                "reason_rejected": {"type": "string"}
                            },
                            "required": ["alternative"]
                        }
                    },
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    }
                },
                "additionalProperties": True
            }
        },
        {
            "name": "revision_metadata",
            "object_type": "thinking_metadata",
            "description": "Schema for thought revision metadata",
            "schema": {
                "$id": "revision_metadata",
                "type": "object",
                "title": "Revision Metadata Schema",
                "properties": {
                    "revision_type": {
                        "type": "string",
                        "enum": ["correction", "clarification", "expansion", "refinement", "complete_rethink"]
                    },
                    "revision_reason": {
                        "type": "string",
                        "maxLength": 500
                    },
                    "changes_made": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "aspect": {"type": "string"},
                                "from": {"type": "string"},
                                "to": {"type": "string"},
                                "rationale": {"type": "string"}
                            },
                            "required": ["aspect", "rationale"]
                        }
                    },
                    "impact_assessment": {
                        "type": "object",
                        "properties": {
                            "clarity_improvement": {
                                "type": "string",
                                "enum": ["none", "minor", "moderate", "significant", "major"]
                            },
                            "accuracy_improvement": {
                                "type": "string",
                                "enum": ["none", "minor", "moderate", "significant", "major"]
                            },
                            "completeness_improvement": {
                                "type": "string",
                                "enum": ["none", "minor", "moderate", "significant", "major"]
                            }
                        }
                    },
                    "lessons_learned": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["revision_type", "revision_reason"],
                "additionalProperties": True
            }
        },
        {
            "name": "thinking_pattern",
            "object_type": "thinking_observation",
            "description": "Schema for observed thinking patterns",
            "schema": {
                "$id": "thinking_pattern",
                "type": "object",
                "title": "Thinking Pattern Schema",
                "properties": {
                    "pattern_name": {
                        "type": "string",
                        "maxLength": 100
                    },
                    "pattern_type": {
                        "type": "string",
                        "enum": ["cognitive_bias", "reasoning_strategy", "problem_solving_approach", "decision_pattern", "creative_technique"]
                    },
                    "frequency": {
                        "type": "string",
                        "enum": ["rare", "occasional", "common", "frequent", "dominant"]
                    },
                    "effectiveness": {
                        "type": "string",
                        "enum": ["ineffective", "somewhat_effective", "effective", "very_effective", "optimal"]
                    },
                    "context_dependence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "context": {"type": "string"},
                                "effectiveness_in_context": {
                                    "type": "string",
                                    "enum": ["ineffective", "somewhat_effective", "effective", "very_effective", "optimal"]
                                }
                            },
                            "required": ["context", "effectiveness_in_context"]
                        }
                    },
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["pattern_name", "pattern_type"],
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
        
        logger.info(f"\n🎉 Thinking schema seeding complete!")
        logger.info(f"   Inserted: {inserted} schemas")
        logger.info(f"   Updated: {updated} schemas")

if __name__ == "__main__":
    asyncio.run(seed_thinking_schemas())
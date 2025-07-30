# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Add missing hook type examples to blog writing knowledge.
This completes the blog writing SOP with concrete examples.
"""
import os
import sys
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
# Add crew-api path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from crew-api models
from services.crew_api.src.database.models import MemoryEntities, MemoryObservations
from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine for this script
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))
SessionLocal = sessionmaker(bind=engine)

def add_hook_examples():
    """Add concrete hook type examples to blog writing knowledge"""
    
    logger.info("🚀 Adding hook type examples to blog writing knowledge")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Constants for synth_class 24
        ACTOR_TYPE = 'synth_class'
        ACTOR_ID = '24'  # Now text field - just the number as string
        
        # First, find the Blog SOP entity
        result = db.execute(text("""
            SELECT id, entity_name 
            FROM memory_entities
            WHERE actor_type = :actor_type
            AND actor_id = :actor_id
            AND entity_name LIKE '%Blog Writing Standard Operating Procedure%'
            LIMIT 1
        """), {"actor_type": ACTOR_TYPE, "actor_id": ACTOR_ID})
        
        sop = result.fetchone()
        if not sop:
            logger.info("❌ Blog SOP not found!")
            return
        
        sop_id = sop[0]
        logger.info(f"✅ Found Blog SOP: {sop[1]}")
        
        # Create hook examples observation
        hook_examples = MemoryObservations(
            id=uuid4(),
            entity_id=sop_id,
            observation_type='writing_technique',
            observation_value={
                "technique": "Introduction Hook Types",
                "category": "engagement",
                "description": "Five proven hook types to grab reader attention",
                "examples": [
                    {
                        "type": "Question Hook",
                        "example": "Have you ever wondered why 90% of startups fail within their first year?",
                        "when_to_use": "When addressing common pain points or curiosities",
                        "effectiveness": "High for problem-aware audiences"
                    },
                    {
                        "type": "Statistic Hook",
                        "example": "According to recent studies, the average person spends 6 hours and 58 minutes per day looking at screens—that's more than 100 days per year.",
                        "when_to_use": "When you have surprising or counterintuitive data",
                        "effectiveness": "High for data-driven readers"
                    },
                    {
                        "type": "Story Hook",
                        "example": "Sarah stared at her laptop screen at 3 AM, wondering how her competitor had suddenly outranked her on every keyword. Then she discovered something that changed everything.",
                        "when_to_use": "For creating emotional connection and relatability",
                        "effectiveness": "High for narrative-driven content"
                    },
                    {
                        "type": "Problem Hook",
                        "example": "Your website traffic is declining. Your conversions are dropping. And you have no idea why. Sound familiar?",
                        "when_to_use": "When targeting readers experiencing specific challenges",
                        "effectiveness": "High for solution-seeking audiences"
                    },
                    {
                        "type": "Quote Hook",
                        "example": "'Content is king, but distribution is queen and she wears the pants.' - Jonathan Perelman. This insight revolutionized how we think about content marketing.",
                        "when_to_use": "When expert authority adds credibility",
                        "effectiveness": "High for establishing expertise"
                    }
                ],
                "best_practices": [
                    "Match hook type to content purpose",
                    "Keep hooks under 50 words",
                    "Follow immediately with context",
                    "Test different hooks for same content",
                    "Track engagement metrics by hook type"
                ]
            },
            source='synth_class_24_writing_guide'
        )
        
        db.add(hook_examples)
        db.commit()
        
        logger.info("✅ Successfully added hook type examples")
        
        # Verify the addition
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM memory_observations
            WHERE entity_id = :sop_id
            AND observation_type = 'writing_technique'
        """), {"sop_id": sop_id})
        
        count = result.scalar()
        logger.info(f"📊 Total writing technique observations for Blog SOP: {count}")
        
    except Exception as e:
        logger.error(f"❌ Error adding hook examples: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_hook_examples()
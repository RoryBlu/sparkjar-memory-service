# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Simple update of actor_id for synth_class memories.
"""
import os
import sys
from pathlib import Path
from uuid import UUID
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to Python path

# Load environment variables
load_dotenv()

from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))

def update_actor_ids():
    """Update synth_class actor_ids"""
    
    logger.info("🔧 Updating synth_class actor_ids...\n")
    
    old_id = UUID('24000000-0000-0000-0000-000000000024')
    new_id = UUID('00000000-0000-0000-0000-000000000024')
    
    logger.info(f"   Old actor_id: {old_id}")
    logger.info(f"   New actor_id: {new_id}")
    
    with engine.begin() as conn:
        # Simple update
        result = conn.execute(text("""
            UPDATE memory_entities 
            SET actor_id = :new_id
            WHERE actor_type = 'synth_class' 
            AND actor_id = :old_id
        """), {"new_id": new_id, "old_id": old_id})
        
        logger.info(f"\n   ✅ Updated {result.rowcount} records")
        
        # Verify
        result = conn.execute(text("""
            SELECT COUNT(*), actor_id
            FROM memory_entities
            WHERE actor_type = 'synth_class'
            GROUP BY actor_id
        """))
        
        logger.info(f"\n📋 Verification:")
        for row in result:
            logger.info(f"   - {row[0]} records with actor_id: {row[1]}")
    
    logger.info(f"\n✅ Update complete!")

if __name__ == "__main__":
    update_actor_ids()
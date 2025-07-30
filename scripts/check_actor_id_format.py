# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Check the actual actor_id format in the database after the schema change.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to Python path

# Load environment variables
load_dotenv()

from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT

# Create synchronous engine
engine = create_engine(DATABASE_URL_DIRECT.replace('postgresql+asyncpg', 'postgresql'))

def check_actor_ids():
    """Check actor_id formats after DB change to text"""
    
    logger.info("🔍 Checking actor_id formats after DB change to text\n")
    
    with engine.connect() as conn:
        # Check all unique actor_ids for synth_class
        result = conn.execute(text("""
            SELECT DISTINCT actor_type, actor_id, COUNT(*) as count
            FROM memory_entities
            WHERE actor_type IN ('synth_class', 'synth', 'client')
            GROUP BY actor_type, actor_id
            ORDER BY actor_type, count DESC
        """))
        
        logger.info("📋 Current actor_id values:")
        for row in result:
            logger.info(f"   - {row[0]}: '{row[1]}' ({row[2]} records)")
            logger.info(f"     Type: {type(row[1])}, Length: {len(str(row[1]))}")
        
        # Check specifically for blog writing entities
        logger.info("\n📋 Blog writing entities:")
        result = conn.execute(text("""
            SELECT entity_name, actor_id, created_at
            FROM memory_entities
            WHERE actor_type = 'synth_class'
            AND entity_name LIKE '%Blog%'
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        for row in result:
            logger.info(f"   - {row[0]}")
            logger.info(f"     actor_id: '{row[1]}'")
            logger.info(f"     created: {row[2]}")

if __name__ == "__main__":
    check_actor_ids()
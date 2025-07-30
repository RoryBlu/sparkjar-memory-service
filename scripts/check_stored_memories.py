# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Check what was actually stored in memory_entities.
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

def check_memories():
    """Check stored memories"""
    
    logger.info("🔍 Checking stored memories...\n")
    
    with engine.connect() as conn:
        # Check synth_class memories
        result = conn.execute(text("""
            SELECT actor_type, actor_id, entity_name, entity_type
            FROM memory_entities
            WHERE actor_type = 'synth_class'
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        logger.info("📋 Synth class memories:")
        for row in result:
            logger.info(f"   - actor_id: {row[1]}")
            logger.info(f"     name: {row[2]}")
            logger.info(f"     type: {row[3]}")
            logger.info()
        
        # Check specific actor_id formats
        logger.info("\n🔍 Checking specific actor_id values:")
        
        # Check for the UUID I used
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM memory_entities 
            WHERE actor_id = '24000000-0000-0000-0000-000000000024'::uuid
        """))
        count1 = result.scalar()
        logger.info(f"   - actor_id = '24000000-0000-0000-0000-000000000024': {count1} records")
        
        # Check for just '24' as various formats
        test_values = [
            ("'00000000-0000-0000-0000-000000000024'::uuid", "Zero-padded 24"),
            ("'00000024-0000-0000-0000-000000000000'::uuid", "24 in first segment"),
            ("gen_random_uuid()", "Random UUID (example)"),
        ]
        
        for test_val, desc in test_values:
            try:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM memory_entities 
                    WHERE actor_id = {test_val}
                """))
                count = result.scalar()
                logger.info(f"   - {desc}: {count} records")
            except:
                pass

if __name__ == "__main__":
    check_memories()
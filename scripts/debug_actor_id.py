# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Debug actor_id issues
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

def debug_actor_ids():
    """Debug actor_id formats"""
    
    logger.debug("🔍 Debugging actor_id issues...\n")
    
    with engine.connect() as conn:
        # Check what's actually stored
        result = conn.execute(text("""
            SELECT DISTINCT actor_type, actor_id, COUNT(*) as count
            FROM memory_entities
            WHERE actor_type IN ('synth_class', 'synth')
            GROUP BY actor_type, actor_id
            ORDER BY actor_type, actor_id
        """))
        
        logger.info("📋 Current actor_id values:")
        for row in result:
            logger.info(f"   - {row[0]}: {row[1]} ({row[2]} records)")
        
        # Test specific lookups
        test_uuid = UUID('00000000-0000-0000-0000-000000000024')
        
        result = conn.execute(text("""
            SELECT entity_name, actor_id
            FROM memory_entities
            WHERE actor_type = 'synth_class'
            AND actor_id = :test_id
        """), {"test_id": test_uuid})
        
        rows = result.fetchall()
        logger.info(f"\n🔍 Looking for actor_id = {test_uuid}:")
        logger.info(f"   Found {len(rows)} records")
        for row in rows:
            logger.info(f"   - {row[0]}")
        
        # Check what the synth's class_id should map to
        result = conn.execute(text("""
            SELECT s.id, s.first_name, s.synth_classes_id, sc.title
            FROM synths s
            JOIN synth_classes sc ON s.synth_classes_id = sc.id
            WHERE s.synth_classes_id = 24
            LIMIT 5
        """))
        
        logger.info(f"\n📋 Synths with class 24:")
        for row in result:
            logger.info(f"   - {row[1]} (synth_id: {row[0]})")
            logger.info(f"     class: {row[3]} (id: {row[2]})")
            logger.info(f"     Expected class actor_id: 00000000-0000-0000-0000-000000000024")

if __name__ == "__main__":
    debug_actor_ids()
#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Check the actual memory schema in the database.
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

def check_schema():
    """Check the actual memory schema"""
    
    logger.info("🔍 Checking memory schema in database...\n")
    
    with engine.connect() as conn:
        # Check memory_entities columns
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'memory_entities'
            ORDER BY ordinal_position
        """))
        
        logger.info("📋 memory_entities columns:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            logger.info(f"   - {row[0]}: {row[1]} {nullable}")
        
        # Check constraints
        result = conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'memory_entities'::regclass
            AND contype = 'c'
        """))
        
        logger.info("\n📋 memory_entities constraints:")
        for row in result:
            logger.info(f"   - {row[0]}: {row[1]}")
        
        # Check memory_relations columns
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'memory_relations'
            ORDER BY ordinal_position
        """))
        
        logger.info("\n📋 memory_relations columns:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            logger.info(f"   - {row[0]}: {row[1]} {nullable}")

if __name__ == "__main__":
    check_schema()
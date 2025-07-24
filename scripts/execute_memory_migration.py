#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Execute the memory schema migration to support hierarchical knowledge architecture.
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

def execute_migration():
    """Execute the hierarchical memory schema migration"""
    
    migration_file = Path(__file__).parent.parent / 'migrations' / 'update_memory_schema_hierarchical.sql'
    
    if not migration_file.exists():
        logger.info(f"❌ Migration file not found: {migration_file}")
        return False
    
    logger.info(f"🚀 Executing memory schema migration for hierarchical support")
    logger.info(f"   Migration file: {migration_file}")
    
    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Execute migration
    with engine.begin() as conn:
        try:
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    logger.info(f"   Executing statement {i}/{len(statements)}...")
                    conn.execute(text(statement))
            
            logger.info(f"\n✅ Migration completed successfully!")
            logger.info(f"   - memory_entities now allows NULL client_id")
            logger.info(f"   - Added support for synth_class and skill_module actor types")
            logger.info(f"   - Updated unique constraints for hierarchical access")
            logger.info(f"   - Added performance indexes")
            
            # Verify the changes
            result = conn.execute(text("""
                SELECT conname, pg_get_constraintdef(oid) 
                FROM pg_constraint 
                WHERE conname = 'memory_entities_actor_type_check'
            """))
            
            for row in result:
                logger.info(f"\n📋 New actor_type constraint: {row[1]}")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    success = execute_migration()
    if success:
        logger.info("\n🎯 Next steps:")
        logger.info("   1. Run UPDATE_MODELS.py to update SQLAlchemy models")
        logger.info("   2. Execute blog writing knowledge storage script")
        logger.info("   3. Create test synth with blog writer class")
        sys.exit(0)
    else:
        sys.exit(1)
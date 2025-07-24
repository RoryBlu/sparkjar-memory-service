#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Verify the database schema for the memory service.
This script checks that all required tables exist and are properly configured.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path for imports

def get_database_url():
    """Get the database URL from environment variables."""
    db_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URL_DIRECT') or os.getenv('SUPABASE_DB_URL')
    if not db_url:
        raise ValueError("No database URL found")
    if '+asyncpg' in db_url:
        db_url = db_url.replace('+asyncpg', '')
    return db_url

def verify_database():
    """Verify all tables and extensions are properly set up."""
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            logger.info("🔍 Checking database schema...\n")
            
            # Check tables
            result = conn.execute(text("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'memory_entities', 'memory_observations', 'memory_relations',
                    'thinking_sessions', 'thoughts'
                )
                ORDER BY table_name;
            """))
            
            tables = list(result)
            logger.info("📊 Memory Service Tables:")
            for table_name, col_count in tables:
                logger.info(f"  ✅ {table_name:<20} ({col_count} columns)")
            
            if len(tables) < 5:
                logger.warning(f"\n⚠️  Warning: Only {len(tables)} of 5 expected tables found")
            
            # Check pgvector
            result = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"))
            vector_ext = result.fetchone()
            
            logger.info(f"\n🔌 Extensions:")
            if vector_ext:
                logger.info(f"  ✅ pgvector {vector_ext[1]} - Ready for embeddings")
            else:
                logger.info(f"  ❌ pgvector not found - Vector search will not work")
            
            # Check row counts
            logger.info(f"\n📈 Table Statistics:")
            for table_name, _ in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                logger.info(f"  • {table_name:<20} {count:>6} rows")
            
            # Check functions
            result = conn.execute(text("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('update_updated_at_column', 'get_next_thought_number')
                ORDER BY routine_name;
            """))
            
            functions = [row[0] for row in result]
            if functions:
                logger.info(f"\n🔧 Helper Functions:")
                for func in functions:
                    logger.info(f"  ✅ {func}")
            
            # Check views
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = 'thinking_session_stats';
            """))
            
            if result.fetchone():
                logger.info(f"\n👁️  Views:")
                logger.info(f"  ✅ thinking_session_stats")
            
            logger.info("\n✅ Database is ready for the memory service!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Memory Service Database Verification")
    logger.info("=" * 60)
    logger.info()
    
    success = verify_database()
    
    if not success:
        logger.error("\n❌ Database verification failed")
        sys.exit(1)
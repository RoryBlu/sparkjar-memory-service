#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Create or recreate the database schema for the memory and thinking services.
This script will DROP existing tables and create fresh ones.
"""
import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path for imports

# Set up logging
from sparkjar_crew.shared.utils.logging_config import setup_script_logging
logger = setup_script_logging("memory_schema_creator")

def get_database_url():
    """Get the database URL from environment variables."""
    # Try different possible env var names
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        db_url = os.getenv('DATABASE_URL_DIRECT')
    if not db_url:
        db_url = os.getenv('SUPABASE_DB_URL')
    
    if not db_url:
        raise ValueError(
            "No database URL found. Please set one of: "
            "DATABASE_URL, DATABASE_URL_DIRECT, or SUPABASE_DB_URL"
        )
    
    # Convert to sync URL if needed (remove +asyncpg)
    if '+asyncpg' in db_url:
        db_url = db_url.replace('+asyncpg', '')
    
    return db_url

def create_schema():
    """Create the database schema by executing the SQL files."""
    logger.info("Starting database schema creation...")
    
    # Get database URL
    try:
        db_url = get_database_url()
        logger.info("Found database URL")
    except ValueError as e:
        logger.error(f"Error: {e}")
        return False
    
    # Use the fixed SQL file
    sql_file = Path(__file__).parent / 'sql' / 'create_memory_schema_fixed.sql'
    functions_file = Path(__file__).parent / 'sql' / 'create_functions_and_views.sql'
    
    if not sql_file.exists():
        logger.error(f"SQL file not found: {sql_file}")
        return False
    
    # Create engine
    try:
        logger.info("Connecting to database...")
        engine = create_engine(db_url)
        
        # First, execute the main schema
        logger.info(f"Creating tables from: {sql_file}")
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        with engine.begin() as conn:
            # Execute the entire SQL file as one transaction
            logger.warning("Dropping existing tables if they exist...")
            logger.info("Creating new tables...")
            
            try:
                conn.execute(text(sql_content))
                logger.info("All tables created successfully!")
            except SQLAlchemyError as e:
                logger.error(f"Error creating tables: {e}")
                return False
            
            # Verify tables were created
            logger.info("Verifying created tables...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'memory_entities', 'memory_observations', 'memory_relations',
                    'thinking_sessions', 'thoughts'
                )
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")
            
            if len(tables) != 5:
                logger.warning(f"Expected 5 tables but found {len(tables)}")
                missing = set(['memory_entities', 'memory_observations', 'memory_relations', 
                             'thinking_sessions', 'thoughts']) - set(tables)
                if missing:
                    logger.error(f"Missing tables: {', '.join(missing)}")
                return False
            else:
                logger.info("All 5 tables verified!")
        
        # Now create functions and views
        if functions_file.exists():
            logger.info(f"Creating functions and views from: {functions_file}")
            with open(functions_file, 'r') as f:
                functions_content = f.read()
            
            with engine.begin() as conn:
                try:
                    conn.execute(text(functions_content))
                    logger.info("Functions and views created successfully!")
                except SQLAlchemyError as e:
                    logger.warning(f"Warning creating functions/views: {e}")
                    logger.info("(This is not critical - tables are ready)")
        
        # Final verification
        with engine.connect() as conn:
            # Check for pgvector extension
            result = conn.execute(text("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector';
            """))
            
            vector_ext = result.fetchone()
            if vector_ext:
                logger.info(f"pgvector extension enabled (version {vector_ext[1]})")
            else:
                logger.warning("pgvector extension not found. Vector search may not work.")
                
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    """Main entry point."""
    # Keep interactive elements as print statements for user interaction
    logger.info("=" * 60)
    logger.info("Memory Service Database Schema Creator")
    logger.info("=" * 60)
    logger.warning("\n⚠️  WARNING: This will DROP and recreate all memory tables!")
    logger.info("Any existing data will be lost.\n")
    
    logger.warning("Starting interactive schema creation process")
    
    # Confirm with user
    response = input("Do you want to continue? (yes/no): ").lower().strip()
    if response != 'yes':
        logger.info("\n❌ Schema creation cancelled.")
        logger.info("Schema creation cancelled by user")
        return
    
    logger.info("User confirmed schema creation - proceeding")
    
    # Create schema
    success = create_schema()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ DATABASE READY FOR DEPLOYMENT!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Deploy the memory service to Railway")
        logger.info("2. Set the DATABASE_URL environment variable")
        logger.info("3. Start capturing and retrieving memories!")
        logger.info("Database schema creation completed successfully")
    else:
        logger.error("\n❌ Schema creation failed. Please check the errors above.")
        logger.error("Schema creation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
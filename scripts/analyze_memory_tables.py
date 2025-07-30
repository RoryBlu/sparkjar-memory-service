# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Analyze memory tables in the database:
1. Check current constraints on memory_entities, memory_relations, and memory_observations
2. Count records by actor_type to understand data distribution
3. Look for any existing migration scripts or SQL files
4. Check if there are any existing indexes on actor_id or actor_type columns
5. Find any records with actor_type='system' that would need migration
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL_DIRECT")
if not DATABASE_URL:
    logger.error("Error: DATABASE_URL_DIRECT environment variable not set")
    sys.exit(1)

# Convert asyncpg URL to psycopg2 format
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def get_db_connection():
    """Create a direct database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def analyze_constraints(conn):
    """Analyze constraints on memory tables"""
    logger.info("\n=== TABLE CONSTRAINTS ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        logger.info(f"\n{table.upper()} Constraints:")
        logger.info("-" * 80)
        
        # Get all constraints
        query = """
        SELECT 
            con.conname AS constraint_name,
            con.contype AS constraint_type,
            pg_get_constraintdef(con.oid) AS definition
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        WHERE rel.relname = %s
        AND nsp.nspname = 'public'
        ORDER BY con.contype, con.conname;
        """
        
        with conn.cursor() as cur:
            cur.execute(query, (table,))
            constraints = cur.fetchall()
            
            if constraints:
                for constraint in constraints:
                    constraint_type = {
                        'p': 'PRIMARY KEY',
                        'f': 'FOREIGN KEY',
                        'u': 'UNIQUE',
                        'c': 'CHECK'
                    }.get(constraint['constraint_type'], constraint['constraint_type'])
                    
                    logger.info(f"\n  {constraint['constraint_name']} ({constraint_type}):")
                    logger.info(f"    {constraint['definition']}")
            else:
                logger.info("  No constraints found")

def analyze_indexes(conn):
    """Analyze indexes on memory tables"""
    logger.info("\n\n=== TABLE INDEXES ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        logger.info(f"\n{table.upper()} Indexes:")
        logger.info("-" * 80)
        
        query = """
        SELECT 
            i.relname AS index_name,
            pg_get_indexdef(i.oid) AS index_definition,
            idx.indisunique AS is_unique,
            idx.indisprimary AS is_primary
        FROM pg_index idx
        JOIN pg_class i ON i.oid = idx.indexrelid
        JOIN pg_class t ON t.oid = idx.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relname = %s
        AND n.nspname = 'public'
        ORDER BY i.relname;
        """
        
        with conn.cursor() as cur:
            cur.execute(query, (table,))
            indexes = cur.fetchall()
            
            if indexes:
                for index in indexes:
                    logger.info(f"\n  {index['index_name']}:")
                    logger.info(f"    {index['index_definition']}")
                    if index['is_unique']:
                        logger.info(f"    (UNIQUE)")
                    if index['is_primary']:
                        logger.info(f"    (PRIMARY KEY)")
            else:
                logger.info("  No indexes found")

def count_records_by_actor_type(conn):
    """Count records by actor_type in each table"""
    logger.info("\n\n=== RECORD COUNTS BY ACTOR_TYPE ===\n")
    
    # Check memory_entities
    logger.info("\nmemory_entities by actor_type:")
    logger.info("-" * 50)
    query = """
    SELECT 
        actor_type,
        COUNT(*) as count,
        COUNT(DISTINCT client_id) as unique_clients,
        COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
        COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_count
    FROM memory_entities
    GROUP BY actor_type
    ORDER BY count DESC;
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            headers = ['Actor Type', 'Total Count', 'Unique Clients', 'Active', 'Deleted']
            rows = [[r['actor_type'], r['count'], r['unique_clients'], r['active_count'], r['deleted_count']] for r in results]
            logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            logger.info("  No records found in memory_entities")
    
    # Check memory_relations
    logger.info("\n\nmemory_relations by actor_type:")
    logger.info("-" * 50)
    query = """
    SELECT 
        actor_type,
        COUNT(*) as count,
        COUNT(DISTINCT client_id) as unique_clients,
        COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count,
        COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_count
    FROM memory_relations
    GROUP BY actor_type
    ORDER BY count DESC;
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            headers = ['Actor Type', 'Total Count', 'Unique Clients', 'Active', 'Deleted']
            rows = [[r['actor_type'], r['count'], r['unique_clients'], r['active_count'], r['deleted_count']] for r in results]
            logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            logger.info("  No records found in memory_relations")

def find_system_actor_records(conn):
    """Find records with actor_type='system'"""
    logger.info("\n\n=== SYSTEM ACTOR RECORDS ===\n")
    
    # Check memory_entities
    logger.info("\nSample memory_entities with actor_type='system':")
    logger.info("-" * 80)
    query = """
    SELECT 
        id,
        client_id,
        actor_id,
        entity_name,
        entity_type,
        created_at,
        deleted_at
    FROM memory_entities
    WHERE actor_type = 'system'
    ORDER BY created_at DESC
    LIMIT 10;
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            headers = ['ID', 'Client ID', 'Actor ID', 'Entity Name', 'Entity Type', 'Created At', 'Deleted At']
            rows = [[r['id'], r['client_id'], r['actor_id'], r['entity_name'][:30], r['entity_type'], 
                    r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] else None,
                    r['deleted_at'].strftime('%Y-%m-%d %H:%M:%S') if r['deleted_at'] else None] for r in results]
            logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
            
            # Get total count
            cur.execute("SELECT COUNT(*) as count FROM memory_entities WHERE actor_type = 'system'")
            total = cur.fetchone()
            logger.info(f"\nTotal system actor records in memory_entities: {total['count']}")
        else:
            logger.info("  No system actor records found in memory_entities")
    
    # Check memory_relations
    logger.info("\n\nSample memory_relations with actor_type='system':")
    logger.info("-" * 80)
    query = """
    SELECT 
        r.id,
        r.client_id,
        r.actor_id,
        r.relation_type,
        e1.entity_name as from_entity,
        e2.entity_name as to_entity,
        r.created_at
    FROM memory_relations r
    JOIN memory_entities e1 ON e1.id = r.from_entity_id
    JOIN memory_entities e2 ON e2.id = r.to_entity_id
    WHERE r.actor_type = 'system'
    ORDER BY r.created_at DESC
    LIMIT 10;
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        if results:
            headers = ['ID', 'Client ID', 'Actor ID', 'Relation Type', 'From Entity', 'To Entity', 'Created At']
            rows = [[r['id'], r['client_id'], r['actor_id'], r['relation_type'], 
                    r['from_entity'][:20], r['to_entity'][:20],
                    r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] else None] for r in results]
            logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
            
            # Get total count
            cur.execute("SELECT COUNT(*) as count FROM memory_relations WHERE actor_type = 'system'")
            total = cur.fetchone()
            logger.info(f"\nTotal system actor records in memory_relations: {total['count']}")
        else:
            logger.info("  No system actor records found in memory_relations")

def check_column_existence(conn):
    """Check if actor_type and actor_id columns exist"""
    logger.info("\n\n=== COLUMN EXISTENCE CHECK ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        logger.info(f"\n{table} columns:")
        logger.info("-" * 50)
        
        query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        AND column_name IN ('actor_type', 'actor_id')
        ORDER BY ordinal_position;
        """
        
        with conn.cursor() as cur:
            cur.execute(query, (table,))
            columns = cur.fetchall()
            
            if columns:
                for col in columns:
                    logger.info(f"  {col['column_name']}: {col['data_type']}", end="")
                    if col['character_maximum_length']:
                        logger.info(f"({col['character_maximum_length']})", end="")
                    logger.info(f" - nullable: {col['is_nullable']}", end="")
                    if col['column_default']:
                        logger.info(f" - default: {col['column_default']}", end="")
                    logger.info()
            else:
                logger.info("  No actor_type or actor_id columns found")

def main():
    """Main function"""
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        # Check column existence first
        check_column_existence(conn)
        
        # Analyze constraints
        analyze_constraints(conn)
        
        # Analyze indexes
        analyze_indexes(conn)
        
        # Count records by actor_type
        count_records_by_actor_type(conn)
        
        # Find system actor records
        find_system_actor_records(conn)
        
        conn.close()
        logger.info("\n\nAnalysis complete!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
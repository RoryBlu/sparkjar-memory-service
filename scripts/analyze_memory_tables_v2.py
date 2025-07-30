# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3

import logging
logger = logging.getLogger(__name__)

"""
Analyze memory tables in the database - V2 with proper column detection
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

def get_table_columns(conn, table_name):
    """Get all columns for a table"""
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
    ORDER BY ordinal_position;
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (table_name,))
        return cur.fetchall()

def analyze_table_structure(conn):
    """Analyze the structure of memory tables"""
    logger.info("\n=== TABLE STRUCTURE ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        logger.info(f"\n{table.upper()} Structure:")
        logger.info("-" * 80)
        
        columns = get_table_columns(conn, table)
        
        if columns:
            headers = ['Column', 'Type', 'Nullable', 'Default']
            rows = []
            for col in columns:
                col_type = col['data_type']
                if col['character_maximum_length']:
                    col_type += f"({col['character_maximum_length']})"
                rows.append([
                    col['column_name'],
                    col_type,
                    col['is_nullable'],
                    col['column_default'][:30] if col['column_default'] else None
                ])
            logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            logger.info("  Table not found")

def analyze_constraints(conn):
    """Analyze constraints on memory tables"""
    logger.info("\n\n=== TABLE CONSTRAINTS ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        logger.info(f"\n{table.upper()} Constraints:")
        logger.info("-" * 80)
        
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

def count_records_by_actor_type(conn):
    """Count records by actor_type where applicable"""
    logger.info("\n\n=== RECORD COUNTS BY ACTOR_TYPE ===\n")
    
    # First check which tables have actor_type column
    tables_with_actor_type = []
    
    for table in ['memory_entities', 'memory_relations', 'memory_observations']:
        columns = get_table_columns(conn, table)
        if any(col['column_name'] == 'actor_type' for col in columns):
            tables_with_actor_type.append(table)
    
    for table in tables_with_actor_type:
        logger.info(f"\n{table} by actor_type:")
        logger.info("-" * 50)
        
        # Build dynamic query based on available columns
        columns = get_table_columns(conn, table)
        column_names = [col['column_name'] for col in columns]
        
        select_parts = ['actor_type', 'COUNT(*) as count']
        
        if 'client_id' in column_names:
            select_parts.append('COUNT(DISTINCT client_id) as unique_clients')
        
        if 'deleted_at' in column_names:
            select_parts.append('COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_count')
            select_parts.append('COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_count')
        
        query = f"""
        SELECT {', '.join(select_parts)}
        FROM {table}
        GROUP BY actor_type
        ORDER BY count DESC;
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if results:
                headers = ['Actor Type', 'Total Count']
                rows = []
                
                for r in results:
                    row = [r['actor_type'], r['count']]
                    if 'unique_clients' in r:
                        headers.append('Unique Clients') if 'Unique Clients' not in headers else None
                        row.append(r['unique_clients'])
                    if 'active_count' in r:
                        headers.extend(['Active', 'Deleted']) if 'Active' not in headers else None
                        row.extend([r['active_count'], r['deleted_count']])
                    rows.append(row)
                
                logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
            else:
                logger.info("  No records found")

def find_system_actor_records(conn):
    """Find records with actor_type='system'"""
    logger.info("\n\n=== SYSTEM ACTOR RECORDS ===\n")
    
    # Check memory_entities if it has actor_type
    columns = get_table_columns(conn, 'memory_entities')
    column_names = [col['column_name'] for col in columns]
    
    if 'actor_type' in column_names:
        logger.info("\nChecking for actor_type='system' in memory_entities:")
        logger.info("-" * 80)
        
        # First check if 'system' is a valid value
        query = """
        SELECT DISTINCT actor_type 
        FROM memory_entities 
        ORDER BY actor_type;
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            actor_types = [r['actor_type'] for r in cur.fetchall()]
            logger.info(f"Valid actor_types in memory_entities: {', '.join(actor_types)}")
            
            if 'system' in actor_types:
                # Get count of system records
                cur.execute("SELECT COUNT(*) as count FROM memory_entities WHERE actor_type = 'system'")
                result = cur.fetchone()
                logger.info(f"\nTotal records with actor_type='system': {result['count']}")
                
                # Show sample records
                if result['count'] > 0:
                    logger.info("\nSample records:")
                    query = """
                    SELECT id, actor_id, entity_name, entity_type, created_at
                    FROM memory_entities
                    WHERE actor_type = 'system'
                    ORDER BY created_at DESC
                    LIMIT 5;
                    """
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    headers = ['ID', 'Actor ID', 'Entity Name', 'Entity Type', 'Created At']
                    rows = [[r['id'], r['actor_id'], r['entity_name'][:30], r['entity_type'], 
                            r['created_at'].strftime('%Y-%m-%d %H:%M:%S')] for r in results]
                    logger.info(tabulate(rows, headers=headers, tablefmt='grid'))
            else:
                logger.info("\nNo records with actor_type='system' found")

def check_indexes(conn):
    """Check indexes on actor_type and actor_id columns"""
    logger.info("\n\n=== INDEXES ON ACTOR COLUMNS ===\n")
    
    tables = ['memory_entities', 'memory_relations', 'memory_observations']
    
    for table in tables:
        # Check if table has these columns
        columns = get_table_columns(conn, table)
        column_names = [col['column_name'] for col in columns]
        
        if 'actor_type' in column_names or 'actor_id' in column_names:
            logger.info(f"\n{table} indexes on actor columns:")
            logger.info("-" * 50)
            
            query = """
            SELECT 
                i.relname AS index_name,
                pg_get_indexdef(i.oid) AS index_definition
            FROM pg_index idx
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_class t ON t.oid = idx.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE t.relname = %s
            AND n.nspname = 'public'
            AND (
                pg_get_indexdef(i.oid) LIKE '%%actor_type%%'
                OR pg_get_indexdef(i.oid) LIKE '%%actor_id%%'
            )
            ORDER BY i.relname;
            """
            
            with conn.cursor() as cur:
                cur.execute(query, (table,))
                indexes = cur.fetchall()
                
                if indexes:
                    for index in indexes:
                        logger.info(f"  {index['index_name']}:")
                        logger.info(f"    {index['index_definition']}")
                else:
                    logger.info("  No indexes found on actor_type or actor_id columns")

def find_migration_scripts():
    """Find migration scripts in the codebase"""
    logger.info("\n\n=== MIGRATION SCRIPTS ===\n")
    
    # Search for SQL files related to memory tables
    logger.info("SQL files related to memory tables:")
    logger.info("-" * 50)
    
    import subprocess
    result = subprocess.run(
        ["find", ".", "-name", "*.sql", "-type", "f", "-exec", "grep", "-l", "memory_", "{}", ";"],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        files = result.stdout.strip().split('\n')
        for file in sorted(files):
            if not file.startswith('./.venv') and not file.startswith('./venv'):
                logger.info(f"  {file}")
    else:
        logger.info("  No SQL files found containing 'memory_'")

def main():
    """Main function"""
    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        
        # Analyze table structure
        analyze_table_structure(conn)
        
        # Analyze constraints
        analyze_constraints(conn)
        
        # Count records by actor_type
        count_records_by_actor_type(conn)
        
        # Check indexes on actor columns
        check_indexes(conn)
        
        # Find system actor records
        find_system_actor_records(conn)
        
        # Find migration scripts
        find_migration_scripts()
        
        conn.close()
        logger.info("\n\nAnalysis complete!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
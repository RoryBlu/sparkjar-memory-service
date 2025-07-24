"""Schema inspector to discover actual memory table structure."""

import asyncio
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .base import BaseValidator, ValidationResult, ValidationStatus

class SchemaInspector(BaseValidator):
    """Inspect and document actual memory table schemas."""
    
    def __init__(self, database_url: Optional[str] = None):
        super().__init__("SchemaInspector")
        self.database_url = database_url
        self.discovered_schemas = {}
    
    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if not self.database_url:
            raise Exception("Database URL not configured")
        
        engine = create_async_engine(self.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return async_session()
    
    async def inspect_table_schema(self, table_name: str) -> Dict:
        """Inspect a specific table's schema."""
        async with await self._get_session() as session:
            # Get column information
            result = await session.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """), {"table_name": table_name})
            
            columns = []
            for row in result.fetchall():
                columns.append({
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                    "default": row.column_default,
                    "max_length": row.character_maximum_length,
                    "precision": row.numeric_precision,
                    "scale": row.numeric_scale
                })
            
            # Get indexes
            result = await session.execute(text("""
                SELECT 
                    i.relname as index_name,
                    a.attname as column_name,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = :table_name
                ORDER BY i.relname, a.attname
            """), {"table_name": table_name})
            
            indexes = {}
            for row in result.fetchall():
                if row.index_name not in indexes:
                    indexes[row.index_name] = {
                        "columns": [],
                        "unique": row.is_unique,
                        "primary": row.is_primary
                    }
                indexes[row.index_name]["columns"].append(row.column_name)
            
            # Get foreign keys
            result = await session.execute(text("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name = :table_name
            """), {"table_name": table_name})
            
            foreign_keys = []
            for row in result.fetchall():
                foreign_keys.append({
                    "constraint_name": row.constraint_name,
                    "column": row.column_name,
                    "references_table": row.foreign_table_name,
                    "references_column": row.foreign_column_name
                })
            
            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            }
    
    async def discover_memory_tables(self) -> List[str]:
        """Discover all memory-related tables."""
        async with await self._get_session() as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND (table_name LIKE '%memory%' OR table_name LIKE '%object%')
                ORDER BY table_name
            """))
            
            return [row.table_name for row in result.fetchall()]
    
    async def inspect_all_memory_tables(self):
        """Inspect all memory-related tables."""
        tables = await self.discover_memory_tables()
        
        self.logger.info(f"Discovered memory tables: {tables}")
        
        for table_name in tables:
            try:
                schema = await self.inspect_table_schema(table_name)
                self.discovered_schemas[table_name] = schema
                
                self.logger.info(f"Table {table_name}:")
                self.logger.info(f"  Columns: {len(schema['columns'])}")
                for col in schema['columns']:
                    self.logger.info(f"    - {col['name']}: {col['type']} {'NULL' if col['nullable'] else 'NOT NULL'}")
                
                if schema['indexes']:
                    self.logger.info(f"  Indexes: {len(schema['indexes'])}")
                    for idx_name, idx_info in schema['indexes'].items():
                        idx_type = "PRIMARY" if idx_info['primary'] else "UNIQUE" if idx_info['unique'] else "INDEX"
                        self.logger.info(f"    - {idx_name} ({idx_type}): {', '.join(idx_info['columns'])}")
                
                if schema['foreign_keys']:
                    self.logger.info(f"  Foreign Keys: {len(schema['foreign_keys'])}")
                    for fk in schema['foreign_keys']:
                        self.logger.info(f"    - {fk['column']} -> {fk['references_table']}.{fk['references_column']}")
                
            except Exception as e:
                self.logger.error(f"Failed to inspect table {table_name}: {e}")
    
    async def test_schema_discovery(self):
        """Test schema discovery functionality."""
        await self.inspect_all_memory_tables()
        
        # Verify we found the expected tables
        expected_tables = ["memory_entities", "memory_relations", "object_schemas"]
        found_tables = list(self.discovered_schemas.keys())
        
        for expected in expected_tables:
            assert expected in found_tables, f"Expected table {expected} not found. Found: {found_tables}"
        
        # Verify memory_entities has basic required columns
        if "memory_entities" in self.discovered_schemas:
            entity_columns = [col["name"] for col in self.discovered_schemas["memory_entities"]["columns"]]
            required_columns = ["id", "entity_name", "actor_id", "actor_type"]  # Actual schema requirements
            
            for req_col in required_columns:
                assert req_col in entity_columns, f"Required column {req_col} not found in memory_entities"
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run schema inspection validation."""
        if not self.database_url:
            return [ValidationResult(
                test_name="schema_discovery",
                status=ValidationStatus.FAILED,
                execution_time_ms=0.0,
                error_message="Database URL not configured"
            )]
        
        result = await self.run_test("schema_discovery", self.test_schema_discovery)
        return [result]
    
    def get_discovered_schema(self, table_name: str) -> Optional[Dict]:
        """Get discovered schema for a specific table."""
        return self.discovered_schemas.get(table_name)
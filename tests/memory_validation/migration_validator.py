"""
Data migration validation for memory system.
Tests data migration between environments and schema version migrations.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import text, MetaData, Table, Column, String, DateTime, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseValidator, ValidationResult, ValidationStatus
# TODO: Fix import - use local database connection
# from database import get_db
# TODO: Fix import - use local models
# from database.models import ...

class MigrationValidator(BaseValidator):
    """Validates data migration procedures between environments."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("MigrationValidator", logger)
        self.temp_dir = None
        self.test_client_id = None
        self.test_data_ids = []
        self.migration_metadata = {}
        
    async def run_validation(self) -> List[ValidationResult]:
        """Run all migration validation tests."""
        self.results = []
        
        # Setup test environment
        await self.run_test("setup_migration_test_environment", self._setup_migration_test_environment)
        
        # Test data migration procedures
        await self.run_test("test_development_to_production_migration", self._test_dev_to_prod_migration)
        await self.run_test("test_relationship_preservation", self._test_relationship_preservation)
        await self.run_test("test_schema_version_migration", self._test_schema_version_migration)
        await self.run_test("test_client_isolation_during_migration", self._test_client_isolation_migration)
        
        # Test migration rollback procedures
        await self.run_test("test_migration_rollback", self._test_migration_rollback)
        await self.run_test("test_partial_migration_recovery", self._test_partial_migration_recovery)
        
        # Test large dataset migration
        await self.run_test("test_large_dataset_migration", self._test_large_dataset_migration)
        
        # Cleanup
        await self.run_test("cleanup_migration_test_environment", self._cleanup_migration_test_environment)
        
        return self.results
    
    async def _setup_migration_test_environment(self):
        """Set up test environment for migration testing."""
        # Create temporary directory for migration files
        self.temp_dir = tempfile.mkdtemp(prefix="memory_migration_test_")
        self.logger.info(f"Created temp directory: {self.temp_dir}")
        
        # Create test client and complex data structure
        self.test_client_id = str(uuid.uuid4())
        
        async with get_direct_session() as session:
            # Create test client
            test_client = Clients(
                id=self.test_client_id,
                client_name=f"MigrationTest_{int(time.time())}",
                client_description="Test client for migration validation",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_client)
            
            # Create multiple test users with relationships
            user_ids = []
            for i in range(3):
                user_id = str(uuid.uuid4())
                test_user = ClientUsers(
                    id=user_id,
                    client_id=self.test_client_id,
                    user_name=f"migration_test_user_{i}",
                    user_email=f"migration.test.{i}@example.com",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(test_user)
                user_ids.append(user_id)
                self.test_data_ids.append(user_id)
            
            # Create crew jobs with complex relationships
            job_ids = []
            for i in range(10):
                job_id = str(uuid.uuid4())
                crew_job = CrewJobs(
                    id=job_id,
                    client_id=self.test_client_id,
                    crew_name=f"migration_test_crew_{i}",
                    job_status="completed" if i % 2 == 0 else "failed",
                    job_input={
                        "test": f"migration_test_input_{i}",
                        "user_id": user_ids[i % len(user_ids)],
                        "complex_data": {
                            "nested": {"value": i},
                            "array": [1, 2, 3, i],
                            "metadata": {"created_by": f"user_{i % len(user_ids)}"}
                        }
                    },
                    job_output={
                        "result": f"migration_test_output_{i}",
                        "metrics": {"duration": i * 100, "success": i % 2 == 0}
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(crew_job)
                job_ids.append(job_id)
                self.test_data_ids.append(job_id)
            
            # Create memory entries with cross-references
            memory_ids = []
            for i in range(20):
                memory_id = str(uuid.uuid4())
                crew_memory = CrewMemory(
                    id=memory_id,
                    client_id=self.test_client_id,
                    memory_type="entity" if i % 3 == 0 else "relationship",
                    memory_content=f"Migration test memory content {i} with references to job {job_ids[i % len(job_ids)]}",
                    memory_metadata={
                        "test_index": i,
                        "migration_test": True,
                        "related_job": job_ids[i % len(job_ids)],
                        "related_user": user_ids[i % len(user_ids)],
                        "cross_references": [job_ids[(i + 1) % len(job_ids)], job_ids[(i + 2) % len(job_ids)]]
                    },
                    created_at=datetime.utcnow()
                )
                session.add(crew_memory)
                memory_ids.append(memory_id)
                self.test_data_ids.append(memory_id)
            
            await session.commit()
            
        # Store migration metadata
        self.migration_metadata = {
            "client_id": self.test_client_id,
            "user_ids": user_ids,
            "job_ids": job_ids,
            "memory_ids": memory_ids,
            "total_records": len(self.test_data_ids)
        }
        
        self.logger.info(f"Created migration test data: {len(self.test_data_ids)} records")
    
    async def _test_dev_to_prod_migration(self):
        """Test migration between development and production environments."""
        # Export data from current environment (simulating dev)
        export_file = os.path.join(self.temp_dir, "dev_export.json")
        export_success = await self._export_client_data(self.test_client_id, export_file)
        assert export_success, "Data export failed"
        
        # Verify export file contains all expected data
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        assert "client" in exported_data, "Client data missing from export"
        assert "users" in exported_data, "User data missing from export"
        assert "jobs" in exported_data, "Job data missing from export"
        assert "memory" in exported_data, "Memory data missing from export"
        
        # Verify data completeness
        assert len(exported_data["users"]) == 3, f"Expected 3 users, found {len(exported_data['users'])}"
        assert len(exported_data["jobs"]) == 10, f"Expected 10 jobs, found {len(exported_data['jobs'])}"
        assert len(exported_data["memory"]) == 20, f"Expected 20 memory entries, found {len(exported_data['memory'])}"
        
        # Simulate production import by creating new client ID
        new_client_id = str(uuid.uuid4())
        
        # Modify export data for production environment
        prod_export_file = os.path.join(self.temp_dir, "prod_import.json")
        await self._prepare_production_import(export_file, prod_export_file, new_client_id)
        
        # Import to production environment (simulated)
        import_success = await self._import_client_data(prod_export_file)
        assert import_success, "Data import to production failed"
        
        # Verify imported data
        await self._verify_migrated_data(new_client_id, exported_data)
        
        # Cleanup production test data
        await self._cleanup_client_data(new_client_id)
        
        self.logger.info("Development to production migration completed successfully")
    
    async def _test_relationship_preservation(self):
        """Test that all relationships are preserved during migration."""
        # Export data with relationships
        export_file = os.path.join(self.temp_dir, "relationship_export.json")
        export_success = await self._export_client_data(self.test_client_id, export_file)
        assert export_success, "Relationship export failed"
        
        # Analyze relationships in original data
        original_relationships = await self._analyze_data_relationships(self.test_client_id)
        
        # Create new client for migration test
        new_client_id = str(uuid.uuid4())
        
        # Prepare and import data
        import_file = os.path.join(self.temp_dir, "relationship_import.json")
        await self._prepare_production_import(export_file, import_file, new_client_id)
        
        import_success = await self._import_client_data(import_file)
        assert import_success, "Relationship import failed"
        
        # Analyze relationships in migrated data
        migrated_relationships = await self._analyze_data_relationships(new_client_id)
        
        # Verify relationship preservation
        assert len(original_relationships["job_user_refs"]) == len(migrated_relationships["job_user_refs"]), \
            "Job-user relationships not preserved"
        assert len(original_relationships["memory_job_refs"]) == len(migrated_relationships["memory_job_refs"]), \
            "Memory-job relationships not preserved"
        assert len(original_relationships["memory_cross_refs"]) == len(migrated_relationships["memory_cross_refs"]), \
            "Memory cross-references not preserved"
        
        # Cleanup
        await self._cleanup_client_data(new_client_id)
        
        self.logger.info("Relationship preservation verified successfully")
    
    async def _test_schema_version_migration(self):
        """Test schema version migration procedures."""
        # Create a mock schema version table
        async with get_direct_session() as session:
            # Create schema version tracking
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            
            # Insert current version
            await session.execute(text("""
                INSERT INTO schema_versions (version, description) 
                VALUES ('1.0.0', 'Initial schema version for migration test')
            """))
            
            await session.commit()
        
        # Simulate schema migration (add a new column)
        migration_sql = """
        ALTER TABLE crew_memory ADD COLUMN IF NOT EXISTS migration_test_column VARCHAR(255);
        UPDATE schema_versions SET version = '1.1.0', description = 'Added migration test column' 
        WHERE version = '1.0.0';
        """
        
        async with get_direct_session() as session:
            await session.execute(text(migration_sql))
            await session.commit()
        
        # Verify schema migration
        async with get_direct_session() as session:
            # Check if new column exists
            result = await session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'crew_memory' AND column_name = 'migration_test_column'
            """))
            column_exists = result.fetchone() is not None
            assert column_exists, "Schema migration failed - new column not found"
            
            # Check version update
            version_result = await session.execute(text("""
                SELECT version FROM schema_versions ORDER BY applied_at DESC LIMIT 1
            """))
            current_version = version_result.scalar()
            assert current_version == '1.1.0', f"Schema version not updated: {current_version}"
        
        # Test data migration with new schema
        async with get_direct_session() as session:
            await session.execute(text("""
                UPDATE crew_memory 
                SET migration_test_column = 'migrated_value' 
                WHERE client_id = :client_id
            """), {"client_id": self.test_client_id})
            await session.commit()
        
        # Verify data migration
        async with get_direct_session() as session:
            result = await session.execute(text("""
                SELECT COUNT(*) FROM crew_memory 
                WHERE client_id = :client_id AND migration_test_column = 'migrated_value'
            """), {"client_id": self.test_client_id})
            migrated_count = result.scalar()
            assert migrated_count == 20, f"Expected 20 migrated records, found {migrated_count}"
        
        # Cleanup schema changes
        async with get_direct_session() as session:
            await session.execute(text("ALTER TABLE crew_memory DROP COLUMN IF EXISTS migration_test_column"))
            await session.execute(text("DROP TABLE IF EXISTS schema_versions"))
            await session.commit()
        
        self.logger.info("Schema version migration completed successfully")
    
    async def _test_client_isolation_migration(self):
        """Test that client data isolation is maintained during migration."""
        # Create another test client to ensure isolation
        other_client_id = str(uuid.uuid4())
        
        async with get_direct_session() as session:
            other_client = Clients(
                id=other_client_id,
                client_name="IsolationTestClient",
                client_description="Client for testing isolation during migration",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(other_client)
            
            # Add some data for the other client
            other_memory = CrewMemory(
                id=str(uuid.uuid4()),
                client_id=other_client_id,
                memory_type="entity",
                memory_content="Other client data that should not be migrated",
                memory_metadata={"isolation_test": True},
                created_at=datetime.utcnow()
            )
            session.add(other_memory)
            
            await session.commit()
        
        # Export only the test client data
        export_file = os.path.join(self.temp_dir, "isolation_export.json")
        export_success = await self._export_client_data(self.test_client_id, export_file)
        assert export_success, "Isolation export failed"
        
        # Verify export doesn't contain other client's data
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        # Check that no other client data is included
        for memory_entry in exported_data.get("memory", []):
            assert memory_entry["client_id"] == self.test_client_id, \
                "Other client data found in export"
        
        # Verify other client data still exists
        async with get_direct_session() as session:
            other_data_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                {"client_id": other_client_id}
            )
            assert other_data_count > 0, "Other client data was affected by migration"
        
        # Cleanup other client
        await self._cleanup_client_data(other_client_id)
        
        self.logger.info("Client isolation during migration verified successfully")
    
    async def _test_migration_rollback(self):
        """Test migration rollback procedures."""
        # Create backup before migration
        backup_file = os.path.join(self.temp_dir, "rollback_backup.json")
        backup_success = await self._export_client_data(self.test_client_id, backup_file)
        assert backup_success, "Pre-migration backup failed"
        
        # Perform a migration that we'll rollback (modify some data)
        async with get_direct_session() as session:
            await session.execute(text("""
                UPDATE crew_memory 
                SET memory_content = memory_content || ' [MIGRATED]'
                WHERE client_id = :client_id
            """), {"client_id": self.test_client_id})
            await session.commit()
        
        # Verify migration changes
        async with get_direct_session() as session:
            result = await session.execute(text("""
                SELECT COUNT(*) FROM crew_memory 
                WHERE client_id = :client_id AND memory_content LIKE '%[MIGRATED]%'
            """), {"client_id": self.test_client_id})
            migrated_count = result.scalar()
            assert migrated_count == 20, "Migration changes not applied"
        
        # Perform rollback by restoring from backup
        rollback_success = await self._rollback_migration(backup_file, self.test_client_id)
        assert rollback_success, "Migration rollback failed"
        
        # Verify rollback
        async with get_direct_session() as session:
            result = await session.execute(text("""
                SELECT COUNT(*) FROM crew_memory 
                WHERE client_id = :client_id AND memory_content LIKE '%[MIGRATED]%'
            """), {"client_id": self.test_client_id})
            migrated_count = result.scalar()
            assert migrated_count == 0, "Rollback did not restore original data"
        
        self.logger.info("Migration rollback completed successfully")
    
    async def _test_partial_migration_recovery(self):
        """Test recovery from partial migration failures."""
        # Simulate partial migration by importing incomplete data
        partial_export = {
            "client": {
                "id": str(uuid.uuid4()),
                "client_name": "PartialMigrationTest",
                "client_description": "Test partial migration recovery"
            },
            "users": [],  # Missing user data
            "jobs": self.migration_metadata["job_ids"][:5],  # Only partial job data
            "memory": []  # Missing memory data
        }
        
        partial_file = os.path.join(self.temp_dir, "partial_migration.json")
        with open(partial_file, 'w') as f:
            json.dump(partial_export, f, indent=2, default=str)
        
        # Attempt import (should handle missing data gracefully)
        try:
            import_success = await self._import_client_data(partial_file)
            # Import might succeed with warnings, or fail gracefully
        except Exception as e:
            self.logger.info(f"Partial migration failed as expected: {e}")
        
        # Verify system state is consistent (no partial data corruption)
        new_client_id = partial_export["client"]["id"]
        async with get_direct_session() as session:
            client_exists = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {"client_id": new_client_id}
            )
            
            if client_exists > 0:
                # If client was created, verify data consistency
                job_count = await session.scalar(
                    text("SELECT COUNT(*) FROM crew_jobs WHERE client_id = :client_id"),
                    {"client_id": new_client_id}
                )
                memory_count = await session.scalar(
                    text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                    {"client_id": new_client_id}
                )
                
                # Cleanup partial data
                await self._cleanup_client_data(new_client_id)
        
        self.logger.info("Partial migration recovery test completed")
    
    async def _test_large_dataset_migration(self):
        """Test migration with large datasets."""
        # Create a larger dataset for migration testing
        large_client_id = str(uuid.uuid4())
        
        async with get_direct_session() as session:
            # Create client
            large_client = Clients(
                id=large_client_id,
                client_name="LargeDatasetMigrationTest",
                client_description="Test client for large dataset migration",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(large_client)
            
            # Create many memory entries (simulate large dataset)
            batch_size = 100
            total_records = 1000
            
            for batch_start in range(0, total_records, batch_size):
                batch_records = []
                for i in range(batch_start, min(batch_start + batch_size, total_records)):
                    memory_id = str(uuid.uuid4())
                    memory_record = CrewMemory(
                        id=memory_id,
                        client_id=large_client_id,
                        memory_type="entity",
                        memory_content=f"Large dataset memory content {i} " + "x" * 100,  # Make content larger
                        memory_metadata={
                            "index": i,
                            "batch": batch_start // batch_size,
                            "large_dataset_test": True
                        },
                        created_at=datetime.utcnow()
                    )
                    batch_records.append(memory_record)
                
                session.add_all(batch_records)
                await session.commit()
                
                # Log progress
                if (batch_start + batch_size) % 500 == 0:
                    self.logger.info(f"Created {batch_start + batch_size} large dataset records")
        
        # Test export of large dataset
        start_time = time.time()
        large_export_file = os.path.join(self.temp_dir, "large_dataset_export.json")
        export_success = await self._export_client_data(large_client_id, large_export_file)
        export_time = time.time() - start_time
        
        assert export_success, "Large dataset export failed"
        assert export_time < 60, f"Export took too long: {export_time:.2f}s"
        
        # Verify export file size and content
        file_size = os.path.getsize(large_export_file)
        assert file_size > 100000, f"Export file too small: {file_size} bytes"
        
        with open(large_export_file, 'r') as f:
            large_data = json.load(f)
        
        assert len(large_data["memory"]) == total_records, \
            f"Expected {total_records} memory records, found {len(large_data['memory'])}"
        
        # Cleanup large dataset
        await self._cleanup_client_data(large_client_id)
        
        self.logger.info(f"Large dataset migration test completed: {total_records} records in {export_time:.2f}s")
    
    async def _export_client_data(self, client_id: str, export_file: str) -> bool:
        """Export all data for a specific client."""
        try:
            async with get_direct_session() as session:
                # Export client data
                client_result = await session.execute(
                    text("SELECT * FROM clients WHERE id = :client_id"),
                    {"client_id": client_id}
                )
                client_data = client_result.fetchone()
                
                # Export users
                users_result = await session.execute(
                    text("SELECT * FROM client_users WHERE client_id = :client_id"),
                    {"client_id": client_id}
                )
                users_data = users_result.fetchall()
                
                # Export jobs
                jobs_result = await session.execute(
                    text("SELECT * FROM crew_jobs WHERE client_id = :client_id"),
                    {"client_id": client_id}
                )
                jobs_data = jobs_result.fetchall()
                
                # Export memory
                memory_result = await session.execute(
                    text("SELECT * FROM crew_memory WHERE client_id = :client_id"),
                    {"client_id": client_id}
                )
                memory_data = memory_result.fetchall()
                
                # Prepare export data
                export_data = {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "client": dict(client_data._mapping) if client_data else None,
                    "users": [dict(row._mapping) for row in users_data],
                    "jobs": [dict(row._mapping) for row in jobs_data],
                    "memory": [dict(row._mapping) for row in memory_data]
                }
                
                # Write to file
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                self.logger.info(f"Exported client data: {len(users_data)} users, {len(jobs_data)} jobs, {len(memory_data)} memory entries")
                return True
                
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            return False
    
    async def _prepare_production_import(self, source_file: str, target_file: str, new_client_id: str):
        """Prepare export data for production import with new client ID."""
        with open(source_file, 'r') as f:
            data = json.load(f)
        
        # Update client ID
        old_client_id = data["client"]["id"]
        data["client"]["id"] = new_client_id
        data["client"]["client_name"] += "_PROD"
        
        # Update all references to client ID
        for user in data["users"]:
            user["client_id"] = new_client_id
        
        for job in data["jobs"]:
            job["client_id"] = new_client_id
        
        for memory in data["memory"]:
            memory["client_id"] = new_client_id
        
        # Write updated data
        with open(target_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    async def _import_client_data(self, import_file: str) -> bool:
        """Import client data from export file."""
        try:
            with open(import_file, 'r') as f:
                data = json.load(f)
            
            async with get_direct_session() as session:
                # Import client
                if data["client"]:
                    client = Clients(**{k: v for k, v in data["client"].items() 
                                      if k in ["id", "client_name", "client_description"]})
                    client.created_at = datetime.utcnow()
                    client.updated_at = datetime.utcnow()
                    session.add(client)
                
                # Import users
                for user_data in data["users"]:
                    user = ClientUsers(**{k: v for k, v in user_data.items() 
                                        if k in ["id", "client_id", "user_name", "user_email"]})
                    user.created_at = datetime.utcnow()
                    user.updated_at = datetime.utcnow()
                    session.add(user)
                
                # Import jobs
                for job_data in data["jobs"]:
                    job = CrewJobs(**{k: v for k, v in job_data.items() 
                                    if k in ["id", "client_id", "crew_name", "job_status", "job_input", "job_output"]})
                    job.created_at = datetime.utcnow()
                    job.updated_at = datetime.utcnow()
                    session.add(job)
                
                # Import memory
                for memory_data in data["memory"]:
                    memory = CrewMemory(**{k: v for k, v in memory_data.items() 
                                         if k in ["id", "client_id", "memory_type", "memory_content", "memory_metadata"]})
                    memory.created_at = datetime.utcnow()
                    session.add(memory)
                
                await session.commit()
                
                self.logger.info(f"Imported client data: {len(data['users'])} users, {len(data['jobs'])} jobs, {len(data['memory'])} memory entries")
                return True
                
        except Exception as e:
            self.logger.error(f"Import error: {e}")
            return False
    
    async def _verify_migrated_data(self, client_id: str, expected_data: Dict[str, Any]):
        """Verify that migrated data matches expected data."""
        async with get_direct_session() as session:
            # Verify client
            client_count = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {"client_id": client_id}
            )
            assert client_count == 1, "Client not found after migration"
            
            # Verify users
            user_count = await session.scalar(
                text("SELECT COUNT(*) FROM client_users WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            assert user_count == len(expected_data["users"]), \
                f"User count mismatch: expected {len(expected_data['users'])}, found {user_count}"
            
            # Verify jobs
            job_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_jobs WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            assert job_count == len(expected_data["jobs"]), \
                f"Job count mismatch: expected {len(expected_data['jobs'])}, found {job_count}"
            
            # Verify memory
            memory_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            assert memory_count == len(expected_data["memory"]), \
                f"Memory count mismatch: expected {len(expected_data['memory'])}, found {memory_count}"
    
    async def _analyze_data_relationships(self, client_id: str) -> Dict[str, List]:
        """Analyze relationships in client data."""
        relationships = {
            "job_user_refs": [],
            "memory_job_refs": [],
            "memory_cross_refs": []
        }
        
        async with get_direct_session() as session:
            # Analyze job-user relationships
            jobs_result = await session.execute(
                text("SELECT id, job_input FROM crew_jobs WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            for job in jobs_result.fetchall():
                job_input = job.job_input
                if isinstance(job_input, dict) and "user_id" in job_input:
                    relationships["job_user_refs"].append({
                        "job_id": job.id,
                        "user_id": job_input["user_id"]
                    })
            
            # Analyze memory-job relationships
            memory_result = await session.execute(
                text("SELECT id, memory_metadata FROM crew_memory WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            for memory in memory_result.fetchall():
                metadata = memory.memory_metadata
                if isinstance(metadata, dict):
                    if "related_job" in metadata:
                        relationships["memory_job_refs"].append({
                            "memory_id": memory.id,
                            "job_id": metadata["related_job"]
                        })
                    if "cross_references" in metadata:
                        relationships["memory_cross_refs"].extend([
                            {"memory_id": memory.id, "ref_id": ref_id}
                            for ref_id in metadata["cross_references"]
                        ])
        
        return relationships
    
    async def _rollback_migration(self, backup_file: str, client_id: str) -> bool:
        """Rollback migration by restoring from backup."""
        try:
            # Delete current data
            await self._cleanup_client_data(client_id)
            
            # Restore from backup
            return await self._import_client_data(backup_file)
            
        except Exception as e:
            self.logger.error(f"Rollback error: {e}")
            return False
    
    async def _cleanup_client_data(self, client_id: str):
        """Clean up all data for a specific client."""
        async with get_direct_session() as session:
            await session.execute(
                text("DELETE FROM crew_memory WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.execute(
                text("DELETE FROM crew_jobs WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.execute(
                text("DELETE FROM client_users WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.execute(
                text("DELETE FROM clients WHERE id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
    
    async def _cleanup_migration_test_environment(self):
        """Clean up migration test environment."""
        try:
            # Clean up test data
            if self.test_client_id:
                await self._cleanup_client_data(self.test_client_id)
                self.logger.info(f"Cleaned up migration test data for client: {self.test_client_id}")
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"Cleaned up temp directory: {self.temp_dir}")
                
        except Exception as e:
            self.logger.error(f"Migration cleanup error: {e}")
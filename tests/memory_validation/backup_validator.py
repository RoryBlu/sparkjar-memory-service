# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""
Backup and restore validation for memory system.
Tests database backup procedures, consistency, and restoration.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseValidator, ValidationResult, ValidationStatus
from sparkjar_shared.database.connection import get_direct_session
from sparkjar_shared.database.models import (
    Clients,
    ClientUsers,
    CrewJobs,
    CrewMemory,
)

class BackupValidator(BaseValidator):
    """Validates database backup and restore procedures."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("BackupValidator", logger)
        self.temp_dir = None
        self.test_client_id = None
        self.test_data_ids = []
        
    async def run_validation(self) -> List[ValidationResult]:
        """Run all backup validation tests."""
        self.results = []
        
        # Setup test environment
        await self.run_test("setup_test_environment", self._setup_test_environment)
        
        # Test backup procedures
        await self.run_test("test_database_backup_during_operations", self._test_backup_during_operations)
        await self.run_test("test_backup_data_consistency", self._test_backup_consistency)
        await self.run_test("test_backup_restoration", self._test_backup_restoration)
        await self.run_test("test_no_data_loss_during_backup", self._test_no_data_loss)
        
        # Test incremental backup scenarios
        await self.run_test("test_incremental_backup", self._test_incremental_backup)
        await self.run_test("test_backup_with_concurrent_writes", self._test_concurrent_backup)
        
        # Cleanup
        await self.run_test("cleanup_test_environment", self._cleanup_test_environment)
        
        return self.results
    
    async def _setup_test_environment(self):
        """Set up test environment with temporary directory and test data."""
        # Create temporary directory for backups
        self.temp_dir = tempfile.mkdtemp(prefix="memory_backup_test_")
        self.logger.info(f"Created temp directory: {self.temp_dir}")
        
        # Create test client and data
        self.test_client_id = str(uuid.uuid4())
        
        async with get_direct_session() as session:
            # Create test client
            test_client = Clients(
                id=self.test_client_id,
                client_name=f"BackupTest_{int(time.time())}",
                client_description="Test client for backup validation",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_client)
            
            # Create test user
            test_user_id = str(uuid.uuid4())
            test_user = ClientUsers(
                id=test_user_id,
                client_id=self.test_client_id,
                user_name="backup_test_user",
                user_email="backup.test@example.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_user)
            
            # Create test crew jobs
            for i in range(5):
                job_id = str(uuid.uuid4())
                crew_job = CrewJobs(
                    id=job_id,
                    client_id=self.test_client_id,
                    crew_name=f"backup_test_crew_{i}",
                    job_status="completed",
                    job_input={"test": f"backup_test_input_{i}"},
                    job_output={"result": f"backup_test_output_{i}"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(crew_job)
                self.test_data_ids.append(job_id)
            
            # Create test memory entries
            for i in range(10):
                memory_id = str(uuid.uuid4())
                crew_memory = CrewMemory(
                    id=memory_id,
                    client_id=self.test_client_id,
                    memory_type="entity",
                    memory_content=f"Test memory content {i} for backup validation",
                    memory_metadata={"test_index": i, "backup_test": True},
                    created_at=datetime.utcnow()
                )
                session.add(crew_memory)
                self.test_data_ids.append(memory_id)
            
            await session.commit()
            
        self.logger.info(f"Created test data: client_id={self.test_client_id}, {len(self.test_data_ids)} records")
    
    async def _test_backup_during_operations(self):
        """Test database backup while operations are running."""
        backup_file = os.path.join(self.temp_dir, "active_backup.sql")
        
        # Start concurrent operations
        operation_task = asyncio.create_task(self._simulate_concurrent_operations())
        
        # Wait a moment for operations to start
        await asyncio.sleep(0.5)
        
        # Perform backup during operations
        backup_success = await self._perform_database_backup(backup_file)
        
        # Stop concurrent operations
        operation_task.cancel()
        try:
            await operation_task
        except asyncio.CancelledError:
            pass
        
        assert backup_success, "Backup failed during concurrent operations"
        assert os.path.exists(backup_file), "Backup file was not created"
        assert os.path.getsize(backup_file) > 0, "Backup file is empty"
        
        self.logger.info(f"Backup completed during operations: {os.path.getsize(backup_file)} bytes")
    
    async def _test_backup_consistency(self):
        """Test that backup data is consistent and complete."""
        backup_file = os.path.join(self.temp_dir, "consistency_backup.sql")
        
        # Get data counts before backup
        async with get_direct_session() as session:
            client_count = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            job_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_jobs WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            memory_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
        
        # Perform backup
        backup_success = await self._perform_database_backup(backup_file)
        assert backup_success, "Backup operation failed"
        
        # Verify backup file contains expected data
        with open(backup_file, 'r') as f:
            backup_content = f.read()
        
        # Check that backup contains our test data
        assert self.test_client_id in backup_content, "Test client ID not found in backup"
        assert "backup_test_crew" in backup_content, "Test crew jobs not found in backup"
        assert "Test memory content" in backup_content, "Test memory content not found in backup"
        
        self.logger.info(f"Backup consistency verified: {client_count} clients, {job_count} jobs, {memory_count} memories")
    
    async def _test_backup_restoration(self):
        """Test backup restoration procedures."""
        backup_file = os.path.join(self.temp_dir, "restore_test_backup.sql")
        
        # Create backup
        backup_success = await self._perform_database_backup(backup_file)
        assert backup_success, "Initial backup failed"
        
        # Delete test data
        async with get_direct_session() as session:
            await session.execute(
                text("DELETE FROM crew_memory WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            await session.execute(
                text("DELETE FROM crew_jobs WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            await session.execute(
                text("DELETE FROM client_users WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            await session.execute(
                text("DELETE FROM clients WHERE id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            await session.commit()
        
        # Verify data is deleted
        async with get_direct_session() as session:
            client_exists = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            assert client_exists == 0, "Test data was not properly deleted"
        
        # Restore from backup
        restore_success = await self._restore_from_backup(backup_file)
        assert restore_success, "Backup restoration failed"
        
        # Verify data is restored
        async with get_direct_session() as session:
            client_exists = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            job_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_jobs WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            memory_count = await session.scalar(
                text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
        
        assert client_exists > 0, "Client data was not restored"
        assert job_count == 5, f"Expected 5 crew jobs, found {job_count}"
        assert memory_count == 10, f"Expected 10 memory entries, found {memory_count}"
        
        self.logger.info("Backup restoration completed successfully")
    
    async def _test_no_data_loss(self):
        """Test that no data is lost during backup operations."""
        # Record initial data state
        initial_counts = await self._get_data_counts()
        
        # Perform backup
        backup_file = os.path.join(self.temp_dir, "no_loss_backup.sql")
        backup_success = await self._perform_database_backup(backup_file)
        assert backup_success, "Backup operation failed"
        
        # Verify data counts are unchanged
        final_counts = await self._get_data_counts()
        
        for table, initial_count in initial_counts.items():
            final_count = final_counts.get(table, 0)
            assert final_count >= initial_count, f"Data loss detected in {table}: {initial_count} -> {final_count}"
        
        self.logger.info("No data loss detected during backup operation")
    
    async def _test_incremental_backup(self):
        """Test incremental backup procedures."""
        # Create initial backup
        full_backup = os.path.join(self.temp_dir, "full_backup.sql")
        backup_success = await self._perform_database_backup(full_backup)
        assert backup_success, "Full backup failed"
        
        # Add new data
        new_data_ids = []
        async with get_direct_session() as session:
            for i in range(3):
                memory_id = str(uuid.uuid4())
                crew_memory = CrewMemory(
                    id=memory_id,
                    client_id=self.test_client_id,
                    memory_type="entity",
                    memory_content=f"Incremental test memory {i}",
                    memory_metadata={"incremental_test": True},
                    created_at=datetime.utcnow()
                )
                session.add(crew_memory)
                new_data_ids.append(memory_id)
            
            await session.commit()
        
        # Create incremental backup (simulate by backing up only new data)
        incremental_backup = os.path.join(self.temp_dir, "incremental_backup.sql")
        incremental_success = await self._perform_incremental_backup(incremental_backup, new_data_ids)
        assert incremental_success, "Incremental backup failed"
        
        # Verify incremental backup contains new data
        with open(incremental_backup, 'r') as f:
            incremental_content = f.read()
        
        assert "Incremental test memory" in incremental_content, "New data not found in incremental backup"
        
        self.logger.info(f"Incremental backup completed with {len(new_data_ids)} new records")
    
    async def _test_concurrent_backup(self):
        """Test backup with concurrent write operations."""
        backup_file = os.path.join(self.temp_dir, "concurrent_backup.sql")
        
        # Start backup and concurrent writes simultaneously
        backup_task = asyncio.create_task(self._perform_database_backup(backup_file))
        write_task = asyncio.create_task(self._perform_concurrent_writes())
        
        # Wait for both to complete
        backup_success, write_count = await asyncio.gather(backup_task, write_task)
        
        assert backup_success, "Backup failed with concurrent writes"
        assert write_count > 0, "No concurrent writes were performed"
        assert os.path.exists(backup_file), "Backup file was not created"
        
        self.logger.info(f"Concurrent backup completed with {write_count} concurrent writes")
    
    async def _simulate_concurrent_operations(self):
        """Simulate concurrent database operations during backup."""
        try:
            while True:
                async with get_pooled_session() as session:
                    # Perform some read operations
                    await session.execute(
                        text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                        {# "client_id" removed - use actor_id when actor_type="client"
                    )
                    
                    # Small write operation
                    temp_id = str(uuid.uuid4())
                    temp_memory = CrewMemory(
                        id=temp_id,
                        client_id=self.test_client_id,
                        memory_type="temp",
                        memory_content="Temporary concurrent operation data",
                        memory_metadata={"concurrent": True},
                        created_at=datetime.utcnow()
                    )
                    session.add(temp_memory)
                    await session.commit()
                    
                    # Clean up temporary data
                    await session.execute(
                        text("DELETE FROM crew_memory WHERE id = :id"),
                        {"id": temp_id}
                    )
                    await session.commit()
                
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
    
    async def _perform_database_backup(self, backup_file: str) -> bool:
        """Perform database backup using pg_dump."""
        try:
            # Get database connection info from environment
            db_host = os.getenv("DATABASE_HOST", "localhost")
            db_port = os.getenv("DATABASE_PORT", "5432")
            db_name = os.getenv("DATABASE_NAME", "sparkjar_crew")
            db_user = os.getenv("DATABASE_USER", "postgres")
            db_password = os.getenv("DATABASE_PASSWORD", "")
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                f"--file={backup_file}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Database backup completed: {backup_file}")
                return True
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backup error: {e}")
            return False
    
    async def _restore_from_backup(self, backup_file: str) -> bool:
        """Restore database from backup file."""
        try:
            # Get database connection info
            db_host = os.getenv("DATABASE_HOST", "localhost")
            db_port = os.getenv("DATABASE_PORT", "5432")
            db_name = os.getenv("DATABASE_NAME", "sparkjar_crew")
            db_user = os.getenv("DATABASE_USER", "postgres")
            db_password = os.getenv("DATABASE_PASSWORD", "")
            
            # Build psql command for restore
            cmd = [
                "psql",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--no-password",
                f"--file={backup_file}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password
            
            # Execute restore
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Database restore completed from: {backup_file}")
                return True
            else:
                self.logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Restore error: {e}")
            return False
    
    async def _perform_incremental_backup(self, backup_file: str, data_ids: List[str]) -> bool:
        """Simulate incremental backup by exporting specific records."""
        try:
            async with get_direct_session() as session:
                # Export specific memory records
                result = await session.execute(
                    text("SELECT * FROM crew_memory WHERE id = ANY(:ids)"),
                    {"ids": data_ids}
                )
                records = result.fetchall()
                
                # Write to backup file (simplified format)
                with open(backup_file, 'w') as f:
                    f.write("-- Incremental Backup\n")
                    f.write(f"-- Created: {datetime.utcnow()}\n")
                    f.write(f"-- Records: {len(records)}\n\n")
                    
                    for record in records:
                        f.write(f"INSERT INTO crew_memory VALUES {record};\n")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Incremental backup error: {e}")
            return False
    
    async def _perform_concurrent_writes(self) -> int:
        """Perform concurrent write operations during backup."""
        write_count = 0
        try:
            for i in range(10):
                async with get_pooled_session() as session:
                    temp_id = str(uuid.uuid4())
                    temp_memory = CrewMemory(
                        id=temp_id,
                        client_id=self.test_client_id,
                        memory_type="concurrent_test",
                        memory_content=f"Concurrent write {i}",
                        memory_metadata={"concurrent_write": True},
                        created_at=datetime.utcnow()
                    )
                    session.add(temp_memory)
                    await session.commit()
                    write_count += 1
                    
                    # Clean up immediately
                    await session.execute(
                        text("DELETE FROM crew_memory WHERE id = :id"),
                        {"id": temp_id}
                    )
                    await session.commit()
                
                await asyncio.sleep(0.05)
                
        except Exception as e:
            self.logger.error(f"Concurrent write error: {e}")
        
        return write_count
    
    async def _get_data_counts(self) -> Dict[str, int]:
        """Get current data counts for verification."""
        counts = {}
        
        async with get_direct_session() as session:
            # Count test client data
            counts["clients"] = await session.scalar(
                text("SELECT COUNT(*) FROM clients WHERE id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            counts["crew_jobs"] = await session.scalar(
                text("SELECT COUNT(*) FROM crew_jobs WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            counts["crew_memory"] = await session.scalar(
                text("SELECT COUNT(*) FROM crew_memory WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
            counts["client_users"] = await session.scalar(
                text("SELECT COUNT(*) FROM client_users WHERE client_id = :client_id"),
                {# "client_id" removed - use actor_id when actor_type="client"
            )
        
        return counts
    
    async def _cleanup_test_environment(self):
        """Clean up test environment and temporary files."""
        try:
            # Clean up test data
            if self.test_client_id:
                async with get_direct_session() as session:
                    await session.execute(
                        text("DELETE FROM crew_memory WHERE client_id = :client_id"),
                        {# "client_id" removed - use actor_id when actor_type="client"
                    )
                    await session.execute(
                        text("DELETE FROM crew_jobs WHERE client_id = :client_id"),
                        {# "client_id" removed - use actor_id when actor_type="client"
                    )
                    await session.execute(
                        text("DELETE FROM client_users WHERE client_id = :client_id"),
                        {# "client_id" removed - use actor_id when actor_type="client"
                    )
                    await session.execute(
                        text("DELETE FROM clients WHERE id = :client_id"),
                        {# "client_id" removed - use actor_id when actor_type="client"
                    )
                    await session.commit()
                
                self.logger.info(f"Cleaned up test data for client: {self.test_client_id}")
            
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"Cleaned up temp directory: {self.temp_dir}")
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
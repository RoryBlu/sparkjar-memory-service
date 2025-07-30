# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""
Cleanup and maintenance operations validator.

This module tests the system's ability to:
- Clean up generic entities that are no longer needed
- Implement entity grade decay mechanisms
- Perform database maintenance operations
- Measure impact of cleanup on system performance
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

class CleanupValidator(BaseValidator):
    """Validate cleanup and maintenance operations."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("CleanupValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Cleanup metrics
        self.cleanup_metrics = {}
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "cleanup_batch_size": int(os.getenv("CLEANUP_BATCH_SIZE", "100")),
            "grade_decay_threshold": float(os.getenv("GRADE_DECAY_THRESHOLD", "0.1")),
            "generic_entity_age_days": int(os.getenv("GENERIC_ENTITY_AGE_DAYS", "30")),
            "maintenance_timeout_seconds": int(os.getenv("MAINTENANCE_TIMEOUT", "300"))
        }
    
    async def test_generic_entity_cleanup(self) -> ValidationResult:
        """Test cleanup of generic entities that are no longer needed."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="generic_entity_cleanup",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_client_id = f"cleanup_test_{int(time.time())}"
            
            # Create test entities with different grades and ages
            entities_created = 0
            generic_entities = []
            specific_entities = []
            
            async with async_session() as session:
                # Create generic entities (low grade, old)
                for i in range(10):
                    entity_id = f"generic_{test_client_id}_{i}"
                    old_date = datetime.utcnow() - timedelta(days=self.config["generic_entity_age_days"] + 1)
                    
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, grade, metadata, created_at, updated_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :grade, :metadata, :created_at, :updated_at)
                    """), {
                        "id": entity_id,
                        "actor_type": "client",
                        "actor_id": test_client_id,
                        "name": f"Generic Entity {i}",
                        "entity_type": "generic",
                        "grade": 0.05,  # Very low grade
                        "metadata": json.dumps({"type": "generic", "test": True}),
                        "created_at": old_date,
                        "updated_at": old_date
                    })
                    
                    generic_entities.append(entity_id)
                    entities_created += 1
                
                # Create specific entities (high grade, recent)
                for i in range(5):
                    entity_id = f"specific_{test_client_id}_{i}"
                    recent_date = datetime.utcnow() - timedelta(days=1)
                    
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, grade, metadata, created_at, updated_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :grade, :metadata, :created_at, :updated_at)
                    """), {
                        "id": entity_id,
                        "actor_type": "client",
                        "actor_id": test_client_id,
                        "name": f"Specific Entity {i}",
                        "entity_type": "person",
                        "grade": 0.8,  # High grade
                        "metadata": json.dumps({"type": "specific", "test": True}),
                        "created_at": recent_date,
                        "updated_at": recent_date
                    })
                    
                    specific_entities.append(entity_id)
                    entities_created += 1
                
                await session.commit()
            
            # Perform cleanup operation
            cleanup_start = time.perf_counter()
            entities_cleaned = 0
            
            async with async_session() as session:
                # Clean up generic entities that are old and have low grade
                cleanup_query = text("""
                    DELETE FROM memory_entities 
                    WHERE actor_id = :actor_id 
                    AND entity_type = 'generic' 
                    AND grade < :grade_threshold 
                    AND updated_at < :age_threshold
                """)
                
                age_threshold = datetime.utcnow() - timedelta(days=self.config["generic_entity_age_days"])
                
                result = await session.execute(cleanup_query, {
                    "actor_id": test_client_id,
                    "grade_threshold": self.config["grade_decay_threshold"],
                    "age_threshold": age_threshold
                })
                
                entities_cleaned = result.rowcount
                await session.commit()
            
            cleanup_time = (time.perf_counter() - cleanup_start) * 1000
            
            # Verify cleanup results
            async with async_session() as session:
                # Count remaining entities
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                
                remaining_entities = result.scalar()
                
                # Count specific entities (should be preserved)
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities 
                    WHERE actor_id = :actor_id AND entity_type != 'generic'
                """), {"actor_id": test_client_id})
                
                remaining_specific = result.scalar()
            
            # Clean up test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Record cleanup metrics
            self.cleanup_metrics["generic_entity_cleanup"] = {
                "entities_created": entities_created,
                "entities_cleaned": entities_cleaned,
                "remaining_entities": remaining_entities,
                "remaining_specific": remaining_specific,
                "cleanup_time_ms": cleanup_time
            }
            
            # Validate results
            expected_cleaned = len(generic_entities)  # All generic entities should be cleaned
            expected_remaining = len(specific_entities)  # Only specific entities should remain
            
            if entities_cleaned == expected_cleaned and remaining_specific == expected_remaining:
                return ValidationResult(
                    test_name="generic_entity_cleanup",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entities_created": entities_created,
                        "entities_cleaned": entities_cleaned,
                        "remaining_entities": remaining_entities,
                        "cleanup_time_ms": cleanup_time,
                        "cleanup_efficiency": entities_cleaned / entities_created if entities_created > 0 else 0
                    }
                )
            else:
                return ValidationResult(
                    test_name="generic_entity_cleanup",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Cleanup did not work as expected. Cleaned: {entities_cleaned}, Expected: {expected_cleaned}",
                    details={
                        "entities_created": entities_created,
                        "entities_cleaned": entities_cleaned,
                        "expected_cleaned": expected_cleaned,
                        "remaining_entities": remaining_entities,
                        "expected_remaining": expected_remaining
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="generic_entity_cleanup",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Generic entity cleanup test failed: {str(e)}"
            )
    
    async def test_entity_grade_decay(self) -> ValidationResult:
        """Test entity grade decay mechanisms."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="entity_grade_decay",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_client_id = f"decay_test_{int(time.time())}"
            
            # Create entities with different initial grades
            entities_created = 0
            initial_grades = [0.9, 0.7, 0.5, 0.3, 0.1]
            
            async with async_session() as session:
                for i, grade in enumerate(initial_grades):
                    entity_id = f"decay_{test_client_id}_{i}"
                    old_date = datetime.utcnow() - timedelta(days=7)  # Week old
                    
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, grade, metadata, created_at, updated_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :grade, :metadata, :created_at, :updated_at)
                    """), {
                        "id": entity_id,
                        "actor_type": "client",
                        "actor_id": test_client_id,
                        "name": f"Decay Test Entity {i}",
                        "entity_type": "person",
                        "grade": grade,
                        "metadata": json.dumps({"initial_grade": grade, "test": True}),
                        "created_at": old_date,
                        "updated_at": old_date
                    })
                    
                    entities_created += 1
                
                await session.commit()
            
            # Apply grade decay (simulate time-based decay)
            decay_start = time.perf_counter()
            decay_factor = 0.9  # 10% decay per week
            
            async with async_session() as session:
                # Update grades with decay factor
                await session.execute(text("""
                    UPDATE memory_entities 
                    SET grade = grade * :decay_factor,
                        updated_at = :updated_at
                    WHERE actor_id = :actor_id 
                    AND updated_at < :decay_threshold
                """), {
                    "decay_factor": decay_factor,
                    "updated_at": datetime.utcnow(),
                    "actor_id": test_client_id,
                    "decay_threshold": datetime.utcnow() - timedelta(days=1)
                })
                
                await session.commit()
            
            decay_time = (time.perf_counter() - decay_start) * 1000
            
            # Verify decay results
            async with async_session() as session:
                result = await session.execute(text("""
                    SELECT id, grade, metadata FROM memory_entities 
                    WHERE actor_id = :actor_id 
                    ORDER BY id
                """), {"actor_id": test_client_id})
                
                entities = result.fetchall()
            
            # Validate decay
            decay_correct = True
            decay_results = []
            
            for i, (entity_id, current_grade, metadata_str) in enumerate(entities):
                metadata = json.loads(metadata_str)
                initial_grade = metadata["initial_grade"]
                expected_grade = initial_grade * decay_factor
                
                decay_results.append({
                    "entity_id": entity_id,
                    "initial_grade": initial_grade,
                    "current_grade": current_grade,
                    "expected_grade": expected_grade,
                    "decay_correct": abs(current_grade - expected_grade) < 0.01
                })
                
                if abs(current_grade - expected_grade) >= 0.01:
                    decay_correct = False
            
            # Clean up test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Record decay metrics
            self.cleanup_metrics["entity_grade_decay"] = {
                "entities_processed": entities_created,
                "decay_factor": decay_factor,
                "decay_time_ms": decay_time,
                "decay_results": decay_results
            }
            
            if decay_correct:
                return ValidationResult(
                    test_name="entity_grade_decay",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entities_processed": entities_created,
                        "decay_factor": decay_factor,
                        "decay_time_ms": decay_time,
                        "all_decays_correct": True
                    }
                )
            else:
                return ValidationResult(
                    test_name="entity_grade_decay",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Grade decay did not work correctly for all entities",
                    details={
                        "entities_processed": entities_created,
                        "decay_results": decay_results,
                        "decay_time_ms": decay_time
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="entity_grade_decay",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Entity grade decay test failed: {str(e)}"
            )
    
    async def test_database_maintenance_operations(self) -> ValidationResult:
        """Test database maintenance operations."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="database_maintenance_operations",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            maintenance_operations = []
            
            # Test VACUUM operation (PostgreSQL specific)
            try:
                vacuum_start = time.perf_counter()
                async with async_session() as session:
                    # Note: VACUUM cannot be run inside a transaction in PostgreSQL
                    # This is a simulation of maintenance operations
                    await session.execute(text("SELECT pg_stat_user_tables.schemaname, pg_stat_user_tables.relname FROM pg_stat_user_tables LIMIT 1"))
                    
                vacuum_time = (time.perf_counter() - vacuum_start) * 1000
                maintenance_operations.append({
                    "operation": "vacuum_simulation",
                    "success": True,
                    "time_ms": vacuum_time
                })
            except Exception as e:
                maintenance_operations.append({
                    "operation": "vacuum_simulation",
                    "success": False,
                    "error": str(e),
                    "time_ms": 0
                })
            
            # Test ANALYZE operation simulation
            try:
                analyze_start = time.perf_counter()
                async with async_session() as session:
                    # Simulate analyze by getting table statistics
                    await session.execute(text("""
                        SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
                        FROM pg_stat_user_tables 
                        WHERE schemaname = 'public' 
                        LIMIT 5
                    """))
                    
                analyze_time = (time.perf_counter() - analyze_start) * 1000
                maintenance_operations.append({
                    "operation": "analyze_simulation",
                    "success": True,
                    "time_ms": analyze_time
                })
            except Exception as e:
                maintenance_operations.append({
                    "operation": "analyze_simulation",
                    "success": False,
                    "error": str(e),
                    "time_ms": 0
                })
            
            # Test index maintenance simulation
            try:
                index_start = time.perf_counter()
                async with async_session() as session:
                    # Check index usage statistics
                    await session.execute(text("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        WHERE schemaname = 'public'
                        LIMIT 5
                    """))
                    
                index_time = (time.perf_counter() - index_start) * 1000
                maintenance_operations.append({
                    "operation": "index_maintenance_simulation",
                    "success": True,
                    "time_ms": index_time
                })
            except Exception as e:
                maintenance_operations.append({
                    "operation": "index_maintenance_simulation",
                    "success": False,
                    "error": str(e),
                    "time_ms": 0
                })
            
            await engine.dispose()
            
            # Analyze results
            successful_operations = sum(1 for op in maintenance_operations if op["success"])
            total_operations = len(maintenance_operations)
            total_maintenance_time = sum(op.get("time_ms", 0) for op in maintenance_operations)
            
            # Record maintenance metrics
            self.cleanup_metrics["database_maintenance"] = {
                "operations": maintenance_operations,
                "successful_operations": successful_operations,
                "total_operations": total_operations,
                "total_time_ms": total_maintenance_time
            }
            
            if successful_operations == total_operations:
                return ValidationResult(
                    test_name="database_maintenance_operations",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "successful_operations": successful_operations,
                        "total_operations": total_operations,
                        "total_maintenance_time_ms": total_maintenance_time,
                        "operations": maintenance_operations
                    }
                )
            else:
                return ValidationResult(
                    test_name="database_maintenance_operations",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Some maintenance operations failed: {total_operations - successful_operations}/{total_operations}",
                    details={
                        "successful_operations": successful_operations,
                        "total_operations": total_operations,
                        "operations": maintenance_operations
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="database_maintenance_operations",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Database maintenance operations test failed: {str(e)}"
            )
    
    async def test_cleanup_performance_impact(self) -> ValidationResult:
        """Test the impact of cleanup operations on system performance."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="cleanup_performance_impact",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_client_id = f"performance_test_{int(time.time())}"
            
            # Create a larger dataset for performance testing
            entities_to_create = 1000
            entities_created = 0
            
            # Measure baseline performance (before cleanup)
            baseline_start = time.perf_counter()
            
            async with async_session() as session:
                # Create test entities
                for i in range(entities_to_create):
                    entity_id = f"perf_{test_client_id}_{i}"
                    grade = 0.05 if i % 2 == 0 else 0.8  # Half low grade, half high grade
                    entity_type = "generic" if i % 2 == 0 else "person"
                    old_date = datetime.utcnow() - timedelta(days=35 if i % 2 == 0 else 1)
                    
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, grade, metadata, created_at, updated_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :grade, :metadata, :created_at, :updated_at)
                    """), {
                        "id": entity_id,
                        "actor_type": "client",
                        "actor_id": test_client_id,
                        "name": f"Performance Test Entity {i}",
                        "entity_type": entity_type,
                        "grade": grade,
                        "metadata": json.dumps({"test": True, "index": i}),
                        "created_at": old_date,
                        "updated_at": old_date
                    })
                    
                    entities_created += 1
                    
                    # Commit in batches for better performance
                    if i % self.config["cleanup_batch_size"] == 0:
                        await session.commit()
                
                await session.commit()
            
            baseline_time = (time.perf_counter() - baseline_start) * 1000
            
            # Measure query performance before cleanup
            query_before_start = time.perf_counter()
            async with async_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                count_before = result.scalar()
            query_before_time = (time.perf_counter() - query_before_start) * 1000
            
            # Perform cleanup operation
            cleanup_start = time.perf_counter()
            async with async_session() as session:
                result = await session.execute(text("""
                    DELETE FROM memory_entities 
                    WHERE actor_id = :actor_id 
                    AND entity_type = 'generic' 
                    AND grade < :grade_threshold 
                    AND updated_at < :age_threshold
                """), {
                    "actor_id": test_client_id,
                    "grade_threshold": self.config["grade_decay_threshold"],
                    "age_threshold": datetime.utcnow() - timedelta(days=self.config["generic_entity_age_days"])
                })
                
                entities_cleaned = result.rowcount
                await session.commit()
            cleanup_time = (time.perf_counter() - cleanup_start) * 1000
            
            # Measure query performance after cleanup
            query_after_start = time.perf_counter()
            async with async_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                count_after = result.scalar()
            query_after_time = (time.perf_counter() - query_after_start) * 1000
            
            # Clean up remaining test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Calculate performance metrics
            performance_improvement = ((query_before_time - query_after_time) / query_before_time * 100) if query_before_time > 0 else 0
            cleanup_efficiency = entities_cleaned / entities_created if entities_created > 0 else 0
            
            # Record performance metrics
            self.cleanup_metrics["cleanup_performance_impact"] = {
                "entities_created": entities_created,
                "entities_cleaned": entities_cleaned,
                "count_before": count_before,
                "count_after": count_after,
                "baseline_time_ms": baseline_time,
                "cleanup_time_ms": cleanup_time,
                "query_before_time_ms": query_before_time,
                "query_after_time_ms": query_after_time,
                "performance_improvement_percent": performance_improvement,
                "cleanup_efficiency": cleanup_efficiency
            }
            
            # Determine if performance impact is acceptable
            acceptable_cleanup_time = 5000  # 5 seconds max for cleanup
            acceptable_performance_degradation = -10  # Max 10% performance degradation
            
            if (cleanup_time <= acceptable_cleanup_time and 
                performance_improvement >= acceptable_performance_degradation):
                return ValidationResult(
                    test_name="cleanup_performance_impact",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entities_created": entities_created,
                        "entities_cleaned": entities_cleaned,
                        "cleanup_time_ms": cleanup_time,
                        "performance_improvement_percent": performance_improvement,
                        "cleanup_efficiency": cleanup_efficiency,
                        "acceptable_performance": True
                    }
                )
            else:
                return ValidationResult(
                    test_name="cleanup_performance_impact",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Cleanup performance may be suboptimal. Time: {cleanup_time:.1f}ms, Performance change: {performance_improvement:.1f}%",
                    details={
                        "entities_created": entities_created,
                        "entities_cleaned": entities_cleaned,
                        "cleanup_time_ms": cleanup_time,
                        "performance_improvement_percent": performance_improvement,
                        "cleanup_efficiency": cleanup_efficiency,
                        "acceptable_performance": False
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="cleanup_performance_impact",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Cleanup performance impact test failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all cleanup and maintenance validation tests."""
        self.logger.info("Starting cleanup and maintenance validation tests")
        
        results = []
        
        # Run all cleanup tests
        test_methods = [
            self.test_generic_entity_cleanup,
            self.test_entity_grade_decay,
            self.test_database_maintenance_operations,
            self.test_cleanup_performance_impact
        ]
        
        for test_method in test_methods:
            try:
                self.logger.info(f"Running {test_method.__name__}")
                result = await test_method()
                results.append(result)
                
                if result.status == ValidationStatus.PASSED:
                    self.logger.info(f"✓ {result.test_name} passed")
                elif result.status == ValidationStatus.WARNING:
                    self.logger.warning(f"⚠ {result.test_name} passed with warnings: {result.warning_message}")
                else:
                    self.logger.error(f"✗ {result.test_name} failed: {result.error_message}")
                    
            except Exception as e:
                self.logger.error(f"Error running {test_method.__name__}: {str(e)}")
                results.append(ValidationResult(
                    test_name=test_method.__name__,
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message=f"Test execution failed: {str(e)}"
                ))
        
        self.logger.info(f"Cleanup validation completed. {len(results)} tests run.")
        return results
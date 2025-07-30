# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""
Scalability validation system for memory system.

This module provides comprehensive scalability testing for the SparkJAR memory system:
- Large dataset performance testing (1M+ entities)
- Resource management validation
- System capacity limit measurement
- Cleanup and maintenance operation testing
"""

import asyncio
import json
import logging
import os
import psutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

@dataclass
class ScalabilityResult:
    """Result of a scalability test."""
    test_name: str
    dataset_size: int
    max_concurrent_users: int
    operations_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    execution_time_ms: float
    breaking_point: Optional[Dict[str, Any]]
    details: Dict[str, Any]

class ScalabilityValidator(BaseValidator):
    """Comprehensive scalability testing for memory system."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("ScalabilityValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Scalability thresholds from requirements
        self.scalability_thresholds = {
            "max_entities_per_client": 1_000_000,  # 1M+ entities per client
            "max_relationships": 10_000_000,  # 10M relationships
            "max_storage_gb": 100,  # 100GB storage
            "max_concurrent_users": 1000,  # 1000 concurrent users
            "search_response_ms_large": 1000,  # <1s search with large datasets
            "memory_usage_limit_mb": 8192,  # 8GB memory limit
            "cpu_usage_limit_percent": 80  # 80% CPU usage limit
        }
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "300")),  # 5 minutes for large tests
            "large_dataset_size": int(os.getenv("LARGE_DATASET_SIZE", "10000")),  # Start with 10K for testing
            "max_test_entities": int(os.getenv("MAX_TEST_ENTITIES", "100000")),  # Max 100K for CI
            "batch_size": int(os.getenv("BATCH_SIZE", "1000")),  # Insert batch size
            "cleanup_enabled": os.getenv("CLEANUP_ENABLED", "true").lower() == "true"
        }
    
    def _get_detailed_system_resources(self) -> Dict[str, float]:
        """Get detailed system resource usage."""
        try:
            process = psutil.Process()
            system = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "process_cpu_percent": process.cpu_percent(),
                "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                "process_memory_percent": process.memory_percent(),
                "system_memory_total_mb": system.total / 1024 / 1024,
                "system_memory_used_mb": system.used / 1024 / 1024,
                "system_memory_percent": system.percent,
                "disk_total_gb": disk.total / 1024 / 1024 / 1024,
                "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                "disk_percent": (disk.used / disk.total) * 100,
                "open_files": len(process.open_files()),
                "threads": process.num_threads(),
                "connections": len(process.connections())
            }
        except Exception as e:
            self.logger.warning(f"Could not get system resources: {e}")
            return {}
    
    def _calculate_percentiles(self, response_times: List[float]) -> Tuple[float, float, float]:
        """Calculate average, 95th, and 99th percentiles from response times."""
        if not response_times:
            return 0.0, 0.0, 0.0
        
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        avg = sum(sorted_times) / n
        p95_idx = int(0.95 * n)
        p99_idx = int(0.99 * n)
        
        p95 = sorted_times[min(p95_idx, n-1)]
        p99 = sorted_times[min(p99_idx, n-1)]
        
        return avg, p95, p99
    
    async def _create_database_session(self):
        """Create database session for testing."""
        if not self.config["database_url"]:
            raise ValueError("Database URL not configured")
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        engine = create_async_engine(
            self.config["database_url"],
            pool_size=20,  # Larger pool for scalability testing
            max_overflow=30,
            pool_timeout=30,
            pool_recycle=3600
        )
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        return engine, async_session
    
    async def _insert_entities_batch(self, session, entities: List, batch_size: int = 1000) -> Tuple[int, float]:
        """Insert entities in batches for better performance."""
        from sqlalchemy import text
        
        total_inserted = 0
        total_time = 0.0
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            batch_start = time.perf_counter()
            
            try:
                # Use bulk insert for better performance
                values = []
                for entity in batch:
                    values.append({
                        "id": entity.id,
                        "actor_type": "client",
                        "actor_id": entity.client_user_id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "metadata": json.dumps(entity.metadata),
                        "created_at": entity.created_at
                    })
                
                # Use executemany for bulk insert
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), values)
                
                await session.commit()
                total_inserted += len(batch)
                
                batch_time = time.perf_counter() - batch_start
                total_time += batch_time
                
                if i % (batch_size * 10) == 0:  # Log progress every 10 batches
                    self.logger.info(f"Inserted {total_inserted} entities in {total_time:.2f}s")
                
            except Exception as e:
                self.logger.error(f"Batch insert failed at {i}: {e}")
                await session.rollback()
                raise
        
        return total_inserted, total_time
    
    async def test_large_dataset_performance(self) -> ScalabilityResult:
        """Test performance with large datasets (1M+ entities per client)."""
        start_time = time.perf_counter()
        test_client_id = f"large_dataset_test_{int(time.time())}"
        
        try:
            engine, async_session = await self._create_database_session()
            
            # Use configured dataset size (but cap for CI/testing)
            dataset_size = min(self.config["large_dataset_size"], self.config["max_test_entities"])
            batch_size = self.config["batch_size"]
            
            self.logger.info(f"Testing large dataset performance with {dataset_size} entities")
            
            # Track metrics throughout the test
            resource_snapshots = []
            response_times = []
            error_count = 0
            
            # Initial resource snapshot
            initial_resources = self._get_detailed_system_resources()
            resource_snapshots.append(("start", initial_resources))
            
            # Phase 1: Data Loading Performance
            self.logger.info("Phase 1: Loading large dataset...")
            load_start = time.perf_counter()
            
            entities = self.test_data_generator.generate_entities(dataset_size, test_client_id)
            generation_time = time.perf_counter() - load_start
            
            # Insert entities in batches
            async with async_session() as session:
                inserted_count, insert_time = await self._insert_entities_batch(session, entities, batch_size)
            
            load_end_resources = self._get_detailed_system_resources()
            resource_snapshots.append(("after_load", load_end_resources))
            
            load_time = time.perf_counter() - load_start
            self.logger.info(f"Loaded {inserted_count} entities in {load_time:.2f}s ({inserted_count/load_time:.1f} entities/sec)")
            
            # Phase 2: Search Performance with Large Dataset
            self.logger.info("Phase 2: Testing search performance with large dataset...")
            search_start = time.perf_counter()
            
            from sqlalchemy import text
            
            # Define search scenarios for large datasets
            search_scenarios = [
                ("count_all", "SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id"),
                ("recent_entities", "SELECT * FROM memory_entities WHERE actor_id = :actor_id ORDER BY created_at DESC LIMIT 50"),
                ("name_search", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND name LIKE :pattern LIMIT 20"),
                ("type_filter", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND entity_type = :entity_type LIMIT 30"),
                ("metadata_query", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND metadata->>'department' IS NOT NULL LIMIT 25"),
                ("id_lookup", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND id = :entity_id"),
                ("pagination", "SELECT * FROM memory_entities WHERE actor_id = :actor_id ORDER BY name LIMIT 100 OFFSET :offset")
            ]
            
            search_results = {}
            
            for scenario_name, query in search_scenarios:
                scenario_times = []
                scenario_errors = 0
                iterations = 10  # Fewer iterations for large dataset tests
                
                for i in range(iterations):
                    operation_start = time.perf_counter()
                    
                    try:
                        async with async_session() as session:
                            if scenario_name == "name_search":
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "pattern": f"%{['John', 'Jane', 'Company', 'Meeting', 'Project'][i % 5]}%"
                                })
                            elif scenario_name == "type_filter":
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "entity_type": ["person", "company", "meeting", "project"][i % 4]
                                })
                            elif scenario_name == "id_lookup":
                                # Use a random entity ID from our test data
                                entity_id = entities[i * (len(entities) // iterations)].id
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "entity_id": entity_id
                                })
                            elif scenario_name == "pagination":
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "offset": i * 100
                                })
                            else:
                                await session.execute(text(query), {"actor_id": test_client_id})
                        
                        operation_time = (time.perf_counter() - operation_start) * 1000
                        scenario_times.append(operation_time)
                        response_times.append(operation_time)
                        
                    except Exception as e:
                        scenario_errors += 1
                        error_count += 1
                        self.logger.warning(f"Search error in {scenario_name}: {e}")
                
                # Calculate scenario statistics
                if scenario_times:
                    avg, p95, p99 = self._calculate_percentiles(scenario_times)
                    search_results[scenario_name] = {
                        "avg_response_time_ms": avg,
                        "p95_response_time_ms": p95,
                        "p99_response_time_ms": p99,
                        "error_count": scenario_errors,
                        "iterations": iterations
                    }
            
            search_time = time.perf_counter() - search_start
            search_end_resources = self._get_detailed_system_resources()
            resource_snapshots.append(("after_search", search_end_resources))
            
            # Phase 3: Concurrent Operations with Large Dataset
            self.logger.info("Phase 3: Testing concurrent operations with large dataset...")
            concurrent_start = time.perf_counter()
            
            concurrent_users = min(20, self.config.get("concurrent_users", 20))  # Moderate load for large dataset
            concurrent_times = []
            concurrent_errors = 0
            
            async def concurrent_user_operations(user_id: int) -> List[float]:
                """Simulate operations for a concurrent user on large dataset."""
                user_times = []
                operations = 3  # Fewer operations per user for large dataset test
                
                try:
                    for op in range(operations):
                        op_start = time.perf_counter()
                        
                        try:
                            async with async_session() as session:
                                # Mix of read operations on large dataset
                                if op == 0:
                                    # Count entities
                                    await session.execute(text("""
                                        SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                                    """), {"actor_id": test_client_id})
                                elif op == 1:
                                    # Search by type
                                    await session.execute(text("""
                                        SELECT * FROM memory_entities 
                                        WHERE actor_id = :actor_id AND entity_type = :entity_type 
                                        LIMIT 10
                                    """), {"actor_id": test_client_id, "entity_type": "person"})
                                else:
                                    # Recent entities
                                    await session.execute(text("""
                                        SELECT * FROM memory_entities 
                                        WHERE actor_id = :actor_id 
                                        ORDER BY created_at DESC LIMIT 5
                                    """), {"actor_id": test_client_id})
                            
                            op_time = (time.perf_counter() - op_start) * 1000
                            user_times.append(op_time)
                            
                        except Exception as e:
                            nonlocal concurrent_errors
                            concurrent_errors += 1
                            self.logger.warning(f"Concurrent operation error for user {user_id}: {e}")
                
                except Exception as e:
                    self.logger.error(f"Concurrent user {user_id} failed: {e}")
                
                return user_times
            
            # Execute concurrent operations
            tasks = [concurrent_user_operations(user_id) for user_id in range(concurrent_users)]
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect concurrent operation times
            for result in concurrent_results:
                if isinstance(result, list):
                    concurrent_times.extend(result)
                    response_times.extend(result)
                elif isinstance(result, Exception):
                    concurrent_errors += 3  # 3 operations per user
            
            concurrent_time = time.perf_counter() - concurrent_start
            concurrent_end_resources = self._get_detailed_system_resources()
            resource_snapshots.append(("after_concurrent", concurrent_end_resources))
            
            # Cleanup (if enabled)
            cleanup_time = 0.0
            if self.config["cleanup_enabled"]:
                self.logger.info("Phase 4: Cleaning up test data...")
                cleanup_start = time.perf_counter()
                
                async with async_session() as session:
                    # Delete in batches to avoid memory issues
                    deleted_total = 0
                    while True:
                        result = await session.execute(text("""
                            DELETE FROM memory_entities 
                            WHERE actor_id = :actor_id 
                            AND id IN (
                                SELECT id FROM memory_entities 
                                WHERE actor_id = :actor_id 
                                LIMIT :batch_size
                            )
                        """), {"actor_id": test_client_id, "batch_size": batch_size})
                        
                        deleted_count = result.rowcount
                        deleted_total += deleted_count
                        await session.commit()
                        
                        if deleted_count == 0:
                            break
                        
                        if deleted_total % (batch_size * 10) == 0:
                            self.logger.info(f"Deleted {deleted_total} entities...")
                
                cleanup_time = time.perf_counter() - cleanup_start
                self.logger.info(f"Cleaned up {deleted_total} entities in {cleanup_time:.2f}s")
            
            await engine.dispose()
            
            # Calculate final statistics
            execution_time = (time.perf_counter() - start_time) * 1000
            total_operations = len(response_times)
            error_rate = error_count / total_operations if total_operations > 0 else 0
            
            if response_times:
                avg_response, p95_response, p99_response = self._calculate_percentiles(response_times)
            else:
                avg_response = p95_response = p99_response = 0.0
            
            # Calculate operations per second (excluding data loading time)
            active_time = search_time + concurrent_time
            ops_per_second = total_operations / active_time if active_time > 0 else 0
            
            # Get final resource usage
            final_resources = self._get_detailed_system_resources()
            
            return ScalabilityResult(
                test_name="large_dataset_performance",
                dataset_size=dataset_size,
                max_concurrent_users=concurrent_users,
                operations_per_second=ops_per_second,
                avg_response_time_ms=avg_response,
                p95_response_time_ms=p95_response,
                p99_response_time_ms=p99_response,
                memory_usage_mb=final_resources.get("process_memory_mb", 0),
                cpu_usage_percent=final_resources.get("process_cpu_percent", 0),
                error_rate=error_rate,
                execution_time_ms=execution_time,
                breaking_point=None,  # No breaking point reached in this test
                details={
                    "inserted_entities": inserted_count,
                    "generation_time_s": generation_time,
                    "insert_time_s": insert_time,
                    "load_time_s": load_time,
                    "search_time_s": search_time,
                    "concurrent_time_s": concurrent_time,
                    "cleanup_time_s": cleanup_time,
                    "search_scenarios": search_results,
                    "concurrent_users": concurrent_users,
                    "concurrent_errors": concurrent_errors,
                    "total_operations": total_operations,
                    "error_count": error_count,
                    "resource_snapshots": resource_snapshots,
                    "batch_size": batch_size
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Large dataset performance test failed: {e}", exc_info=True)
            
            return ScalabilityResult(
                test_name="large_dataset_performance",
                dataset_size=0,
                max_concurrent_users=0,
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                error_rate=1.0,
                execution_time_ms=execution_time,
                breaking_point={"error": str(e)},
                details={"error": str(e), "test_client_id": test_client_id}
            )
    
    async def validate_large_dataset_performance(self) -> ValidationResult:
        """Validate system performance with large datasets meets requirements."""
        result = await self.test_large_dataset_performance()
        
        issues = []
        warnings = []
        
        # Check dataset size achieved
        if result.dataset_size < self.config["large_dataset_size"]:
            warnings.append(f"Dataset size limited to {result.dataset_size} (target: {self.config['large_dataset_size']})")
        
        # Check search performance with large dataset
        if result.p95_response_time_ms > self.scalability_thresholds["search_response_ms_large"]:
            issues.append(f"Search too slow with large dataset: {result.p95_response_time_ms:.1f}ms > {self.scalability_thresholds['search_response_ms_large']}ms")
        
        # Check memory usage
        if result.memory_usage_mb > self.scalability_thresholds["memory_usage_limit_mb"]:
            issues.append(f"Memory usage too high: {result.memory_usage_mb:.1f}MB > {self.scalability_thresholds['memory_usage_limit_mb']}MB")
        
        # Check error rate
        if result.error_rate > 0.05:  # More than 5% error rate
            issues.append(f"High error rate with large dataset: {result.error_rate:.1%}")
        
        # Check throughput
        if result.operations_per_second < 5:  # Very low throughput
            warnings.append(f"Low throughput with large dataset: {result.operations_per_second:.1f} ops/sec")
        
        if issues:
            return ValidationResult(
                test_name="large_dataset_performance",
                status=ValidationStatus.FAILED,
                execution_time_ms=result.execution_time_ms,
                error_message=f"Large dataset performance issues: {'; '.join(issues)}",
                details=result.__dict__
            )
        elif warnings:
            return ValidationResult(
                test_name="large_dataset_performance",
                status=ValidationStatus.WARNING,
                execution_time_ms=result.execution_time_ms,
                warning_message=f"Large dataset performance warnings: {'; '.join(warnings)}",
                details=result.__dict__
            )
        else:
            return ValidationResult(
                test_name="large_dataset_performance",
                status=ValidationStatus.PASSED,
                execution_time_ms=result.execution_time_ms,
                details=result.__dict__
            )
    
    async def test_maximum_concurrent_users(self) -> ScalabilityResult:
        """Test maximum concurrent users the system can support."""
        start_time = time.perf_counter()
        test_client_id = f"concurrent_limit_test_{int(time.time())}"
        
        try:
            engine, async_session = await self._create_database_session()
            
            # Start with a reasonable number and increase until we find the limit
            max_users_tested = 0
            breaking_point = None
            successful_operations = 0
            failed_operations = 0
            response_times = []
            
            # Test increasing concurrent user loads
            for concurrent_users in [10, 25, 50, 100, 200, 500, 1000]:
                self.logger.info(f"Testing {concurrent_users} concurrent users...")
                
                async def user_operation(user_id: int) -> bool:
                    """Single user operation for concurrent testing."""
                    try:
                        op_start = time.perf_counter()
                        async with async_session() as session:
                            # Simple read operation
                            from sqlalchemy import text
                            await session.execute(text("SELECT 1"))
                        
                        op_time = (time.perf_counter() - op_start) * 1000
                        response_times.append(op_time)
                        return True
                    except Exception as e:
                        self.logger.warning(f"User {user_id} operation failed: {e}")
                        return False
                
                # Launch concurrent operations
                tasks = [user_operation(i) for i in range(concurrent_users)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successes and failures
                batch_successful = sum(1 for r in results if r is True)
                batch_failed = len(results) - batch_successful
                
                successful_operations += batch_successful
                failed_operations += batch_failed
                
                max_users_tested = concurrent_users
                
                # Check if we've hit a breaking point (>20% failure rate)
                failure_rate = batch_failed / len(results)
                if failure_rate > 0.2:
                    breaking_point = {
                        "concurrent_users": concurrent_users,
                        "failure_rate": failure_rate,
                        "successful_operations": batch_successful,
                        "failed_operations": batch_failed
                    }
                    break
                
                # Add delay between test batches
                await asyncio.sleep(1)
            
            await engine.dispose()
            
            # Calculate final metrics
            execution_time = (time.perf_counter() - start_time) * 1000
            total_operations = successful_operations + failed_operations
            error_rate = failed_operations / total_operations if total_operations > 0 else 0
            
            if response_times:
                avg_response, p95_response, p99_response = self._calculate_percentiles(response_times)
            else:
                avg_response = p95_response = p99_response = 0.0
            
            ops_per_second = total_operations / (execution_time / 1000) if execution_time > 0 else 0
            
            # Get final resource usage
            final_resources = self._get_detailed_system_resources()
            
            return ScalabilityResult(
                test_name="maximum_concurrent_users",
                dataset_size=0,
                max_concurrent_users=max_users_tested,
                operations_per_second=ops_per_second,
                avg_response_time_ms=avg_response,
                p95_response_time_ms=p95_response,
                p99_response_time_ms=p99_response,
                memory_usage_mb=final_resources.get("process_memory_mb", 0),
                cpu_usage_percent=final_resources.get("process_cpu_percent", 0),
                error_rate=error_rate,
                execution_time_ms=execution_time,
                breaking_point=breaking_point,
                details={
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "total_operations": total_operations,
                    "max_users_without_failure": max_users_tested if not breaking_point else breaking_point["concurrent_users"] - 10
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return ScalabilityResult(
                test_name="maximum_concurrent_users",
                dataset_size=0,
                max_concurrent_users=0,
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                error_rate=1.0,
                execution_time_ms=execution_time,
                breaking_point={"error": str(e)},
                details={"error": str(e)}
            )
    
    async def test_memory_usage_patterns(self) -> ScalabilityResult:
        """Test memory usage patterns under various loads."""
        start_time = time.perf_counter()
        test_client_id = f"memory_test_{int(time.time())}"
        
        try:
            engine, async_session = await self._create_database_session()
            
            memory_snapshots = []
            dataset_sizes = [100, 500, 1000, 5000, 10000]
            
            for dataset_size in dataset_sizes:
                self.logger.info(f"Testing memory usage with {dataset_size} entities...")
                
                # Take initial memory snapshot
                initial_memory = self._get_detailed_system_resources()
                
                # Create entities
                entities = self.test_data_generator.generate_entities(dataset_size, f"{test_client_id}_{dataset_size}")
                
                async with async_session() as session:
                    await self._insert_entities_batch(session, entities, 100)
                
                # Take memory snapshot after creation
                after_creation_memory = self._get_detailed_system_resources()
                
                # Perform some operations
                async with async_session() as session:
                    from sqlalchemy import text
                    # Search operations
                    await session.execute(text("""
                        SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                    """), {"actor_id": f"{test_client_id}_{dataset_size}"})
                    
                    await session.execute(text("""
                        SELECT * FROM memory_entities WHERE actor_id = :actor_id LIMIT 100
                    """), {"actor_id": f"{test_client_id}_{dataset_size}"})
                
                # Take final memory snapshot
                final_memory = self._get_detailed_system_resources()
                
                memory_snapshots.append({
                    "dataset_size": dataset_size,
                    "initial_memory_mb": initial_memory.get("process_memory_mb", 0),
                    "after_creation_memory_mb": after_creation_memory.get("process_memory_mb", 0),
                    "final_memory_mb": final_memory.get("process_memory_mb", 0),
                    "memory_increase_mb": final_memory.get("process_memory_mb", 0) - initial_memory.get("process_memory_mb", 0),
                    "system_memory_percent": final_memory.get("system_memory_percent", 0)
                })
                
                # Clean up this batch
                async with async_session() as session:
                    await session.execute(text("""
                        DELETE FROM memory_entities WHERE actor_id = :actor_id
                    """), {"actor_id": f"{test_client_id}_{dataset_size}"})
                    await session.commit()
            
            await engine.dispose()
            
            # Analyze memory patterns
            max_memory_usage = max(snapshot["final_memory_mb"] for snapshot in memory_snapshots)
            max_memory_increase = max(snapshot["memory_increase_mb"] for snapshot in memory_snapshots)
            
            # Calculate memory efficiency (entities per MB)
            memory_efficiency = []
            for snapshot in memory_snapshots:
                if snapshot["memory_increase_mb"] > 0:
                    efficiency = snapshot["dataset_size"] / snapshot["memory_increase_mb"]
                    memory_efficiency.append(efficiency)
            
            avg_efficiency = sum(memory_efficiency) / len(memory_efficiency) if memory_efficiency else 0
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return ScalabilityResult(
                test_name="memory_usage_patterns",
                dataset_size=max(dataset_sizes),
                max_concurrent_users=0,
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                memory_usage_mb=max_memory_usage,
                cpu_usage_percent=0.0,
                error_rate=0.0,
                execution_time_ms=execution_time,
                breaking_point=None,
                details={
                    "memory_snapshots": memory_snapshots,
                    "max_memory_usage_mb": max_memory_usage,
                    "max_memory_increase_mb": max_memory_increase,
                    "avg_memory_efficiency_entities_per_mb": avg_efficiency,
                    "dataset_sizes_tested": dataset_sizes
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return ScalabilityResult(
                test_name="memory_usage_patterns",
                dataset_size=0,
                max_concurrent_users=0,
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                error_rate=1.0,
                execution_time_ms=execution_time,
                breaking_point={"error": str(e)},
                details={"error": str(e)}
            )
    
    async def validate_system_resource_limits(self) -> ValidationResult:
        """Validate system resource limits and capacity."""
        start_time = time.perf_counter()
        
        try:
            # Test concurrent user limits
            concurrent_result = await self.test_maximum_concurrent_users()
            
            # Test memory usage patterns
            memory_result = await self.test_memory_usage_patterns()
            
            issues = []
            warnings = []
            
            # Check concurrent user capacity
            if concurrent_result.breaking_point and concurrent_result.max_concurrent_users < self.scalability_thresholds["max_concurrent_users"]:
                issues.append(f"Concurrent user limit too low: {concurrent_result.max_concurrent_users} < {self.scalability_thresholds['max_concurrent_users']}")
            
            # Check memory usage
            if memory_result.memory_usage_mb > self.scalability_thresholds["memory_usage_limit_mb"]:
                issues.append(f"Memory usage too high: {memory_result.memory_usage_mb:.1f}MB > {self.scalability_thresholds['memory_usage_limit_mb']}MB")
            
            # Check error rates
            if concurrent_result.error_rate > 0.05:  # More than 5% error rate
                issues.append(f"High error rate under load: {concurrent_result.error_rate:.1%}")
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            if issues:
                return ValidationResult(
                    test_name="system_resource_limits",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=execution_time,
                    error_message=f"Resource limit issues: {'; '.join(issues)}",
                    details={
                        "concurrent_test": concurrent_result.__dict__,
                        "memory_test": memory_result.__dict__,
                        "issues": issues
                    }
                )
            elif warnings:
                return ValidationResult(
                    test_name="system_resource_limits",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=execution_time,
                    warning_message=f"Resource limit warnings: {'; '.join(warnings)}",
                    details={
                        "concurrent_test": concurrent_result.__dict__,
                        "memory_test": memory_result.__dict__,
                        "warnings": warnings
                    }
                )
            else:
                return ValidationResult(
                    test_name="system_resource_limits",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=execution_time,
                    details={
                        "concurrent_test": concurrent_result.__dict__,
                        "memory_test": memory_result.__dict__,
                        "max_concurrent_users": concurrent_result.max_concurrent_users,
                        "max_memory_usage_mb": memory_result.memory_usage_mb
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="system_resource_limits",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Resource limits test failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all scalability validation tests."""
        self.logger.info("Starting scalability validation tests...")
        
        results = []
        
        # Test 6.1: Large dataset performance
        self.logger.info("Running large dataset performance validation...")
        large_dataset_result = await self.run_test(
            "large_dataset_performance",
            self.validate_large_dataset_performance
        )
        results.append(large_dataset_result)
        
        # Test 6.3: System resource limits
        self.logger.info("Running system resource limits validation...")
        resource_limits_result = await self.run_test(
            "system_resource_limits",
            self.validate_system_resource_limits
        )
        results.append(resource_limits_result)
        
        return results

async def main():
    """Main function for running scalability validation."""
    import logging
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run validator
    validator = ScalabilityValidator()
    results = await validator.run_validation()
    
    # Print results
    print(f"\n{'='*60}")
    print("SCALABILITY VALIDATION RESULTS")
    print(f"{'='*60}")
    
    for result in results:
        status_icon = "✅" if result.passed else "❌"
        print(f"{status_icon} {result.test_name}: {result.status.value}")
        if result.error_message:
            print(f"   Error: {result.error_message}")
        if result.warning_message:
            print(f"   Warning: {result.warning_message}")
        print(f"   Execution time: {result.execution_time_ms:.1f}ms")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
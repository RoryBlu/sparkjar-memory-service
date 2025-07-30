# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

"""
Performance benchmarking system for memory validation.

This module provides comprehensive performance testing for the SparkJAR memory system:
- Text processing performance across different sizes
- Concurrent operation handling
- Search and retrieval performance
- Resource usage monitoring
"""

import asyncio
import json
import logging
import os
import psutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

@dataclass
class BenchmarkResult:
    """Result of a performance benchmark test."""
    test_name: str
    operations_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    resource_usage: Dict[str, float]
    execution_time_ms: float
    details: Dict[str, Any]

class PerformanceBenchmarker(BaseValidator):
    """Comprehensive performance benchmarking for memory system."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("PerformanceBenchmarker")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Performance thresholds from requirements
        self.performance_thresholds = {
            "small_text_response_ms": 200,  # <1KB text
            "medium_text_response_ms": 500,  # 1-10KB text
            "large_text_response_ms": 2000,  # 10-50KB text
            "search_response_ms": 1000,  # Search with 100K+ entities
            "concurrent_users": 100,  # Concurrent user capacity
            "min_ops_per_second": 10  # Minimum operations per second
        }
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "mcp_api_url": os.getenv("MEMORY_MCP_API_URL", "http://localhost:8002"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
            "test_client_count": int(os.getenv("TEST_CLIENT_COUNT", "3")),
            "test_entity_count": int(os.getenv("TEST_ENTITY_COUNT", "100"))
        }
    
    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage."""
        try:
            process = psutil.Process()
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "open_files": len(process.open_files()),
                "threads": process.num_threads()
            }
        except Exception:
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
        
        engine = create_async_engine(self.config["database_url"])
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        return engine, async_session
    
    async def benchmark_text_processing_performance(self) -> BenchmarkResult:
        """Benchmark text processing performance for different text sizes."""
        start_time = time.perf_counter()
        
        try:
            engine, async_session = await self._create_database_session()
            
            # Generate text samples of different sizes
            text_samples = self.test_data_generator.generate_text_samples()
            test_client_id = f"perf_text_test_{int(time.time())}"
            
            # Test results storage
            results_by_size = {}
            all_response_times = []
            error_count = 0
            total_operations = 0
            
            from sqlalchemy import text
            
            # Test each text size category
            for size_category, text_content in text_samples.items():
                category_response_times = []
                category_errors = 0
                
                # Run multiple iterations for statistical significance
                iterations = 10 if size_category == "large" else 20
                
                for i in range(iterations):
                    operation_start = time.perf_counter()
                    
                    try:
                        # Create entity with text content
                        entity = self.test_data_generator.generate_entities(1, test_client_id)[0]
                        entity.metadata["text_content"] = text_content
                        entity.metadata["size_category"] = size_category
                        entity.name = f"text_entity_{size_category}_{i}"
                        
                        async with async_session() as session:
                            # Insert entity (simulating text processing)
                            await session.execute(text("""
                                INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                                VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                            """), {
                                "id": entity.id,
                                "actor_type": "client",
                                "actor_id": entity.client_user_id,
                                "name": entity.name,
                                "entity_type": entity.entity_type,
                                "metadata": json.dumps(entity.metadata),
                                "created_at": entity.created_at
                            })
                            
                            # Simulate text search/retrieval
                            await session.execute(text("""
                                SELECT name, metadata FROM memory_entities 
                                WHERE actor_id = :actor_id 
                                AND metadata->>'size_category' = :size_category
                                LIMIT 5
                            """), {"actor_id": test_client_id, "size_category": size_category})
                            
                            await session.commit()
                        
                        operation_time = (time.perf_counter() - operation_start) * 1000
                        category_response_times.append(operation_time)
                        all_response_times.append(operation_time)
                        
                    except Exception as e:
                        category_errors += 1
                        error_count += 1
                        self.logger.warning(f"Text processing error for {size_category}: {e}")
                    
                    total_operations += 1
                
                # Calculate statistics for this size category
                if category_response_times:
                    avg, p95, p99 = self._calculate_percentiles(category_response_times)
                    results_by_size[size_category] = {
                        "avg_response_time_ms": avg,
                        "p95_response_time_ms": p95,
                        "p99_response_time_ms": p99,
                        "error_count": category_errors,
                        "total_operations": iterations,
                        "text_size_bytes": len(text_content.encode('utf-8'))
                    }
            
            # Clean up test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Calculate overall statistics
            execution_time = (time.perf_counter() - start_time) * 1000
            error_rate = error_count / total_operations if total_operations > 0 else 0
            ops_per_second = total_operations / (execution_time / 1000) if execution_time > 0 else 0
            
            if all_response_times:
                avg_response, p95_response, p99_response = self._calculate_percentiles(all_response_times)
            else:
                avg_response = p95_response = p99_response = 0.0
            
            return BenchmarkResult(
                test_name="text_processing_performance",
                operations_per_second=ops_per_second,
                avg_response_time_ms=avg_response,
                p95_response_time_ms=p95_response,
                p99_response_time_ms=p99_response,
                error_rate=error_rate,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={
                    "results_by_size": results_by_size,
                    "total_operations": total_operations,
                    "error_count": error_count
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return BenchmarkResult(
                test_name="text_processing_performance",
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                error_rate=1.0,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={"error": str(e)}
            )
    
    async def benchmark_concurrent_operations(self) -> BenchmarkResult:
        """Benchmark system performance under concurrent load."""
        start_time = time.perf_counter()
        
        try:
            engine, async_session = await self._create_database_session()
            
            # Test configuration
            concurrent_users = min(50, self.config.get("concurrent_users", 50))  # Start with moderate load
            operations_per_user = 5
            test_client_base = f"concurrent_test_{int(time.time())}"
            
            # Track results
            all_response_times = []
            error_count = 0
            total_operations = 0
            
            from sqlalchemy import text
            
            async def user_operations(user_id: int) -> List[float]:
                """Simulate operations for a single concurrent user."""
                user_response_times = []
                user_client_id = f"{test_client_base}_user_{user_id}"
                
                try:
                    # Generate test entities for this user
                    entities = self.test_data_generator.generate_entities(operations_per_user, user_client_id)
                    
                    for entity in entities:
                        operation_start = time.perf_counter()
                        
                        try:
                            async with async_session() as session:
                                # Create entity
                                await session.execute(text("""
                                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                                """), {
                                    "id": entity.id,
                                    "actor_type": "client",
                                    "actor_id": entity.client_user_id,
                                    "name": entity.name,
                                    "entity_type": entity.entity_type,
                                    "metadata": json.dumps(entity.metadata),
                                    "created_at": entity.created_at
                                })
                                
                                # Search for entities
                                await session.execute(text("""
                                    SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                                """), {"actor_id": user_client_id})
                                
                                await session.commit()
                            
                            operation_time = (time.perf_counter() - operation_start) * 1000
                            user_response_times.append(operation_time)
                            
                        except Exception as e:
                            nonlocal error_count
                            error_count += 1
                            self.logger.warning(f"Concurrent operation error for user {user_id}: {e}")
                        
                        nonlocal total_operations
                        total_operations += 1
                
                except Exception as e:
                    self.logger.error(f"User {user_id} operations failed: {e}")
                
                return user_response_times
            
            # Execute concurrent operations
            concurrent_start = time.perf_counter()
            
            # Use asyncio.gather for true concurrency
            tasks = [user_operations(user_id) for user_id in range(concurrent_users)]
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            concurrent_time = (time.perf_counter() - concurrent_start) * 1000
            
            # Collect all response times
            for result in user_results:
                if isinstance(result, list):
                    all_response_times.extend(result)
                elif isinstance(result, Exception):
                    error_count += operations_per_user
            
            # Clean up test data
            cleanup_start = time.perf_counter()
            async with async_session() as session:
                for user_id in range(concurrent_users):
                    user_client_id = f"{test_client_base}_user_{user_id}"
                    await session.execute(text("""
                        DELETE FROM memory_entities WHERE actor_id = :actor_id
                    """), {"actor_id": user_client_id})
                await session.commit()
            cleanup_time = (time.perf_counter() - cleanup_start) * 1000
            
            await engine.dispose()
            
            # Calculate statistics
            execution_time = (time.perf_counter() - start_time) * 1000
            error_rate = error_count / total_operations if total_operations > 0 else 0
            ops_per_second = total_operations / (concurrent_time / 1000) if concurrent_time > 0 else 0
            
            if all_response_times:
                avg_response, p95_response, p99_response = self._calculate_percentiles(all_response_times)
            else:
                avg_response = p95_response = p99_response = 0.0
            
            return BenchmarkResult(
                test_name="concurrent_operations",
                operations_per_second=ops_per_second,
                avg_response_time_ms=avg_response,
                p95_response_time_ms=p95_response,
                p99_response_time_ms=p99_response,
                error_rate=error_rate,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={
                    "concurrent_users": concurrent_users,
                    "operations_per_user": operations_per_user,
                    "total_operations": total_operations,
                    "error_count": error_count,
                    "concurrent_execution_time_ms": concurrent_time,
                    "cleanup_time_ms": cleanup_time
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return BenchmarkResult(
                test_name="concurrent_operations",
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                error_rate=1.0,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={"error": str(e)}
            )
    
    async def benchmark_search_performance(self) -> BenchmarkResult:
        """Benchmark search and retrieval performance with various dataset sizes."""
        start_time = time.perf_counter()
        
        try:
            engine, async_session = await self._create_database_session()
            
            # Create test dataset
            test_client_id = f"search_perf_test_{int(time.time())}"
            entity_count = self.config.get("test_entity_count", 1000)  # Use larger dataset for search testing
            
            # Generate and insert test entities
            entities = self.test_data_generator.generate_entities(entity_count, test_client_id)
            
            from sqlalchemy import text
            
            # Insert test data
            insert_start = time.perf_counter()
            async with async_session() as session:
                for entity in entities:
                    await session.execute(text("""
                        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                        VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                    """), {
                        "id": entity.id,
                        "actor_type": "client",
                        "actor_id": entity.client_user_id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "metadata": json.dumps(entity.metadata),
                        "created_at": entity.created_at
                    })
                await session.commit()
            insert_time = (time.perf_counter() - insert_start) * 1000
            
            # Define search scenarios
            search_scenarios = [
                ("exact_id_search", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND id = :entity_id"),
                ("name_pattern_search", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND name LIKE :pattern LIMIT 10"),
                ("entity_type_search", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND entity_type = :entity_type LIMIT 20"),
                ("metadata_search", "SELECT * FROM memory_entities WHERE actor_id = :actor_id AND metadata->>'job_title' IS NOT NULL LIMIT 15"),
                ("count_search", "SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id"),
                ("recent_entities", "SELECT * FROM memory_entities WHERE actor_id = :actor_id ORDER BY created_at DESC LIMIT 25")
            ]
            
            # Execute search benchmarks
            search_results = {}
            all_search_times = []
            error_count = 0
            total_searches = 0
            
            for scenario_name, query in search_scenarios:
                scenario_times = []
                scenario_errors = 0
                iterations = 20
                
                for i in range(iterations):
                    search_start = time.perf_counter()
                    
                    try:
                        async with async_session() as session:
                            if scenario_name == "exact_id_search":
                                # Use a random entity ID from our test data
                                entity_id = entities[i % len(entities)].id
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "entity_id": entity_id
                                })
                            elif scenario_name == "name_pattern_search":
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "pattern": f"%{['John', 'Jane', 'Company', 'Meeting'][i % 4]}%"
                                })
                            elif scenario_name == "entity_type_search":
                                await session.execute(text(query), {
                                    "actor_id": test_client_id,
                                    "entity_type": ["person", "company", "meeting"][i % 3]
                                })
                            else:
                                await session.execute(text(query), {"actor_id": test_client_id})
                        
                        search_time = (time.perf_counter() - search_start) * 1000
                        scenario_times.append(search_time)
                        all_search_times.append(search_time)
                        
                    except Exception as e:
                        scenario_errors += 1
                        error_count += 1
                        self.logger.warning(f"Search error in {scenario_name}: {e}")
                    
                    total_searches += 1
                
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
            
            # Clean up test data
            cleanup_start = time.perf_counter()
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            cleanup_time = (time.perf_counter() - cleanup_start) * 1000
            
            await engine.dispose()
            
            # Calculate overall statistics
            execution_time = (time.perf_counter() - start_time) * 1000
            error_rate = error_count / total_searches if total_searches > 0 else 0
            searches_per_second = total_searches / ((execution_time - insert_time - cleanup_time) / 1000) if execution_time > 0 else 0
            
            if all_search_times:
                avg_response, p95_response, p99_response = self._calculate_percentiles(all_search_times)
            else:
                avg_response = p95_response = p99_response = 0.0
            
            return BenchmarkResult(
                test_name="search_performance",
                operations_per_second=searches_per_second,
                avg_response_time_ms=avg_response,
                p95_response_time_ms=p95_response,
                p99_response_time_ms=p99_response,
                error_rate=error_rate,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={
                    "dataset_size": entity_count,
                    "total_searches": total_searches,
                    "error_count": error_count,
                    "insert_time_ms": insert_time,
                    "cleanup_time_ms": cleanup_time,
                    "search_scenarios": search_results
                }
            )
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return BenchmarkResult(
                test_name="search_performance",
                operations_per_second=0.0,
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                error_rate=1.0,
                resource_usage=self._get_system_resources(),
                execution_time_ms=execution_time,
                details={"error": str(e)}
            )
    
    async def validate_text_processing_performance(self) -> ValidationResult:
        """Validate text processing meets performance requirements."""
        benchmark = await self.benchmark_text_processing_performance()
        
        issues = []
        
        # Check performance against requirements
        if "results_by_size" in benchmark.details:
            for size_category, results in benchmark.details["results_by_size"].items():
                threshold_key = f"{size_category}_text_response_ms"
                if threshold_key in self.performance_thresholds:
                    threshold = self.performance_thresholds[threshold_key]
                    if results["p95_response_time_ms"] > threshold:
                        issues.append(f"{size_category} text processing too slow: {results['p95_response_time_ms']:.1f}ms > {threshold}ms")
        
        if benchmark.error_rate > 0.05:  # More than 5% error rate
            issues.append(f"High error rate: {benchmark.error_rate:.1%}")
        
        if benchmark.operations_per_second < self.performance_thresholds["min_ops_per_second"]:
            issues.append(f"Low throughput: {benchmark.operations_per_second:.1f} ops/sec")
        
        if issues:
            return ValidationResult(
                test_name="text_processing_performance",
                status=ValidationStatus.WARNING,
                execution_time_ms=benchmark.execution_time_ms,
                warning_message=f"Performance issues: {'; '.join(issues)}",
                details=benchmark.__dict__
            )
        else:
            return ValidationResult(
                test_name="text_processing_performance",
                status=ValidationStatus.PASSED,
                execution_time_ms=benchmark.execution_time_ms,
                details=benchmark.__dict__
            )
    
    async def validate_concurrent_operation_handling(self) -> ValidationResult:
        """Validate system handles concurrent operations effectively."""
        benchmark = await self.benchmark_concurrent_operations()
        
        issues = []
        
        if benchmark.error_rate > 0.1:  # More than 10% error rate under load
            issues.append(f"High error rate under concurrent load: {benchmark.error_rate:.1%}")
        
        if benchmark.p95_response_time_ms > 1000:  # More than 1 second for 95% of operations
            issues.append(f"Slow response under load: {benchmark.p95_response_time_ms:.1f}ms p95")
        
        if benchmark.operations_per_second < 5:  # Very low throughput under load
            issues.append(f"Low concurrent throughput: {benchmark.operations_per_second:.1f} ops/sec")
        
        if issues:
            return ValidationResult(
                test_name="concurrent_operation_handling",
                status=ValidationStatus.WARNING,
                execution_time_ms=benchmark.execution_time_ms,
                warning_message=f"Concurrent performance issues: {'; '.join(issues)}",
                details=benchmark.__dict__
            )
        else:
            return ValidationResult(
                test_name="concurrent_operation_handling",
                status=ValidationStatus.PASSED,
                execution_time_ms=benchmark.execution_time_ms,
                details=benchmark.__dict__
            )
    
    async def validate_search_performance(self) -> ValidationResult:
        """Validate search and retrieval performance meets requirements."""
        benchmark = await self.benchmark_search_performance()
        
        issues = []
        
        if benchmark.avg_response_time_ms > self.performance_thresholds["search_response_ms"]:
            issues.append(f"Slow search performance: {benchmark.avg_response_time_ms:.1f}ms average")
        
        if benchmark.error_rate > 0.02:  # More than 2% error rate for searches
            issues.append(f"Search error rate too high: {benchmark.error_rate:.1%}")
        
        if benchmark.operations_per_second < 20:  # Less than 20 searches per second
            issues.append(f"Low search throughput: {benchmark.operations_per_second:.1f} searches/sec")
        
        if issues:
            return ValidationResult(
                test_name="search_performance",
                status=ValidationStatus.WARNING,
                execution_time_ms=benchmark.execution_time_ms,
                warning_message=f"Search performance issues: {'; '.join(issues)}",
                details=benchmark.__dict__
            )
        else:
            return ValidationResult(
                test_name="search_performance",
                status=ValidationStatus.PASSED,
                execution_time_ms=benchmark.execution_time_ms,
                details=benchmark.__dict__
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all performance validation tests."""
        self.logger.info("Starting performance benchmarking validation")
        
        tests = [
            ("text_processing_performance", self.validate_text_processing_performance),
            ("concurrent_operation_handling", self.validate_concurrent_operation_handling),
            ("search_performance", self.validate_search_performance)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.logger.info(f"Running performance test: {test_name}")
            result = await self.run_test(test_name, test_func)
            results.append(result)
        
        return results
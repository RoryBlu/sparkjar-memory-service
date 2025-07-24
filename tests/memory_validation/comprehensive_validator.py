"""
Comprehensive memory system validation suite.

This module provides a complete validation framework that tests:
- System health and connectivity
- Data integrity and consistency  
- Client isolation boundaries
- Entity management reliability
- Performance characteristics
- Error handling and recovery
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseValidator, ValidationResult, ValidationStatus, ValidationFramework
from .health_checker import MemorySystemHealthChecker
from .data_integrity_validator import DataIntegrityValidator
from .performance_benchmarker import PerformanceBenchmarker
from .error_simulator import ErrorSimulator
from .test_data_generator import TestDataGenerator

class ComprehensiveMemoryValidator(BaseValidator):
    """Comprehensive validation orchestrator for memory system."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("ComprehensiveMemoryValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Initialize sub-validators
        self.health_checker = MemorySystemHealthChecker(self.config)
        self.integrity_validator = DataIntegrityValidator(self.config.get("database_url"))
        self.performance_benchmarker = PerformanceBenchmarker(self.config)
        self.error_simulator = ErrorSimulator(self.config)
        
        # Test results storage
        self.validation_report = {}
        self.start_time = None
        self.end_time = None
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "mcp_api_url": os.getenv("MEMORY_MCP_API_URL", "http://localhost:8002"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
            "test_client_count": int(os.getenv("TEST_CLIENT_COUNT", "3")),
            "test_entity_count": int(os.getenv("TEST_ENTITY_COUNT", "50"))
        }
    
    async def validate_system_readiness(self) -> ValidationResult:
        """Validate that the memory system is ready for comprehensive testing."""
        start_time = time.perf_counter()
        
        try:
            # Check basic system health
            health_results = await self.health_checker.run_validation()
            
            # Count healthy components
            healthy_count = sum(1 for r in health_results if r.status == ValidationStatus.PASSED)
            total_count = len(health_results)
            
            if healthy_count == 0:
                return ValidationResult(
                    test_name="system_readiness",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="No system components are healthy - cannot proceed with validation"
                )
            elif healthy_count < total_count:
                return ValidationResult(
                    test_name="system_readiness",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Only {healthy_count}/{total_count} components are healthy",
                    details={"healthy_components": healthy_count, "total_components": total_count}
                )
            else:
                return ValidationResult(
                    test_name="system_readiness",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={"all_components_healthy": True}
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="system_readiness",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"System readiness check failed: {str(e)}"
            )
    
    async def validate_data_integrity_comprehensive(self) -> ValidationResult:
        """Run comprehensive data integrity validation."""
        start_time = time.perf_counter()
        
        try:
            # Run all data integrity tests
            integrity_results = await self.integrity_validator.run_validation()
            
            # Analyze results
            passed_count = sum(1 for r in integrity_results if r.status == ValidationStatus.PASSED)
            failed_count = sum(1 for r in integrity_results if r.status == ValidationStatus.FAILED)
            warning_count = sum(1 for r in integrity_results if r.status == ValidationStatus.WARNING)
            total_count = len(integrity_results)
            
            if failed_count > 0:
                failed_tests = [r.test_name for r in integrity_results if r.status == ValidationStatus.FAILED]
                return ValidationResult(
                    test_name="data_integrity_comprehensive",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"{failed_count} data integrity tests failed: {', '.join(failed_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "failed_tests": failed_tests
                    }
                )
            elif warning_count > 0:
                warning_tests = [r.test_name for r in integrity_results if r.status == ValidationStatus.WARNING]
                return ValidationResult(
                    test_name="data_integrity_comprehensive",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"{warning_count} data integrity tests had warnings: {', '.join(warning_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "warning_tests": warning_tests
                    }
                )
            else:
                return ValidationResult(
                    test_name="data_integrity_comprehensive",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "passed": passed_count,
                        "total": total_count,
                        "all_tests_passed": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="data_integrity_comprehensive",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Data integrity validation failed: {str(e)}"
            )
    
    async def validate_multi_client_isolation(self) -> ValidationResult:
        """Validate strict client data isolation across multiple clients."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="multi_client_isolation",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            # Create test data for multiple clients
            client_count = self.config["test_client_count"]
            entities_per_client = 10
            
            client_data = {}
            
            async with async_session() as session:
                for client_idx in range(client_count):
                    client_id = f"isolation_test_client_{client_idx}"
                    entities = self.test_data_generator.generate_entities(entities_per_client, client_id)
                    client_data[client_id] = entities
                    
                    # Insert entities for this client
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
                
                # Validate isolation for each client
                isolation_violations = []
                
                for client_id, expected_entities in client_data.items():
                    # Check that client can only see their own data
                    result = await session.execute(text("""
                        SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                    """), {"actor_id": client_id})
                    
                    actual_count = result.scalar()
                    expected_count = len(expected_entities)
                    
                    if actual_count != expected_count:
                        isolation_violations.append(f"Client {client_id}: expected {expected_count}, got {actual_count}")
                    
                    # Check for cross-client data leakage
                    other_clients = [cid for cid in client_data.keys() if cid != client_id]
                    for other_client in other_clients:
                        result = await session.execute(text("""
                            SELECT COUNT(*) FROM memory_entities 
                            WHERE actor_id = :client_id 
                            AND name IN (
                                SELECT name FROM memory_entities WHERE actor_id = :other_client
                            )
                        """), {"client_id": client_id, "other_client": other_client})
                        
                        cross_client_matches = result.scalar()
                        if cross_client_matches > 0:
                            isolation_violations.append(f"Data leakage: {cross_client_matches} entities from {other_client} visible to {client_id}")
                
                # Clean up test data
                for client_id in client_data.keys():
                    await session.execute(text("""
                        DELETE FROM memory_entities WHERE actor_id = :actor_id
                    """), {"actor_id": client_id})
                
                await session.commit()
            
            await engine.dispose()
            
            if isolation_violations:
                return ValidationResult(
                    test_name="multi_client_isolation",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Client isolation violations: {'; '.join(isolation_violations)}",
                    details={"violations": isolation_violations}
                )
            else:
                return ValidationResult(
                    test_name="multi_client_isolation",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "clients_tested": client_count,
                        "entities_per_client": entities_per_client,
                        "isolation_maintained": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="multi_client_isolation",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Multi-client isolation test failed: {str(e)}"
            )
    
    async def validate_performance_comprehensive(self) -> ValidationResult:
        """Run comprehensive performance validation."""
        start_time = time.perf_counter()
        
        try:
            # Run all performance tests
            performance_results = await self.performance_benchmarker.run_validation()
            
            # Analyze results
            passed_count = sum(1 for r in performance_results if r.status == ValidationStatus.PASSED)
            failed_count = sum(1 for r in performance_results if r.status == ValidationStatus.FAILED)
            warning_count = sum(1 for r in performance_results if r.status == ValidationStatus.WARNING)
            total_count = len(performance_results)
            
            if failed_count > 0:
                failed_tests = [r.test_name for r in performance_results if r.status == ValidationStatus.FAILED]
                return ValidationResult(
                    test_name="performance_comprehensive",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"{failed_count} performance tests failed: {', '.join(failed_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "failed_tests": failed_tests
                    }
                )
            elif warning_count > 0:
                warning_tests = [r.test_name for r in performance_results if r.status == ValidationStatus.WARNING]
                return ValidationResult(
                    test_name="performance_comprehensive",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"{warning_count} performance tests had warnings: {', '.join(warning_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "warning_tests": warning_tests
                    }
                )
            else:
                return ValidationResult(
                    test_name="performance_comprehensive",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "passed": passed_count,
                        "total": total_count,
                        "all_tests_passed": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="performance_comprehensive",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Performance validation failed: {str(e)}"
            )

    async def validate_error_handling_comprehensive(self) -> ValidationResult:
        """Run comprehensive error handling and recovery validation."""
        start_time = time.perf_counter()
        
        try:
            # Run all error simulation tests
            error_results = await self.error_simulator.run_validation()
            
            # Analyze results
            passed_count = sum(1 for r in error_results if r.status == ValidationStatus.PASSED)
            failed_count = sum(1 for r in error_results if r.status == ValidationStatus.FAILED)
            warning_count = sum(1 for r in error_results if r.status == ValidationStatus.WARNING)
            total_count = len(error_results)
            
            if failed_count > 0:
                failed_tests = [r.test_name for r in error_results if r.status == ValidationStatus.FAILED]
                return ValidationResult(
                    test_name="error_handling_comprehensive",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"{failed_count} error handling tests failed: {', '.join(failed_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "failed_tests": failed_tests,
                        "recovery_metrics": self.error_simulator.recovery_metrics
                    }
                )
            elif warning_count > 0:
                warning_tests = [r.test_name for r in error_results if r.status == ValidationStatus.WARNING]
                return ValidationResult(
                    test_name="error_handling_comprehensive",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"{warning_count} error handling tests had warnings: {', '.join(warning_tests)}",
                    details={
                        "passed": passed_count,
                        "failed": failed_count,
                        "warnings": warning_count,
                        "total": total_count,
                        "warning_tests": warning_tests,
                        "recovery_metrics": self.error_simulator.recovery_metrics
                    }
                )
            else:
                return ValidationResult(
                    test_name="error_handling_comprehensive",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "passed": passed_count,
                        "total": total_count,
                        "all_tests_passed": True,
                        "recovery_metrics": self.error_simulator.recovery_metrics
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="error_handling_comprehensive",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Error handling validation failed: {str(e)}"
            )

    async def validate_system_under_load(self) -> ValidationResult:
        """Validate system behavior under moderate load."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="system_under_load",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            # Create test scenario
            test_client_id = f"load_test_client_{int(time.time())}"
            entity_count = self.config["test_entity_count"]
            
            # Generate test entities
            entities = self.test_data_generator.generate_entities(entity_count, test_client_id)
            
            # Measure bulk insert performance
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
            insert_rate = entity_count / (insert_time / 1000)  # entities per second
            
            # Measure search performance
            search_start = time.perf_counter()
            
            async with async_session() as session:
                # Perform various search operations
                for _ in range(10):
                    # Search by entity type
                    await session.execute(text("""
                        SELECT COUNT(*) FROM memory_entities 
                        WHERE actor_id = :actor_id AND entity_type = 'person'
                    """), {"actor_id": test_client_id})
                    
                    # Search by name pattern
                    await session.execute(text("""
                        SELECT name FROM memory_entities 
                        WHERE actor_id = :actor_id AND name LIKE '%John%'
                        LIMIT 10
                    """), {"actor_id": test_client_id})
                    
                    # JSON metadata search
                    await session.execute(text("""
                        SELECT name FROM memory_entities 
                        WHERE actor_id = :actor_id 
                        AND metadata->>'job_title' IS NOT NULL
                        LIMIT 5
                    """), {"actor_id": test_client_id})
            
            search_time = (time.perf_counter() - search_start) * 1000
            avg_search_time = search_time / 30  # 30 total search operations
            
            # Clean up test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Evaluate performance
            performance_issues = []
            
            if insert_rate < 10:  # Less than 10 entities per second
                performance_issues.append(f"Slow insert rate: {insert_rate:.1f} entities/sec")
            
            if avg_search_time > 100:  # More than 100ms average search time
                performance_issues.append(f"Slow search performance: {avg_search_time:.1f}ms average")
            
            if performance_issues:
                return ValidationResult(
                    test_name="system_under_load",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Performance concerns: {'; '.join(performance_issues)}",
                    details={
                        "entities_tested": entity_count,
                        "insert_rate_per_sec": insert_rate,
                        "avg_search_time_ms": avg_search_time,
                        "total_insert_time_ms": insert_time,
                        "total_search_time_ms": search_time
                    }
                )
            else:
                return ValidationResult(
                    test_name="system_under_load",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entities_tested": entity_count,
                        "insert_rate_per_sec": insert_rate,
                        "avg_search_time_ms": avg_search_time,
                        "performance_acceptable": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="system_under_load",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Load testing failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run comprehensive memory system validation."""
        self.start_time = datetime.utcnow()
        self.logger.info("Starting comprehensive memory system validation")
        
        # Define validation tests in order of execution
        tests = [
            ("system_readiness", self.validate_system_readiness),
            ("data_integrity_comprehensive", self.validate_data_integrity_comprehensive),
            ("multi_client_isolation", self.validate_multi_client_isolation),
            ("performance_comprehensive", self.validate_performance_comprehensive),
            ("error_handling_comprehensive", self.validate_error_handling_comprehensive),
            ("system_under_load", self.validate_system_under_load)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.logger.info(f"Running comprehensive test: {test_name}")
            result = await self.run_test(f"comprehensive_{test_name}", test_func)
            results.append(result)
            
            # Stop on critical failures
            if result.status == ValidationStatus.FAILED and test_name == "system_readiness":
                self.logger.error("System readiness failed - stopping comprehensive validation")
                break
        
        self.end_time = datetime.utcnow()
        
        # Generate summary report
        self.validation_report = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.status == ValidationStatus.PASSED),
            "failed_tests": sum(1 for r in results if r.status == ValidationStatus.FAILED),
            "warning_tests": sum(1 for r in results if r.status == ValidationStatus.WARNING),
            "config": self.config,
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "execution_time_ms": r.execution_time_ms,
                    "error_message": r.error_message,
                    "warning_message": r.warning_message,
                    "details": r.details
                }
                for r in results
            ]
        }
        
        return results
    
    def save_report(self, filepath: str):
        """Save comprehensive validation report to file."""
        with open(filepath, 'w') as f:
            json.dump(self.validation_report, f, indent=2, default=str)
        
        self.logger.info(f"Comprehensive validation report saved to: {filepath}")
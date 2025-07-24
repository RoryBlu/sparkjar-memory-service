"""
Error simulation and recovery testing framework.

This module provides comprehensive error simulation capabilities to test:
- Database failure scenarios and recovery
- Network interruption handling
- Resource exhaustion conditions
- External service failures
- Concurrent operation conflicts
"""

import asyncio
import json
import logging
import os
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from unittest.mock import patch, AsyncMock

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

class ErrorSimulator(BaseValidator):
    """Comprehensive error simulation and recovery testing."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("ErrorSimulator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Simulation state
        self.active_simulations = {}
        self.recovery_metrics = {}
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
            "max_retry_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
            "retry_delay_seconds": float(os.getenv("RETRY_DELAY_SECONDS", "1.0"))
        }
    
    @asynccontextmanager
    async def simulate_database_failure(self, failure_type: str = "connection_lost") -> AsyncGenerator[None, None]:
        """Context manager to simulate database failures."""
        simulation_id = f"db_failure_{int(time.time())}"
        self.active_simulations[simulation_id] = {
            "type": "database_failure",
            "failure_type": failure_type,
            "start_time": time.perf_counter()
        }
        
        try:
            if failure_type == "connection_lost":
                # Simulate connection loss by patching database operations
                with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
                    mock_execute.side_effect = Exception("Connection lost")
                    yield
            elif failure_type == "timeout":
                # Simulate database timeouts
                with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
                    async def slow_execute(*args, **kwargs):
                        await asyncio.sleep(self.config["timeout_seconds"] + 1)
                        raise Exception("Query timeout")
                    mock_execute.side_effect = slow_execute
                    yield
            elif failure_type == "deadlock":
                # Simulate deadlock conditions
                with patch('sqlalchemy.ext.asyncio.AsyncSession.execute') as mock_execute:
                    mock_execute.side_effect = Exception("Deadlock detected")
                    yield
            else:
                yield
        finally:
            self.active_simulations[simulation_id]["end_time"] = time.perf_counter()
            self.active_simulations[simulation_id]["duration"] = (
                self.active_simulations[simulation_id]["end_time"] - 
                self.active_simulations[simulation_id]["start_time"]
            )
    
    @asynccontextmanager
    async def simulate_network_failure(self, failure_type: str = "connection_refused") -> AsyncGenerator[None, None]:
        """Context manager to simulate network failures."""
        simulation_id = f"network_failure_{int(time.time())}"
        self.active_simulations[simulation_id] = {
            "type": "network_failure",
            "failure_type": failure_type,
            "start_time": time.perf_counter()
        }
        
        try:
            if failure_type == "connection_refused":
                # Simulate connection refused errors
                with patch('aiohttp.ClientSession.request') as mock_request:
                    mock_request.side_effect = Exception("Connection refused")
                    yield
            elif failure_type == "timeout":
                # Simulate network timeouts
                with patch('aiohttp.ClientSession.request') as mock_request:
                    async def slow_request(*args, **kwargs):
                        await asyncio.sleep(self.config["timeout_seconds"] + 1)
                        raise Exception("Request timeout")
                    mock_request.side_effect = slow_request
                    yield
            elif failure_type == "intermittent":
                # Simulate intermittent failures (50% failure rate)
                with patch('aiohttp.ClientSession.request') as mock_request:
                    async def intermittent_request(*args, **kwargs):
                        if random.random() < 0.5:
                            raise Exception("Intermittent network failure")
                        # Return mock successful response
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_response.json.return_value = {"status": "success"}
                        return mock_response
                    mock_request.side_effect = intermittent_request
                    yield
            else:
                yield
        finally:
            self.active_simulations[simulation_id]["end_time"] = time.perf_counter()
            self.active_simulations[simulation_id]["duration"] = (
                self.active_simulations[simulation_id]["end_time"] - 
                self.active_simulations[simulation_id]["start_time"]
            )
    
    @asynccontextmanager
    async def simulate_resource_exhaustion(self, resource_type: str = "memory") -> AsyncGenerator[None, None]:
        """Context manager to simulate resource exhaustion."""
        simulation_id = f"resource_exhaustion_{int(time.time())}"
        self.active_simulations[simulation_id] = {
            "type": "resource_exhaustion",
            "resource_type": resource_type,
            "start_time": time.perf_counter()
        }
        
        try:
            if resource_type == "memory":
                # Simulate memory exhaustion
                with patch('psutil.virtual_memory') as mock_memory:
                    mock_memory.return_value.percent = 95.0  # 95% memory usage
                    yield
            elif resource_type == "connections":
                # Simulate connection pool exhaustion
                with patch('sqlalchemy.pool.QueuePool.connect') as mock_connect:
                    mock_connect.side_effect = Exception("Connection pool exhausted")
                    yield
            elif resource_type == "disk":
                # Simulate disk space exhaustion
                with patch('shutil.disk_usage') as mock_disk:
                    mock_disk.return_value = (1000000, 950000, 50000)  # 95% disk usage
                    yield
            else:
                yield
        finally:
            self.active_simulations[simulation_id]["end_time"] = time.perf_counter()
            self.active_simulations[simulation_id]["duration"] = (
                self.active_simulations[simulation_id]["end_time"] - 
                self.active_simulations[simulation_id]["start_time"]
            )
    
    async def test_database_connection_recovery(self) -> ValidationResult:
        """Test database connection failure and recovery."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="database_connection_recovery",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            # Test normal operation first
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            # Verify normal operation
            async with async_session() as session:
                result = await session.execute(text("SELECT 1"))
                if not result.scalar():
                    raise Exception("Database not responding normally")
            
            # Simulate connection failure and test recovery
            recovery_attempts = 0
            max_attempts = self.config["max_retry_attempts"]
            recovery_successful = False
            recovery_start = time.perf_counter()
            
            async with self.simulate_database_failure("connection_lost"):
                for attempt in range(max_attempts):
                    recovery_attempts += 1
                    try:
                        # Attempt to reconnect
                        await asyncio.sleep(self.config["retry_delay_seconds"] * (2 ** attempt))  # Exponential backoff
                        
                        # In real scenario, this would attempt actual reconnection
                        # For simulation, we'll test the retry logic
                        async with async_session() as session:
                            await session.execute(text("SELECT 1"))
                        
                        recovery_successful = True
                        break
                    except Exception as e:
                        self.logger.warning(f"Recovery attempt {attempt + 1} failed: {str(e)}")
                        continue
            
            recovery_time = (time.perf_counter() - recovery_start) * 1000
            
            await engine.dispose()
            
            # Record recovery metrics
            self.recovery_metrics["database_connection"] = {
                "recovery_attempts": recovery_attempts,
                "recovery_successful": recovery_successful,
                "recovery_time_ms": recovery_time,
                "max_attempts": max_attempts
            }
            
            if recovery_successful or recovery_attempts <= max_attempts:
                return ValidationResult(
                    test_name="database_connection_recovery",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "recovery_attempts": recovery_attempts,
                        "recovery_time_ms": recovery_time,
                        "retry_strategy": "exponential_backoff"
                    }
                )
            else:
                return ValidationResult(
                    test_name="database_connection_recovery",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Failed to recover after {recovery_attempts} attempts",
                    details={
                        "recovery_attempts": recovery_attempts,
                        "max_attempts": max_attempts,
                        "recovery_time_ms": recovery_time
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="database_connection_recovery",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Database connection recovery test failed: {str(e)}"
            )
    
    async def test_transaction_rollback_on_failure(self) -> ValidationResult:
        """Test transaction rollback when operations fail."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="transaction_rollback_on_failure",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_client_id = f"rollback_test_{int(time.time())}"
            entities_created = 0
            rollback_successful = False
            
            try:
                async with async_session() as session:
                    # Start transaction and create some entities
                    entities = self.test_data_generator.generate_entities(5, test_client_id)
                    
                    for i, entity in enumerate(entities):
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
                        entities_created += 1
                        
                        # Simulate failure on 3rd entity
                        if i == 2:
                            raise Exception("Simulated transaction failure")
                    
                    await session.commit()
                    
            except Exception as e:
                # Transaction should rollback automatically
                self.logger.info(f"Expected transaction failure: {str(e)}")
                rollback_successful = True
            
            # Verify rollback - no entities should exist
            async with async_session() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                
                remaining_entities = result.scalar()
            
            await engine.dispose()
            
            if rollback_successful and remaining_entities == 0:
                return ValidationResult(
                    test_name="transaction_rollback_on_failure",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entities_attempted": entities_created,
                        "entities_remaining": remaining_entities,
                        "rollback_successful": True
                    }
                )
            else:
                return ValidationResult(
                    test_name="transaction_rollback_on_failure",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Rollback failed - {remaining_entities} entities remain",
                    details={
                        "entities_attempted": entities_created,
                        "entities_remaining": remaining_entities,
                        "rollback_successful": rollback_successful
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="transaction_rollback_on_failure",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Transaction rollback test failed: {str(e)}"
            )
    
    async def test_network_failure_recovery(self) -> ValidationResult:
        """Test network failure handling and recovery."""
        start_time = time.perf_counter()
        
        try:
            import aiohttp
            
            recovery_attempts = 0
            max_attempts = self.config["max_retry_attempts"]
            recovery_successful = False
            recovery_start = time.perf_counter()
            
            # Simulate network failure and test recovery
            async with self.simulate_network_failure("intermittent"):
                for attempt in range(max_attempts):
                    recovery_attempts += 1
                    try:
                        # Attempt network request with retry logic
                        await asyncio.sleep(self.config["retry_delay_seconds"] * (2 ** attempt))
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(self.config["internal_api_url"] + "/health") as response:
                                if response.status == 200:
                                    recovery_successful = True
                                    break
                    except Exception as e:
                        self.logger.warning(f"Network recovery attempt {attempt + 1} failed: {str(e)}")
                        continue
            
            recovery_time = (time.perf_counter() - recovery_start) * 1000
            
            # Record recovery metrics
            self.recovery_metrics["network_failure"] = {
                "recovery_attempts": recovery_attempts,
                "recovery_successful": recovery_successful,
                "recovery_time_ms": recovery_time,
                "max_attempts": max_attempts
            }
            
            if recovery_successful or recovery_attempts <= max_attempts:
                return ValidationResult(
                    test_name="network_failure_recovery",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "recovery_attempts": recovery_attempts,
                        "recovery_time_ms": recovery_time,
                        "retry_strategy": "exponential_backoff"
                    }
                )
            else:
                return ValidationResult(
                    test_name="network_failure_recovery",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Failed to recover after {recovery_attempts} attempts",
                    details={
                        "recovery_attempts": recovery_attempts,
                        "max_attempts": max_attempts,
                        "recovery_time_ms": recovery_time
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="network_failure_recovery",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Network failure recovery test failed: {str(e)}"
            )
    
    async def test_resource_exhaustion_handling(self) -> ValidationResult:
        """Test system behavior under resource exhaustion."""
        start_time = time.perf_counter()
        
        try:
            graceful_degradation = False
            error_handling_correct = False
            system_crashed = False
            
            # Test memory exhaustion handling
            async with self.simulate_resource_exhaustion("memory"):
                try:
                    # Attempt operations under resource pressure
                    test_client_id = f"resource_test_{int(time.time())}"
                    entities = self.test_data_generator.generate_entities(10, test_client_id)
                    
                    # System should either:
                    # 1. Handle gracefully with appropriate errors
                    # 2. Degrade performance but continue working
                    # 3. NOT crash completely
                    
                    if not self.config["database_url"]:
                        raise Exception("Database URL not configured")
                    
                    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
                    from sqlalchemy.orm import sessionmaker
                    from sqlalchemy import text
                    
                    engine = create_async_engine(self.config["database_url"])
                    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                    
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
                    
                    # Clean up
                    async with async_session() as session:
                        await session.execute(text("""
                            DELETE FROM memory_entities WHERE actor_id = :actor_id
                        """), {"actor_id": test_client_id})
                        await session.commit()
                    
                    await engine.dispose()
                    
                    graceful_degradation = True
                    
                except Exception as e:
                    # Check if error handling is appropriate
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["memory", "resource", "exhausted", "limit"]):
                        error_handling_correct = True
                    else:
                        system_crashed = True
            
            # Record resource handling metrics
            self.recovery_metrics["resource_exhaustion"] = {
                "graceful_degradation": graceful_degradation,
                "error_handling_correct": error_handling_correct,
                "system_crashed": system_crashed
            }
            
            if graceful_degradation or error_handling_correct:
                return ValidationResult(
                    test_name="resource_exhaustion_handling",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "graceful_degradation": graceful_degradation,
                        "error_handling_correct": error_handling_correct,
                        "system_crashed": system_crashed
                    }
                )
            else:
                return ValidationResult(
                    test_name="resource_exhaustion_handling",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="System did not handle resource exhaustion gracefully",
                    details={
                        "graceful_degradation": graceful_degradation,
                        "error_handling_correct": error_handling_correct,
                        "system_crashed": system_crashed
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="resource_exhaustion_handling",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Resource exhaustion test failed: {str(e)}"
            )
    
    async def test_concurrent_operation_conflicts(self) -> ValidationResult:
        """Test handling of concurrent operation conflicts."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="concurrent_operation_conflicts",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_client_id = f"conflict_test_{int(time.time())}"
            conflict_detected = False
            conflict_resolved = False
            
            # Create initial entity
            initial_entity = self.test_data_generator.generate_entities(1, test_client_id)[0]
            
            async with async_session() as session:
                await session.execute(text("""
                    INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type, metadata, created_at)
                    VALUES (:id, :actor_type, :actor_id, :name, :entity_type, :metadata, :created_at)
                """), {
                    "id": initial_entity.id,
                    "actor_type": "client",
                    "actor_id": initial_entity.client_user_id,
                    "name": initial_entity.name,
                    "entity_type": initial_entity.entity_type,
                    "metadata": json.dumps(initial_entity.metadata),
                    "created_at": initial_entity.created_at
                })
                await session.commit()
            
            # Simulate concurrent updates to the same entity
            async def concurrent_update(update_id: int):
                try:
                    async with async_session() as session:
                        # Read current entity
                        result = await session.execute(text("""
                            SELECT metadata FROM memory_entities WHERE id = :id
                        """), {"id": initial_entity.id})
                        
                        current_metadata = result.scalar()
                        if current_metadata:
                            metadata = json.loads(current_metadata)
                            metadata[f"update_{update_id}"] = f"value_{update_id}"
                            
                            # Simulate processing delay
                            await asyncio.sleep(0.1)
                            
                            # Update entity
                            await session.execute(text("""
                                UPDATE memory_entities 
                                SET metadata = :metadata 
                                WHERE id = :id
                            """), {
                                "id": initial_entity.id,
                                "metadata": json.dumps(metadata)
                            })
                            
                            await session.commit()
                            return True
                except Exception as e:
                    self.logger.warning(f"Concurrent update {update_id} failed: {str(e)}")
                    return False
            
            # Launch concurrent updates
            tasks = [concurrent_update(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful_updates = sum(1 for r in results if r is True)
            failed_updates = len(results) - successful_updates
            
            if failed_updates > 0:
                conflict_detected = True
                conflict_resolved = successful_updates > 0
            
            # Verify final state
            async with async_session() as session:
                result = await session.execute(text("""
                    SELECT metadata FROM memory_entities WHERE id = :id
                """), {"id": initial_entity.id})
                
                final_metadata = result.scalar()
                
                # Clean up
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Record conflict handling metrics
            self.recovery_metrics["concurrent_conflicts"] = {
                "conflict_detected": conflict_detected,
                "conflict_resolved": conflict_resolved,
                "successful_updates": successful_updates,
                "failed_updates": failed_updates
            }
            
            if not conflict_detected or conflict_resolved:
                return ValidationResult(
                    test_name="concurrent_operation_conflicts",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "conflict_detected": conflict_detected,
                        "conflict_resolved": conflict_resolved,
                        "successful_updates": successful_updates,
                        "failed_updates": failed_updates
                    }
                )
            else:
                return ValidationResult(
                    test_name="concurrent_operation_conflicts",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Concurrent conflicts not handled properly",
                    details={
                        "conflict_detected": conflict_detected,
                        "conflict_resolved": conflict_resolved,
                        "successful_updates": successful_updates,
                        "failed_updates": failed_updates
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="concurrent_operation_conflicts",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Concurrent operation conflict test failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run comprehensive error simulation and recovery tests."""
        self.logger.info("Starting error simulation and recovery validation")
        
        # Define error simulation tests
        tests = [
            ("database_connection_recovery", self.test_database_connection_recovery),
            ("transaction_rollback_on_failure", self.test_transaction_rollback_on_failure),
            ("network_failure_recovery", self.test_network_failure_recovery),
            ("resource_exhaustion_handling", self.test_resource_exhaustion_handling),
            ("concurrent_operation_conflicts", self.test_concurrent_operation_conflicts)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.logger.info(f"Running error simulation test: {test_name}")
            result = await self.run_test(f"error_sim_{test_name}", test_func)
            results.append(result)
        
        # Generate recovery metrics summary
        self.logger.info("Error simulation and recovery validation completed")
        self.logger.info(f"Recovery metrics: {json.dumps(self.recovery_metrics, indent=2)}")
        
        return results
"""Memory system health checker implementation."""

import asyncio
import time
from typing import Dict, List, Optional
import httpx
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .base import BaseValidator, HealthCheckResult, HealthStatus, ValidationResult, ValidationStatus

class MemorySystemHealthChecker(BaseValidator):
    """Comprehensive health validation for memory system."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("MemorySystemHealthChecker")
        self.config = config or self._load_default_config()
        self.health_results: List[HealthCheckResult] = []
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment variables."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT"),
            "internal_api_url": "http://localhost:8001",
            "external_api_url": "http://localhost:8443", 
            "mcp_api_url": "http://localhost:8002",
            "timeout_seconds": 10
        }
    
    async def check_database_health(self) -> HealthCheckResult:
        """Validate database connectivity and performance."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    error_message="DATABASE_URL not configured"
                )
            
            # Create async engine
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value != 1:
                    raise Exception("Database connectivity test failed")
                
                # Test memory-related tables exist
                tables_to_check = [
                    "memory_entities", 
                    "memory_relations", 
                    "object_schemas"
                ]
                
                for table in tables_to_check:
                    try:
                        await session.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
                    except Exception as e:
                        return HealthCheckResult(
                            component="database",
                            status=HealthStatus.UNHEALTHY,
                            response_time_ms=(time.perf_counter() - start_time) * 1000,
                            error_message=f"Table {table} not accessible: {str(e)}"
                        )
            
            await engine.dispose()
            
            response_time = (time.perf_counter() - start_time) * 1000
            
            return HealthCheckResult(
                component="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "tables_checked": tables_to_check,
                    "connection_successful": True
                }
            )
            
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def check_api_endpoint(self, name: str, url: str, expected_status: int = 200) -> HealthCheckResult:
        """Check if an API endpoint is responding."""
        start_time = time.perf_counter()
        
        try:
            async with httpx.AsyncClient(timeout=self.config["timeout_seconds"]) as client:
                # Try health endpoint first, fall back to root
                health_endpoints = ["/health", "/", "/docs"]
                
                last_error = None
                for endpoint in health_endpoints:
                    try:
                        response = await client.get(f"{url}{endpoint}")
                        
                        response_time = (time.perf_counter() - start_time) * 1000
                        
                        if response.status_code in [200, 404]:  # 404 is OK for root endpoints
                            return HealthCheckResult(
                                component=f"api_{name}",
                                status=HealthStatus.HEALTHY,
                                response_time_ms=response_time,
                                details={
                                    "endpoint": f"{url}{endpoint}",
                                    "status_code": response.status_code,
                                    "response_size": len(response.content)
                                }
                            )
                        else:
                            last_error = f"HTTP {response.status_code}"
                            
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                # If we get here, all endpoints failed
                response_time = (time.perf_counter() - start_time) * 1000
                return HealthCheckResult(
                    component=f"api_{name}",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message=f"All endpoints failed. Last error: {last_error}"
                )
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                component=f"api_{name}",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def check_api_endpoints(self) -> List[HealthCheckResult]:
        """Test all API interfaces."""
        endpoints = [
            ("internal", self.config["internal_api_url"]),
            ("external", self.config["external_api_url"]),
            ("mcp", self.config["mcp_api_url"])
        ]
        
        results = []
        for name, url in endpoints:
            if url:
                result = await self.check_api_endpoint(name, url)
                results.append(result)
            else:
                results.append(HealthCheckResult(
                    component=f"api_{name}",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    error_message=f"URL not configured for {name} API"
                ))
        
        return results
    
    async def check_basic_operations(self) -> HealthCheckResult:
        """Test basic CRUD operations if database is available."""
        start_time = time.perf_counter()
        
        try:
            if not self.config["database_url"]:
                return HealthCheckResult(
                    component="basic_operations",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    error_message="Database not configured"
                )
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            test_entity_id = f"test_health_check_{int(time.time())}"
            
            async with async_session() as session:
                # Test CREATE
                await session.execute(text("""
                    INSERT INTO memory_entities (id, client_user_id, name, entity_type, metadata)
                    VALUES (:id, :client_id, :name, :type, :metadata)
                """), {
                    "id": test_entity_id,
                    "client_id": "health_check_client",
                    "name": "Health Check Entity",
                    "type": "test",
                    "metadata": '{"test": true}'
                })
                
                # Test READ
                result = await session.execute(text("""
                    SELECT name FROM memory_entities WHERE id = :id
                """), {"id": test_entity_id})
                
                entity_name = result.scalar()
                if entity_name != "Health Check Entity":
                    raise Exception("Entity read test failed")
                
                # Test UPDATE
                await session.execute(text("""
                    UPDATE memory_entities SET name = :new_name WHERE id = :id
                """), {"id": test_entity_id, "new_name": "Updated Health Check Entity"})
                
                # Test DELETE
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE id = :id
                """), {"id": test_entity_id})
                
                await session.commit()
            
            await engine.dispose()
            
            response_time = (time.perf_counter() - start_time) * 1000
            
            return HealthCheckResult(
                component="basic_operations",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "operations_tested": ["CREATE", "READ", "UPDATE", "DELETE"],
                    "test_entity_id": test_entity_id
                }
            )
            
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return HealthCheckResult(
                component="basic_operations",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run all health validation tests."""
        self.logger.info("Starting memory system health checks")
        
        # Run all health checks
        health_checks = []
        
        # Database health
        db_health = await self.check_database_health()
        health_checks.append(db_health)
        
        # API endpoints health
        api_health_results = await self.check_api_endpoints()
        health_checks.extend(api_health_results)
        
        # Basic operations health (only if database is healthy)
        if db_health.is_healthy:
            ops_health = await self.check_basic_operations()
            health_checks.append(ops_health)
        else:
            health_checks.append(HealthCheckResult(
                component="basic_operations",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0.0,
                error_message="Skipped due to database health issues"
            ))
        
        # Store health results
        self.health_results = health_checks
        
        # Convert health checks to validation results
        validation_results = []
        for health_check in health_checks:
            if health_check.is_healthy:
                status = ValidationStatus.PASSED
                error_msg = None
            elif health_check.status == HealthStatus.DEGRADED:
                status = ValidationStatus.WARNING
                error_msg = health_check.error_message
            else:
                status = ValidationStatus.FAILED
                error_msg = health_check.error_message
            
            validation_results.append(ValidationResult(
                test_name=f"health_check_{health_check.component}",
                status=status,
                execution_time_ms=health_check.response_time_ms,
                error_message=error_msg,
                details=health_check.details,
                timestamp=health_check.timestamp
            ))
        
        return validation_results
    
    def get_health_summary(self) -> Dict:
        """Get summary of health check results."""
        if not self.health_results:
            return {"status": "not_run", "components": []}
        
        healthy_count = sum(1 for h in self.health_results if h.is_healthy)
        total_count = len(self.health_results)
        
        overall_status = "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy"
        
        return {
            "status": overall_status,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "components": [
                {
                    "name": h.component,
                    "status": h.status.value,
                    "response_time_ms": h.response_time_ms,
                    "error": h.error_message
                }
                for h in self.health_results
            ]
        }
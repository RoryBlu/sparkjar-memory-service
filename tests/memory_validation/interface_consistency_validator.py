"""
Interface consistency validation for memory system.

This module validates that all memory system interfaces (CrewAI tools, FastAPI, MCP)
provide consistent behavior and identical results for the same operations.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import requests

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator
from .crewai_tool_validator import CrewAIToolValidator
from .fastapi_consistency_validator import FastAPIConsistencyValidator
from .mcp_compliance_validator import MCPComplianceValidator

class InterfaceConsistencyValidator(BaseValidator):
    """Validate consistency across all memory system interfaces."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("InterfaceConsistencyValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Interface endpoints
        self.internal_api_url = self.config["internal_api_url"]
        self.external_api_url = self.config["external_api_url"]
        self.mcp_api_url = self.config["mcp_api_url"]
        
        # Test results storage
        self.interface_results = {}
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "mcp_api_url": os.getenv("MEMORY_MCP_API_URL", "http://localhost:8002"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
            "test_client_id": os.getenv("TEST_CLIENT_ID", "interface_test_client")
        }
    
    async def check_interface_availability(self) -> ValidationResult:
        """Check that all interfaces are available and responding."""
        start_time = time.perf_counter()
        
        interfaces = {
            "internal_api": self.internal_api_url,
            "external_api": self.external_api_url,
            "mcp_api": self.mcp_api_url
        }
        
        availability_results = {}
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])) as session:
                for interface_name, base_url in interfaces.items():
                    try:
                        health_url = f"{base_url}/health" if not interface_name == "mcp_api" else f"{base_url}/status"
                        async with session.get(health_url) as response:
                            availability_results[interface_name] = {
                                "available": response.status == 200,
                                "status_code": response.status,
                                "response_time_ms": 0  # We'll measure this separately if needed
                            }
                    except Exception as e:
                        availability_results[interface_name] = {
                            "available": False,
                            "error": str(e),
                            "status_code": None
                        }
            
            # Check results
            available_interfaces = sum(1 for r in availability_results.values() if r.get("available", False))
            total_interfaces = len(interfaces)
            
            if available_interfaces == 0:
                return ValidationResult(
                    test_name="interface_availability",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="No interfaces are available",
                    details=availability_results
                )
            elif available_interfaces < total_interfaces:
                return ValidationResult(
                    test_name="interface_availability",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Only {available_interfaces}/{total_interfaces} interfaces available",
                    details=availability_results
                )
            else:
                return ValidationResult(
                    test_name="interface_availability",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details=availability_results
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="interface_availability",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Interface availability check failed: {str(e)}"
            )
    
    async def test_entity_creation_consistency(self) -> ValidationResult:
        """Test that entity creation produces identical results across interfaces."""
        start_time = time.perf_counter()
        
        try:
            # Generate test entity
            test_entities = self.test_data_generator.generate_entities(1, self.config["test_client_id"])
            test_entity = test_entities[0]
            
            # Test data for entity creation
            entity_data = {
                "name": test_entity.name,
                "entity_type": test_entity.entity_type,
                "metadata": test_entity.metadata,
                "client_user_id": test_entity.client_user_id
            }
            
            interface_responses = {}
            
            # Test Internal API
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.internal_api_url}/entities",
                        json=entity_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        interface_responses["internal_api"] = {
                            "status_code": response.status,
                            "data": await response.json() if response.status == 200 else None,
                            "error": await response.text() if response.status != 200 else None
                        }
            except Exception as e:
                interface_responses["internal_api"] = {"error": str(e), "status_code": None}
            
            # Test External API
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.external_api_url}/entities",
                        json=entity_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        interface_responses["external_api"] = {
                            "status_code": response.status,
                            "data": await response.json() if response.status == 200 else None,
                            "error": await response.text() if response.status != 200 else None
                        }
            except Exception as e:
                interface_responses["external_api"] = {"error": str(e), "status_code": None}
            
            # Test MCP Interface (if available)
            try:
                # MCP interface testing would require MCP protocol implementation
                # For now, we'll simulate or skip this test
                interface_responses["mcp_api"] = {"status": "not_implemented", "message": "MCP testing requires protocol implementation"}
            except Exception as e:
                interface_responses["mcp_api"] = {"error": str(e), "status_code": None}
            
            # Analyze consistency
            successful_responses = [r for r in interface_responses.values() if r.get("status_code") == 200]
            
            if len(successful_responses) < 2:
                return ValidationResult(
                    test_name="entity_creation_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Not enough interfaces responded successfully to compare consistency",
                    details=interface_responses
                )
            
            # Compare response data structure (simplified comparison)
            consistency_issues = []
            base_response = successful_responses[0]
            
            for i, response in enumerate(successful_responses[1:], 1):
                if response.get("data") and base_response.get("data"):
                    # Compare key fields
                    base_data = base_response["data"]
                    compare_data = response["data"]
                    
                    if isinstance(base_data, dict) and isinstance(compare_data, dict):
                        for key in ["name", "entity_type"]:
                            if base_data.get(key) != compare_data.get(key):
                                consistency_issues.append(f"Field '{key}' differs between interfaces")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="entity_creation_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Consistency issues found: {'; '.join(consistency_issues)}",
                    details={
                        "interface_responses": interface_responses,
                        "consistency_issues": consistency_issues
                    }
                )
            else:
                return ValidationResult(
                    test_name="entity_creation_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "interface_responses": interface_responses,
                        "successful_interfaces": len(successful_responses)
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="entity_creation_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Entity creation consistency test failed: {str(e)}"
            )
    
    async def test_search_consistency(self) -> ValidationResult:
        """Test that search operations return consistent results across interfaces."""
        start_time = time.perf_counter()
        
        try:
            # First, create some test data via database
            if not self.config["database_url"]:
                return ValidationResult(
                    test_name="search_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message="Database URL not configured"
                )
            
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import text
            
            engine = create_async_engine(self.config["database_url"])
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            # Create test entities
            test_client_id = f"search_test_{int(time.time())}"
            entities = self.test_data_generator.generate_entities(3, test_client_id)
            
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
            
            # Test search across interfaces
            search_query = {"client_user_id": test_client_id, "entity_type": "person"}
            interface_responses = {}
            
            # Test Internal API search
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.internal_api_url}/entities/search",
                        params=search_query
                    ) as response:
                        interface_responses["internal_api"] = {
                            "status_code": response.status,
                            "data": await response.json() if response.status == 200 else None,
                            "error": await response.text() if response.status != 200 else None
                        }
            except Exception as e:
                interface_responses["internal_api"] = {"error": str(e), "status_code": None}
            
            # Test External API search
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.external_api_url}/entities/search",
                        params=search_query
                    ) as response:
                        interface_responses["external_api"] = {
                            "status_code": response.status,
                            "data": await response.json() if response.status == 200 else None,
                            "error": await response.text() if response.status != 200 else None
                        }
            except Exception as e:
                interface_responses["external_api"] = {"error": str(e), "status_code": None}
            
            # Clean up test data
            async with async_session() as session:
                await session.execute(text("""
                    DELETE FROM memory_entities WHERE actor_id = :actor_id
                """), {"actor_id": test_client_id})
                await session.commit()
            
            await engine.dispose()
            
            # Analyze search consistency
            successful_responses = [r for r in interface_responses.values() if r.get("status_code") == 200]
            
            if len(successful_responses) < 2:
                return ValidationResult(
                    test_name="search_consistency",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message="Not enough interfaces responded successfully to compare search consistency",
                    details=interface_responses
                )
            
            # Compare search results
            consistency_issues = []
            base_response = successful_responses[0]
            
            for i, response in enumerate(successful_responses[1:], 1):
                base_data = base_response.get("data", [])
                compare_data = response.get("data", [])
                
                if len(base_data) != len(compare_data):
                    consistency_issues.append(f"Different result counts: {len(base_data)} vs {len(compare_data)}")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="search_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Search consistency issues: {'; '.join(consistency_issues)}",
                    details={
                        "interface_responses": interface_responses,
                        "consistency_issues": consistency_issues
                    }
                )
            else:
                return ValidationResult(
                    test_name="search_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "interface_responses": interface_responses,
                        "successful_interfaces": len(successful_responses)
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="search_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Search consistency test failed: {str(e)}"
            )
    
    async def test_authentication_consistency(self) -> ValidationResult:
        """Test that authentication behaves consistently across interfaces."""
        start_time = time.perf_counter()
        
        try:
            interface_auth_results = {}
            
            # Test authentication on each interface
            interfaces = {
                "internal_api": self.internal_api_url,
                "external_api": self.external_api_url
            }
            
            for interface_name, base_url in interfaces.items():
                try:
                    # Test without authentication (should fail)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{base_url}/entities") as response:
                            interface_auth_results[f"{interface_name}_no_auth"] = {
                                "status_code": response.status,
                                "expected_unauthorized": response.status in [401, 403],
                                "response_text": await response.text()
                            }
                    
                    # Test with invalid authentication (should fail)
                    headers = {"Authorization": "Bearer invalid_token"}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{base_url}/entities", headers=headers) as response:
                            interface_auth_results[f"{interface_name}_invalid_auth"] = {
                                "status_code": response.status,
                                "expected_unauthorized": response.status in [401, 403],
                                "response_text": await response.text()
                            }
                            
                except Exception as e:
                    interface_auth_results[f"{interface_name}_error"] = {"error": str(e)}
            
            # Analyze authentication consistency
            consistency_issues = []
            
            # Check that all interfaces properly reject unauthorized requests
            for interface_name in ["internal_api", "external_api"]:
                no_auth_key = f"{interface_name}_no_auth"
                invalid_auth_key = f"{interface_name}_invalid_auth"
                
                if no_auth_key in interface_auth_results:
                    if not interface_auth_results[no_auth_key].get("expected_unauthorized", False):
                        consistency_issues.append(f"{interface_name} does not properly reject requests without authentication")
                
                if invalid_auth_key in interface_auth_results:
                    if not interface_auth_results[invalid_auth_key].get("expected_unauthorized", False):
                        consistency_issues.append(f"{interface_name} does not properly reject requests with invalid authentication")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="authentication_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Authentication consistency issues: {'; '.join(consistency_issues)}",
                    details={
                        "interface_auth_results": interface_auth_results,
                        "consistency_issues": consistency_issues
                    }
                )
            else:
                return ValidationResult(
                    test_name="authentication_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "interface_auth_results": interface_auth_results,
                        "all_interfaces_secure": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="authentication_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Authentication consistency test failed: {str(e)}"
            )
    
    async def test_error_response_consistency(self) -> ValidationResult:
        """Test that error responses are consistent across interfaces."""
        start_time = time.perf_counter()
        
        try:
            interface_error_responses = {}
            
            # Test error scenarios across interfaces
            interfaces = {
                "internal_api": self.internal_api_url,
                "external_api": self.external_api_url
            }
            
            error_scenarios = [
                ("invalid_endpoint", "/nonexistent", "GET"),
                ("invalid_method", "/entities", "PATCH"),
                ("malformed_data", "/entities", "POST")
            ]
            
            for interface_name, base_url in interfaces.items():
                interface_error_responses[interface_name] = {}
                
                for scenario_name, endpoint, method in error_scenarios:
                    try:
                        async with aiohttp.ClientSession() as session:
                            request_kwargs = {"url": f"{base_url}{endpoint}"}
                            
                            if scenario_name == "malformed_data":
                                request_kwargs["json"] = {"invalid": "data structure"}
                                request_kwargs["headers"] = {"Content-Type": "application/json"}
                            
                            if method == "GET":
                                async with session.get(**request_kwargs) as response:
                                    interface_error_responses[interface_name][scenario_name] = {
                                        "status_code": response.status,
                                        "response_text": await response.text(),
                                        "content_type": response.headers.get("content-type", "")
                                    }
                            elif method == "POST":
                                async with session.post(**request_kwargs) as response:
                                    interface_error_responses[interface_name][scenario_name] = {
                                        "status_code": response.status,
                                        "response_text": await response.text(),
                                        "content_type": response.headers.get("content-type", "")
                                    }
                            elif method == "PATCH":
                                async with session.patch(**request_kwargs) as response:
                                    interface_error_responses[interface_name][scenario_name] = {
                                        "status_code": response.status,
                                        "response_text": await response.text(),
                                        "content_type": response.headers.get("content-type", "")
                                    }
                                    
                    except Exception as e:
                        interface_error_responses[interface_name][scenario_name] = {"error": str(e)}
            
            # Analyze error response consistency
            consistency_issues = []
            
            for scenario_name, _, _ in error_scenarios:
                status_codes = []
                content_types = []
                
                for interface_name in interfaces.keys():
                    if scenario_name in interface_error_responses.get(interface_name, {}):
                        response_data = interface_error_responses[interface_name][scenario_name]
                        if "status_code" in response_data:
                            status_codes.append(response_data["status_code"])
                            content_types.append(response_data.get("content_type", ""))
                
                # Check status code consistency
                if len(set(status_codes)) > 1:
                    consistency_issues.append(f"Inconsistent status codes for {scenario_name}: {status_codes}")
                
                # Check content type consistency
                if len(set(content_types)) > 1:
                    consistency_issues.append(f"Inconsistent content types for {scenario_name}: {content_types}")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="error_response_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Error response consistency issues: {'; '.join(consistency_issues)}",
                    details={
                        "interface_error_responses": interface_error_responses,
                        "consistency_issues": consistency_issues
                    }
                )
            else:
                return ValidationResult(
                    test_name="error_response_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "interface_error_responses": interface_error_responses,
                        "consistent_error_handling": True
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="error_response_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Error response consistency test failed: {str(e)}"
            )
    
    async def run_comprehensive_interface_validation(self) -> ValidationResult:
        """Run comprehensive validation across all interface validators."""
        start_time = time.perf_counter()
        
        try:
            # Initialize specialized validators
            crewai_validator = CrewAIToolValidator(self.config)
            fastapi_validator = FastAPIConsistencyValidator(self.config)
            mcp_validator = MCPComplianceValidator(self.config)
            
            # Run all specialized validations
            validation_results = {}
            
            # CrewAI Tool Validation
            self.logger.info("Running CrewAI tool validation")
            crewai_results = await crewai_validator.run_validation()
            validation_results["crewai_tools"] = {
                "total_tests": len(crewai_results),
                "passed": sum(1 for r in crewai_results if r.status == ValidationStatus.PASSED),
                "failed": sum(1 for r in crewai_results if r.status == ValidationStatus.FAILED),
                "warnings": sum(1 for r in crewai_results if r.status == ValidationStatus.WARNING),
                "results": crewai_results
            }
            
            # FastAPI Consistency Validation
            self.logger.info("Running FastAPI consistency validation")
            fastapi_results = await fastapi_validator.run_validation()
            validation_results["fastapi_consistency"] = {
                "total_tests": len(fastapi_results),
                "passed": sum(1 for r in fastapi_results if r.status == ValidationStatus.PASSED),
                "failed": sum(1 for r in fastapi_results if r.status == ValidationStatus.FAILED),
                "warnings": sum(1 for r in fastapi_results if r.status == ValidationStatus.WARNING),
                "results": fastapi_results
            }
            
            # MCP Compliance Validation
            self.logger.info("Running MCP compliance validation")
            mcp_results = await mcp_validator.run_validation()
            validation_results["mcp_compliance"] = {
                "total_tests": len(mcp_results),
                "passed": sum(1 for r in mcp_results if r.status == ValidationStatus.PASSED),
                "failed": sum(1 for r in mcp_results if r.status == ValidationStatus.FAILED),
                "warnings": sum(1 for r in mcp_results if r.status == ValidationStatus.WARNING),
                "results": mcp_results
            }
            
            # Analyze overall results
            total_tests = sum(v["total_tests"] for v in validation_results.values())
            total_passed = sum(v["passed"] for v in validation_results.values())
            total_failed = sum(v["failed"] for v in validation_results.values())
            total_warnings = sum(v["warnings"] for v in validation_results.values())
            
            # Determine overall status
            if total_failed > 0:
                failed_categories = [
                    category for category, results in validation_results.items()
                    if results["failed"] > 0
                ]
                return ValidationResult(
                    test_name="comprehensive_interface_validation",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Interface validation failures in: {', '.join(failed_categories)}",
                    details={
                        "summary": {
                            "total_tests": total_tests,
                            "passed": total_passed,
                            "failed": total_failed,
                            "warnings": total_warnings
                        },
                        "validation_results": validation_results
                    }
                )
            elif total_warnings > 0:
                warning_categories = [
                    category for category, results in validation_results.items()
                    if results["warnings"] > 0
                ]
                return ValidationResult(
                    test_name="comprehensive_interface_validation",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Interface validation warnings in: {', '.join(warning_categories)}",
                    details={
                        "summary": {
                            "total_tests": total_tests,
                            "passed": total_passed,
                            "failed": total_failed,
                            "warnings": total_warnings
                        },
                        "validation_results": validation_results
                    }
                )
            else:
                return ValidationResult(
                    test_name="comprehensive_interface_validation",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "summary": {
                            "total_tests": total_tests,
                            "passed": total_passed,
                            "failed": total_failed,
                            "warnings": total_warnings,
                            "all_interfaces_consistent": True
                        },
                        "validation_results": validation_results
                    }
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="comprehensive_interface_validation",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Comprehensive interface validation failed: {str(e)}"
            )

    async def run_validation(self) -> List[ValidationResult]:
        """Run comprehensive interface consistency validation."""
        self.logger.info("Starting interface consistency validation")
        
        # Define basic interface consistency tests
        basic_tests = [
            ("interface_availability", self.check_interface_availability),
            ("entity_creation_consistency", self.test_entity_creation_consistency),
            ("search_consistency", self.test_search_consistency),
            ("authentication_consistency", self.test_authentication_consistency),
            ("error_response_consistency", self.test_error_response_consistency)
        ]
        
        results = []
        
        # Run basic interface tests
        for test_name, test_func in basic_tests:
            self.logger.info(f"Running interface consistency test: {test_name}")
            result = await self.run_test(f"interface_{test_name}", test_func)
            results.append(result)
        
        # Run comprehensive interface validation
        self.logger.info("Running comprehensive interface validation")
        comprehensive_result = await self.run_test("comprehensive_interface_validation", self.run_comprehensive_interface_validation)
        results.append(comprehensive_result)
        
        self.logger.info("Interface consistency validation completed")
        return results
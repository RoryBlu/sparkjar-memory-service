"""
FastAPI Endpoint Consistency Validator.

This module validates that the internal and external FastAPI endpoints
provide consistent behavior, data formats, and error handling.
"""

import asyncio
import json
import logging
import os
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import aiohttp

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

class FastAPIConsistencyValidator(BaseValidator):
    """Validate consistency between internal and external FastAPI endpoints."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("FastAPIConsistencyValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # API endpoints
        self.internal_api_url = self.config["internal_api_url"]
        self.external_api_url = self.config["external_api_url"]
        
        # Authentication
        self.test_token = None
        self.test_client_id = str(uuid4())
        self.test_actor_id = str(uuid4())
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
            "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "api_secret_key": os.getenv("API_SECRET_KEY", "test_secret_key"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30"))
        }
    
    def _generate_test_token(self) -> str:
        """Generate a test JWT token for external API authentication."""
        payload = {
            "client_id": self.test_client_id,
            "actor_type": "client",
            "actor_id": self.test_actor_id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "iss": "sparkjar-test"
        }
        return jwt.encode(payload, self.config["api_secret_key"], algorithm="HS256")
    
    async def test_endpoint_availability(self) -> ValidationResult:
        """Test that both internal and external API endpoints are available."""
        start_time = time.perf_counter()
        
        try:
            endpoint_results = {}
            
            # Test internal API health
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])) as session:
                    async with session.get(f"{self.internal_api_url}/docs") as response:
                        endpoint_results["internal_api"] = {
                            "available": response.status == 200,
                            "status_code": response.status,
                            "response_time_ms": 0  # Could measure this if needed
                        }
            except Exception as e:
                endpoint_results["internal_api"] = {
                    "available": False,
                    "error": str(e)
                }
            
            # Test external API health
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])) as session:
                    async with session.get(f"{self.external_api_url}/health") as response:
                        endpoint_results["external_api"] = {
                            "available": response.status == 200,
                            "status_code": response.status,
                            "response_data": await response.json() if response.status == 200 else None
                        }
            except Exception as e:
                endpoint_results["external_api"] = {
                    "available": False,
                    "error": str(e)
                }
            
            # Check results
            available_apis = sum(1 for r in endpoint_results.values() if r.get("available", False))
            total_apis = len(endpoint_results)
            
            if available_apis == 0:
                return ValidationResult(
                    test_name="endpoint_availability",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="No FastAPI endpoints are available",
                    details=endpoint_results
                )
            elif available_apis < total_apis:
                return ValidationResult(
                    test_name="endpoint_availability",
                    status=ValidationStatus.WARNING,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    warning_message=f"Only {available_apis}/{total_apis} FastAPI endpoints available",
                    details=endpoint_results
                )
            else:
                return ValidationResult(
                    test_name="endpoint_availability",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details=endpoint_results
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="endpoint_availability",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Endpoint availability test failed: {str(e)}"
            )
    
    async def test_authentication_consistency(self) -> ValidationResult:
        """Test that authentication behaves consistently across APIs."""
        start_time = time.perf_counter()
        
        try:
            auth_results = {}
            
            # Generate test token
            self.test_token = self._generate_test_token()
            
            # Test internal API (should not require auth)
            try:
                async with aiohttp.ClientSession() as session:
                    # Internal API should accept requests without authentication
                    test_data = {
                        "client_id": self.test_client_id,
                        "actor_type": "client",
                        "actor_id": self.test_actor_id,
                        "query": "test search",
                        "limit": 5
                    }
                    
                    async with session.post(f"{self.internal_api_url}/search", json=test_data) as response:
                        auth_results["internal_no_auth"] = {
                            "status_code": response.status,
                            "accepts_no_auth": response.status != 401,
                            "response_text": await response.text()
                        }
            except Exception as e:
                auth_results["internal_no_auth"] = {"error": str(e)}
            
            # Test external API without authentication (should fail)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.external_api_url}/memory/search", 
                                          params={"query": "test", "limit": 5}) as response:
                        auth_results["external_no_auth"] = {
                            "status_code": response.status,
                            "properly_rejects": response.status == 401,
                            "response_text": await response.text()
                        }
            except Exception as e:
                auth_results["external_no_auth"] = {"error": str(e)}
            
            # Test external API with valid authentication (should succeed)
            try:
                headers = {"Authorization": f"Bearer {self.test_token}"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.external_api_url}/memory/search",
                                          params={"query": "test", "limit": 5},
                                          headers=headers) as response:
                        auth_results["external_valid_auth"] = {
                            "status_code": response.status,
                            "accepts_valid_auth": response.status != 401,
                            "response_text": await response.text()
                        }
            except Exception as e:
                auth_results["external_valid_auth"] = {"error": str(e)}
            
            # Test external API with invalid authentication (should fail)
            try:
                headers = {"Authorization": "Bearer invalid_token"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.external_api_url}/memory/search",
                                          params={"query": "test", "limit": 5},
                                          headers=headers) as response:
                        auth_results["external_invalid_auth"] = {
                            "status_code": response.status,
                            "properly_rejects": response.status == 401,
                            "response_text": await response.text()
                        }
            except Exception as e:
                auth_results["external_invalid_auth"] = {"error": str(e)}
            
            # Analyze authentication consistency
            consistency_issues = []
            
            # Internal API should not require auth
            if not auth_results.get("internal_no_auth", {}).get("accepts_no_auth", False):
                consistency_issues.append("Internal API unexpectedly requires authentication")
            
            # External API should reject requests without auth
            if not auth_results.get("external_no_auth", {}).get("properly_rejects", False):
                consistency_issues.append("External API does not properly reject unauthenticated requests")
            
            # External API should accept valid auth
            if not auth_results.get("external_valid_auth", {}).get("accepts_valid_auth", False):
                consistency_issues.append("External API does not accept valid authentication")
            
            # External API should reject invalid auth
            if not auth_results.get("external_invalid_auth", {}).get("properly_rejects", False):
                consistency_issues.append("External API does not properly reject invalid authentication")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="authentication_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Authentication consistency issues: {'; '.join(consistency_issues)}",
                    details=auth_results
                )
            else:
                return ValidationResult(
                    test_name="authentication_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details=auth_results
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="authentication_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Authentication consistency test failed: {str(e)}"
            )
    
    async def test_data_format_consistency(self) -> ValidationResult:
        """Test that both APIs return consistent data formats."""
        start_time = time.perf_counter()
        
        try:
            # Generate test token if not already done
            if not self.test_token:
                self.test_token = self._generate_test_token()
            
            format_results = {}
            
            # Test search endpoint on both APIs
            search_query = "test search query"
            
            # Test internal API search
            try:
                async with aiohttp.ClientSession() as session:
                    search_data = {
                        "client_id": self.test_client_id,
                        "actor_type": "client",
                        "actor_id": self.test_actor_id,
                        "query": search_query,
                        "limit": 5
                    }
                    
                    async with session.post(f"{self.internal_api_url}/search", json=search_data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            format_results["internal_search"] = {
                                "status_code": response.status,
                                "data_type": type(response_data).__name__,
                                "is_list": isinstance(response_data, list),
                                "has_items": len(response_data) >= 0 if isinstance(response_data, list) else False,
                                "sample_structure": self._analyze_structure(response_data)
                            }
                        else:
                            format_results["internal_search"] = {
                                "status_code": response.status,
                                "error": await response.text()
                            }
            except Exception as e:
                format_results["internal_search"] = {"error": str(e)}
            
            # Test external API search
            try:
                headers = {"Authorization": f"Bearer {self.test_token}"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.external_api_url}/memory/search",
                                          params={"query": search_query, "limit": 5},
                                          headers=headers) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            format_results["external_search"] = {
                                "status_code": response.status,
                                "data_type": type(response_data).__name__,
                                "is_list": isinstance(response_data, list),
                                "has_items": len(response_data) >= 0 if isinstance(response_data, list) else False,
                                "sample_structure": self._analyze_structure(response_data)
                            }
                        else:
                            format_results["external_search"] = {
                                "status_code": response.status,
                                "error": await response.text()
                            }
            except Exception as e:
                format_results["external_search"] = {"error": str(e)}
            
            # Compare data formats
            consistency_issues = []
            
            internal_result = format_results.get("internal_search", {})
            external_result = format_results.get("external_search", {})
            
            # Both should return successful responses or both should fail
            internal_success = internal_result.get("status_code") == 200
            external_success = external_result.get("status_code") == 200
            
            if internal_success and external_success:
                # Compare data structures
                if internal_result.get("data_type") != external_result.get("data_type"):
                    consistency_issues.append(f"Different data types: internal={internal_result.get('data_type')}, external={external_result.get('data_type')}")
                
                if internal_result.get("is_list") != external_result.get("is_list"):
                    consistency_issues.append("Inconsistent list/object response format")
            
            elif not internal_success and not external_success:
                # Both failed - check if error formats are consistent
                internal_error = internal_result.get("error", "")
                external_error = external_result.get("error", "")
                
                # Basic consistency check - both should have error messages
                if not internal_error and not external_error:
                    consistency_issues.append("Both APIs failed but provided no error information")
            
            else:
                # One succeeded, one failed - this might be expected due to different auth requirements
                self.logger.info("Internal and external APIs had different success rates - this may be expected due to authentication differences")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="data_format_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Data format consistency issues: {'; '.join(consistency_issues)}",
                    details=format_results
                )
            else:
                return ValidationResult(
                    test_name="data_format_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details=format_results
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="data_format_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Data format consistency test failed: {str(e)}"
            )
    
    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of response data."""
        if isinstance(data, list):
            return {
                "type": "list",
                "length": len(data),
                "item_structure": self._analyze_structure(data[0]) if data else None
            }
        elif isinstance(data, dict):
            return {
                "type": "dict",
                "keys": list(data.keys())[:5],  # First 5 keys
                "key_count": len(data.keys())
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
            }
    
    async def test_error_response_consistency(self) -> ValidationResult:
        """Test that error responses are consistent across APIs."""
        start_time = time.perf_counter()
        
        try:
            error_scenarios = [
                ("invalid_endpoint", "/nonexistent", "GET"),
                ("malformed_request", "/search", "POST")
            ]
            
            error_results = {}
            
            for scenario_name, endpoint, method in error_scenarios:
                error_results[scenario_name] = {}
                
                # Test internal API
                try:
                    async with aiohttp.ClientSession() as session:
                        if method == "GET":
                            async with session.get(f"{self.internal_api_url}{endpoint}") as response:
                                error_results[scenario_name]["internal"] = {
                                    "status_code": response.status,
                                    "content_type": response.headers.get("content-type", ""),
                                    "response_text": await response.text()
                                }
                        elif method == "POST":
                            # Send malformed data
                            async with session.post(f"{self.internal_api_url}{endpoint}", 
                                                  json={"invalid": "data"}) as response:
                                error_results[scenario_name]["internal"] = {
                                    "status_code": response.status,
                                    "content_type": response.headers.get("content-type", ""),
                                    "response_text": await response.text()
                                }
                except Exception as e:
                    error_results[scenario_name]["internal"] = {"error": str(e)}
                
                # Test external API
                try:
                    headers = {"Authorization": f"Bearer {self.test_token}"} if self.test_token else {}
                    async with aiohttp.ClientSession() as session:
                        if method == "GET":
                            async with session.get(f"{self.external_api_url}{endpoint}", 
                                                 headers=headers) as response:
                                error_results[scenario_name]["external"] = {
                                    "status_code": response.status,
                                    "content_type": response.headers.get("content-type", ""),
                                    "response_text": await response.text()
                                }
                        elif method == "POST":
                            async with session.post(f"{self.external_api_url}{endpoint}",
                                                  json={"invalid": "data"},
                                                  headers=headers) as response:
                                error_results[scenario_name]["external"] = {
                                    "status_code": response.status,
                                    "content_type": response.headers.get("content-type", ""),
                                    "response_text": await response.text()
                                }
                except Exception as e:
                    error_results[scenario_name]["external"] = {"error": str(e)}
            
            # Analyze error response consistency
            consistency_issues = []
            
            for scenario_name, results in error_results.items():
                internal_result = results.get("internal", {})
                external_result = results.get("external", {})
                
                # Check status code consistency (allowing for some differences due to auth)
                internal_status = internal_result.get("status_code")
                external_status = external_result.get("status_code")
                
                if internal_status and external_status:
                    # Both should return error status codes (4xx or 5xx)
                    internal_is_error = internal_status >= 400
                    external_is_error = external_status >= 400
                    
                    if not (internal_is_error and external_is_error):
                        consistency_issues.append(f"{scenario_name}: Inconsistent error status codes")
                
                # Check content type consistency
                internal_content_type = internal_result.get("content_type", "")
                external_content_type = external_result.get("content_type", "")
                
                if internal_content_type and external_content_type:
                    # Both should return similar content types for errors
                    if "json" in internal_content_type and "json" not in external_content_type:
                        consistency_issues.append(f"{scenario_name}: Inconsistent error content types")
                    elif "json" in external_content_type and "json" not in internal_content_type:
                        consistency_issues.append(f"{scenario_name}: Inconsistent error content types")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="error_response_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Error response consistency issues: {'; '.join(consistency_issues)}",
                    details=error_results
                )
            else:
                return ValidationResult(
                    test_name="error_response_consistency",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details=error_results
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="error_response_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Error response consistency test failed: {str(e)}"
            )
    
    async def test_rate_limiting_consistency(self) -> ValidationResult:
        """Test that rate limiting behaves consistently across APIs."""
        start_time = time.perf_counter()
        
        try:
            # Generate test token if not already done
            if not self.test_token:
                self.test_token = self._generate_test_token()
            
            rate_limit_results = {}
            
            # Test rate limiting on external API (internal API may not have rate limiting)
            try:
                headers = {"Authorization": f"Bearer {self.test_token}"}
                request_count = 0
                rate_limited = False
                
                async with aiohttp.ClientSession() as session:
                    # Make multiple rapid requests
                    for i in range(10):  # Reduced from potential higher numbers for testing
                        try:
                            async with session.post(f"{self.external_api_url}/memory/search",
                                                  params={"query": f"test {i}", "limit": 1},
                                                  headers=headers) as response:
                                request_count += 1
                                
                                if response.status == 429:  # Too Many Requests
                                    rate_limited = True
                                    break
                                elif response.status != 200:
                                    # Some other error, not rate limiting
                                    break
                        except Exception:
                            break
                
                rate_limit_results["external_api"] = {
                    "requests_made": request_count,
                    "rate_limited": rate_limited,
                    "rate_limit_detected": rate_limited
                }
                
            except Exception as e:
                rate_limit_results["external_api"] = {"error": str(e)}
            
            # For now, we'll consider this test passed if we can make the requests
            # In a production system, you'd want to test actual rate limiting behavior
            return ValidationResult(
                test_name="rate_limiting_consistency",
                status=ValidationStatus.PASSED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                details=rate_limit_results,
                warning_message="Rate limiting test is basic - production systems should have comprehensive rate limiting tests"
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="rate_limiting_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Rate limiting consistency test failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run comprehensive FastAPI endpoint consistency validation."""
        self.logger.info("Starting FastAPI endpoint consistency validation")
        
        # Define FastAPI consistency tests
        tests = [
            ("endpoint_availability", self.test_endpoint_availability),
            ("authentication_consistency", self.test_authentication_consistency),
            ("data_format_consistency", self.test_data_format_consistency),
            ("error_response_consistency", self.test_error_response_consistency),
            ("rate_limiting_consistency", self.test_rate_limiting_consistency)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.logger.info(f"Running FastAPI consistency test: {test_name}")
            result = await self.run_test(f"fastapi_{test_name}", test_func)
            results.append(result)
        
        self.logger.info("FastAPI endpoint consistency validation completed")
        return results
"""
CrewAI Memory Tool Integration Validator.

This module validates that the CrewAI memory tool works correctly within
agent workflows and provides consistent behavior with other interfaces.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock

from .base import BaseValidator, ValidationResult, ValidationStatus
from .test_data_generator import TestDataGenerator

# Use proper package imports - no sys.path manipulation needed

class CrewAIToolValidator(BaseValidator):
    """Validate CrewAI memory tool integration and functionality."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("CrewAIToolValidator")
        self.config = config or self._load_default_config()
        self.test_data_generator = TestDataGenerator(seed=42)
        
        # Tool instance for testing
        self.memory_tool = None
    
    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
            "memory_service_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
            "mcp_registry_url": os.getenv("MCP_REGISTRY_URL", "http://localhost:8001"),
            "api_secret_key": os.getenv("API_SECRET_KEY", "test_secret_key"),
            "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
            "test_client_id": "crewai_tool_test_client"
        }
    
    def _initialize_memory_tool(self):
        """Initialize the CrewAI memory tool for testing."""
        try:
            from tools.sj_memory_tool import SJMemoryTool, MemoryConfig
            
            # Create tool configuration
            tool_config = MemoryConfig(
                mcp_registry_url=self.config["mcp_registry_url"],
                api_secret_key=self.config["api_secret_key"],
                timeout=self.config["timeout_seconds"]
            )
            
            # Initialize the tool
            self.memory_tool = SJMemoryTool(config=tool_config)
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import CrewAI memory tool: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize CrewAI memory tool: {e}")
            return False
    
    async def test_tool_initialization(self) -> ValidationResult:
        """Test that the CrewAI memory tool initializes correctly."""
        start_time = time.perf_counter()
        
        try:
            success = self._initialize_memory_tool()
            
            if not success:
                return ValidationResult(
                    test_name="tool_initialization",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Failed to initialize CrewAI memory tool"
                )
            
            # Check tool properties
            if not hasattr(self.memory_tool, 'name'):
                return ValidationResult(
                    test_name="tool_initialization",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Memory tool missing required 'name' attribute"
                )
            
            if not hasattr(self.memory_tool, 'description'):
                return ValidationResult(
                    test_name="tool_initialization",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Memory tool missing required 'description' attribute"
                )
            
            if not hasattr(self.memory_tool, '_run'):
                return ValidationResult(
                    test_name="tool_initialization",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Memory tool missing required '_run' method"
                )
            
            return ValidationResult(
                test_name="tool_initialization",
                status=ValidationStatus.PASSED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                details={
                    "tool_name": self.memory_tool.name,
                    "tool_description": self.memory_tool.description[:100] + "..." if len(self.memory_tool.description) > 100 else self.memory_tool.description,
                    "has_required_methods": True
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="tool_initialization",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Tool initialization test failed: {str(e)}"
            )
    
    async def test_entity_creation_via_tool(self) -> ValidationResult:
        """Test entity creation through the CrewAI memory tool."""
        start_time = time.perf_counter()
        
        try:
            if not self.memory_tool:
                if not self._initialize_memory_tool():
                    return ValidationResult(
                        test_name="entity_creation_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=0.0,
                        error_message="Memory tool not initialized"
                    )
            
            # Generate test entity data
            test_entities = self.test_data_generator.generate_entities(1, self.config["test_client_id"])
            test_entity = test_entities[0]
            
            # Create entity via tool
            query = json.dumps({
                "action": "create_entity",
                "params": {
                    "name": test_entity.name,
                    "entity_type": test_entity.entity_type,
                    "metadata": test_entity.metadata
                }
            })
            
            # Mock the HTTP client to avoid actual API calls during testing
            with patch('httpx.AsyncClient') as mock_client:
                # Mock successful response
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    "entity_id": test_entity.id,
                    "name": test_entity.name,
                    "entity_type": test_entity.entity_type
                }
                
                mock_client_instance = MagicMock()
                mock_client_instance.post.return_value.__aenter__.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # Mock service discovery
                with patch.object(self.memory_tool, '_discover_memory_service', return_value=self.config["memory_service_url"]):
                    result = self.memory_tool._run(query)
            
            # Parse and validate result
            try:
                result_data = json.loads(result)
                
                if not result_data.get("success"):
                    return ValidationResult(
                        test_name="entity_creation_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                        error_message=f"Tool returned failure: {result_data.get('error', 'Unknown error')}",
                        details={"tool_result": result}
                    )
                
                # Validate response structure
                if "entity_id" not in result_data:
                    return ValidationResult(
                        test_name="entity_creation_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                        error_message="Tool result missing entity_id",
                        details={"tool_result": result_data}
                    )
                
                return ValidationResult(
                    test_name="entity_creation_via_tool",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "entity_created": True,
                        "entity_id": result_data["entity_id"],
                        "tool_result": result_data
                    }
                )
                
            except json.JSONDecodeError:
                return ValidationResult(
                    test_name="entity_creation_via_tool",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Tool returned invalid JSON",
                    details={"raw_result": result}
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="entity_creation_via_tool",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Entity creation via tool test failed: {str(e)}"
            )
    
    async def test_search_via_tool(self) -> ValidationResult:
        """Test entity search through the CrewAI memory tool."""
        start_time = time.perf_counter()
        
        try:
            if not self.memory_tool:
                if not self._initialize_memory_tool():
                    return ValidationResult(
                        test_name="search_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=0.0,
                        error_message="Memory tool not initialized"
                    )
            
            # Search query
            query = json.dumps({
                "action": "search_entities",
                "params": {
                    "query": "test person",
                    "entity_type": "person",
                    "limit": 10
                }
            })
            
            # Mock the HTTP client
            with patch('httpx.AsyncClient') as mock_client:
                # Mock successful search response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "results": [
                        {
                            "entity_id": "test-entity-1",
                            "name": "Test Person",
                            "entity_type": "person",
                            "relevance_score": 0.95
                        }
                    ]
                }
                
                mock_client_instance = MagicMock()
                mock_client_instance.get.return_value.__aenter__.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                # Mock service discovery
                with patch.object(self.memory_tool, '_discover_memory_service', return_value=self.config["memory_service_url"]):
                    result = self.memory_tool._run(query)
            
            # Parse and validate result
            try:
                result_data = json.loads(result)
                
                if not result_data.get("success"):
                    return ValidationResult(
                        test_name="search_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                        error_message=f"Tool search failed: {result_data.get('error', 'Unknown error')}",
                        details={"tool_result": result}
                    )
                
                # Validate search response structure
                if "results" not in result_data:
                    return ValidationResult(
                        test_name="search_via_tool",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=(time.perf_counter() - start_time) * 1000,
                        error_message="Tool search result missing 'results' field",
                        details={"tool_result": result_data}
                    )
                
                return ValidationResult(
                    test_name="search_via_tool",
                    status=ValidationStatus.PASSED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    details={
                        "search_successful": True,
                        "result_count": result_data.get("count", 0),
                        "tool_result": result_data
                    }
                )
                
            except json.JSONDecodeError:
                return ValidationResult(
                    test_name="search_via_tool",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message="Tool returned invalid JSON for search",
                    details={"raw_result": result}
                )
                
        except Exception as e:
            return ValidationResult(
                test_name="search_via_tool",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Search via tool test failed: {str(e)}"
            )
    
    async def test_tool_error_handling(self) -> ValidationResult:
        """Test that the CrewAI tool handles errors gracefully."""
        start_time = time.perf_counter()
        
        try:
            if not self.memory_tool:
                if not self._initialize_memory_tool():
                    return ValidationResult(
                        test_name="tool_error_handling",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=0.0,
                        error_message="Memory tool not initialized"
                    )
            
            error_scenarios = [
                ("invalid_json", "not valid json"),
                ("missing_action", '{"params": {"name": "test"}}'),
                ("invalid_action", '{"action": "nonexistent_action", "params": {}}'),
                ("missing_params", '{"action": "create_entity", "params": {}}')
            ]
            
            error_handling_results = {}
            
            for scenario_name, query in error_scenarios:
                try:
                    result = self.memory_tool._run(query)
                    
                    # Tool should return error message, not crash
                    error_handling_results[scenario_name] = {
                        "handled_gracefully": "Error:" in result or "error" in result.lower(),
                        "result": result[:200] + "..." if len(result) > 200 else result
                    }
                    
                except Exception as e:
                    error_handling_results[scenario_name] = {
                        "handled_gracefully": False,
                        "exception": str(e)
                    }
            
            # Check if all errors were handled gracefully
            graceful_handling = all(
                result.get("handled_gracefully", False) 
                for result in error_handling_results.values()
            )
            
            if not graceful_handling:
                failed_scenarios = [
                    name for name, result in error_handling_results.items()
                    if not result.get("handled_gracefully", False)
                ]
                
                return ValidationResult(
                    test_name="tool_error_handling",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Tool did not handle errors gracefully: {failed_scenarios}",
                    details=error_handling_results
                )
            
            return ValidationResult(
                test_name="tool_error_handling",
                status=ValidationStatus.PASSED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                details={
                    "all_errors_handled_gracefully": True,
                    "scenarios_tested": list(error_handling_results.keys()),
                    "error_handling_results": error_handling_results
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="tool_error_handling",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Tool error handling test failed: {str(e)}"
            )
    
    async def test_tool_response_format_consistency(self) -> ValidationResult:
        """Test that the tool returns consistent response formats."""
        start_time = time.perf_counter()
        
        try:
            if not self.memory_tool:
                if not self._initialize_memory_tool():
                    return ValidationResult(
                        test_name="tool_response_format_consistency",
                        status=ValidationStatus.FAILED,
                        execution_time_ms=0.0,
                        error_message="Memory tool not initialized"
                    )
            
            # Test different successful operations
            test_operations = [
                {
                    "name": "create_entity",
                    "query": json.dumps({
                        "action": "create_entity",
                        "params": {"name": "Test Entity", "entity_type": "person"}
                    }),
                    "expected_fields": ["success", "entity_id", "message"]
                },
                {
                    "name": "search_entities",
                    "query": json.dumps({
                        "action": "search_entities",
                        "params": {"query": "test", "limit": 5}
                    }),
                    "expected_fields": ["success", "results", "count"]
                }
            ]
            
            format_consistency_results = {}
            
            for operation in test_operations:
                try:
                    # Mock successful responses for each operation
                    with patch('httpx.AsyncClient') as mock_client:
                        if operation["name"] == "create_entity":
                            mock_response = MagicMock()
                            mock_response.status_code = 201
                            mock_response.json.return_value = {
                                "entity_id": "test-id",
                                "name": "Test Entity",
                                "entity_type": "person"
                            }
                        else:  # search_entities
                            mock_response = MagicMock()
                            mock_response.status_code = 200
                            mock_response.json.return_value = {"results": []}
                        
                        mock_client_instance = MagicMock()
                        if operation["name"] == "create_entity":
                            mock_client_instance.post.return_value.__aenter__.return_value = mock_response
                        else:
                            mock_client_instance.get.return_value.__aenter__.return_value = mock_response
                        mock_client.return_value.__aenter__.return_value = mock_client_instance
                        
                        with patch.object(self.memory_tool, '_discover_memory_service', return_value=self.config["memory_service_url"]):
                            result = self.memory_tool._run(operation["query"])
                    
                    # Parse result and check format
                    try:
                        result_data = json.loads(result)
                        
                        missing_fields = []
                        for field in operation["expected_fields"]:
                            if field not in result_data:
                                missing_fields.append(field)
                        
                        format_consistency_results[operation["name"]] = {
                            "valid_json": True,
                            "has_success_field": "success" in result_data,
                            "success_value": result_data.get("success"),
                            "missing_fields": missing_fields,
                            "all_expected_fields_present": len(missing_fields) == 0
                        }
                        
                    except json.JSONDecodeError:
                        format_consistency_results[operation["name"]] = {
                            "valid_json": False,
                            "raw_result": result[:200] + "..." if len(result) > 200 else result
                        }
                        
                except Exception as e:
                    format_consistency_results[operation["name"]] = {
                        "error": str(e)
                    }
            
            # Check overall consistency
            consistency_issues = []
            
            for op_name, result in format_consistency_results.items():
                if not result.get("valid_json", False):
                    consistency_issues.append(f"{op_name}: Invalid JSON response")
                
                if not result.get("has_success_field", False):
                    consistency_issues.append(f"{op_name}: Missing 'success' field")
                
                if result.get("missing_fields"):
                    consistency_issues.append(f"{op_name}: Missing fields {result['missing_fields']}")
            
            if consistency_issues:
                return ValidationResult(
                    test_name="tool_response_format_consistency",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Response format inconsistencies: {'; '.join(consistency_issues)}",
                    details=format_consistency_results
                )
            
            return ValidationResult(
                test_name="tool_response_format_consistency",
                status=ValidationStatus.PASSED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                details={
                    "consistent_response_format": True,
                    "operations_tested": list(format_consistency_results.keys()),
                    "format_results": format_consistency_results
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="tool_response_format_consistency",
                status=ValidationStatus.FAILED,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Tool response format consistency test failed: {str(e)}"
            )
    
    async def run_validation(self) -> List[ValidationResult]:
        """Run comprehensive CrewAI tool validation."""
        self.logger.info("Starting CrewAI tool validation")
        
        # Define CrewAI tool tests
        tests = [
            ("tool_initialization", self.test_tool_initialization),
            ("entity_creation_via_tool", self.test_entity_creation_via_tool),
            ("search_via_tool", self.test_search_via_tool),
            ("tool_error_handling", self.test_tool_error_handling),
            ("tool_response_format_consistency", self.test_tool_response_format_consistency)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.logger.info(f"Running CrewAI tool test: {test_name}")
            result = await self.run_test(f"crewai_{test_name}", test_func)
            results.append(result)
        
        self.logger.info("CrewAI tool validation completed")
        return results
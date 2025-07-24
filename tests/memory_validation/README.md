# Memory System Validation Framework

This directory contains a comprehensive validation framework for the SparkJAR memory system. The framework validates data integrity, system health, performance, and reliability before production deployment.

## Overview

The validation framework consists of several components:

- **Health Checker**: Validates system connectivity and basic operations
- **Data Integrity Validator**: Tests data consistency, client isolation, and referential integrity
- **Comprehensive Validator**: Orchestrates complete system validation including load testing
- **Test Data Generator**: Creates realistic test data for validation scenarios

## Quick Start

### Prerequisites

1. Set up your database connection:
```bash
export DATABASE_URL_DIRECT="postgresql+asyncpg://user:password@localhost/database"
```

2. Ensure your memory system services are running (optional for database-only tests):
```bash
export MEMORY_INTERNAL_API_URL="http://localhost:8001"
export MEMORY_EXTERNAL_API_URL="http://localhost:8443"
export MEMORY_MCP_API_URL="http://localhost:8002"
```

### Running Validations

#### Quick Data Integrity Check
```bash
python tests/memory_validation/run_data_integrity_validation.py
```

#### Comprehensive System Validation
```bash
python tests/memory_validation/run_validation.py --save-report --verbose
```

#### Performance Benchmarking
```bash
python tests/memory_validation/run_performance_benchmarks.py --save-report --test-size medium
```

#### Error Simulation and Recovery Testing
```bash
python tests/memory_validation/run_error_simulation.py
```

#### Interface Consistency Validation
```bash
python tests/memory_validation/run_interface_validation.py
```

#### Custom Configuration
```bash
python tests/memory_validation/run_validation.py --config-file config.json --save-report
```

## Validation Components

### 1. Health Checker (`health_checker.py`)

Validates basic system health:
- Database connectivity
- API endpoint availability
- Basic CRUD operations
- Authentication systems

### 2. Data Integrity Validator (`data_integrity_validator.py`)

Tests data consistency and integrity:
- **Schema Validation**: Ensures all required tables and columns exist
- **Entity Uniqueness**: Tests duplicate prevention and merging
- **Referential Integrity**: Validates relationship consistency
- **Client Isolation**: Ensures strict data boundaries between clients
- **JSON Metadata**: Tests complex metadata storage and querying
- **Timestamp Consistency**: Validates created/updated timestamp handling
- **Concurrent Operations**: Tests race condition handling
- **Large Data Handling**: Tests performance with large metadata objects

### 3. Performance Benchmarker (`performance_benchmarker.py`)

Comprehensive performance testing:
- **Text Processing Performance**: Tests processing speed for different text sizes (1KB, 10KB, 50KB)
- **Concurrent Operations**: Tests system behavior under concurrent load
- **Search Performance**: Benchmarks search and retrieval operations
- **Resource Monitoring**: Tracks CPU, memory, and system resource usage

### 4. Error Simulator (`error_simulator.py`)

Comprehensive error simulation and recovery testing:
- **Database Failure Scenarios**: Connection loss, timeouts, deadlocks
- **Network Failure Handling**: Connection refused, timeouts, intermittent failures
- **Resource Exhaustion**: Memory, connection pool, disk space exhaustion
- **Transaction Rollback**: Ensures failed transactions rollback completely
- **Concurrent Conflicts**: Tests handling of concurrent operation conflicts
- **Recovery Mechanisms**: Validates retry logic and exponential backoff

### 5. Interface Consistency Validator (`interface_consistency_validator.py`)

Comprehensive interface consistency and integration testing:
- **CrewAI Tool Integration**: Validates memory tools work within CrewAI agents
- **FastAPI Endpoint Consistency**: Tests internal and external API consistency
- **MCP Interface Compliance**: Validates MCP protocol compliance and functionality
- **Cross-Interface Data Consistency**: Ensures identical operations produce same results
- **Authentication Consistency**: Verifies consistent auth behavior across interfaces
- **Error Response Consistency**: Tests consistent error handling across all interfaces

### 6. CrewAI Tool Validator (`crewai_tool_validator.py`)

Specialized CrewAI tool integration testing:
- **Tool Initialization**: Validates proper tool setup and configuration
- **Entity Operations**: Tests entity creation, search, and management via tools
- **Error Handling**: Ensures tools handle errors gracefully without breaking agents
- **Response Format Consistency**: Validates consistent JSON response formats
- **Agent Workflow Integration**: Tests tool performance within agent execution

### 7. FastAPI Consistency Validator (`fastapi_consistency_validator.py`)

FastAPI endpoint consistency validation:
- **Endpoint Availability**: Tests internal and external API availability
- **Authentication Consistency**: Validates auth requirements and behavior
- **Data Format Consistency**: Ensures consistent response structures
- **Error Response Consistency**: Tests consistent error handling and formats
- **Rate Limiting Consistency**: Validates consistent rate limiting behavior

### 8. MCP Compliance Validator (`mcp_compliance_validator.py`)

MCP (Model Context Protocol) interface compliance:
- **Server Initialization**: Validates MCP server setup and configuration
- **Tool Definitions**: Tests all required MCP tools are properly defined
- **Resource Definitions**: Validates MCP resources for browsing memory content
- **Prompt Definitions**: Tests MCP prompts for memory-aware templates
- **External API Integration**: Validates MCP server integrates with memory APIs
- **Protocol Compliance**: Ensures adherence to MCP protocol standards

### 9. Comprehensive Validator (`comprehensive_validator.py`)

Orchestrates complete system validation:
- **System Readiness**: Overall health assessment
- **Data Integrity**: Complete integrity test suite
- **Multi-Client Isolation**: Advanced client boundary testing
- **Performance Comprehensive**: Full performance benchmark suite
- **Error Handling**: Complete error simulation and recovery testing
- **Interface Consistency**: Multi-interface validation orchestration
- **Load Testing**: Performance under moderate load

### 10. Test Data Generator (`test_data_generator.py`)

Generates realistic test data:
- Person entities with various grades (absolute, high, medium, low, generic)
- Company entities with business information
- Meeting entities with participants and metadata
- Relationships between entities
- Text samples of various sizes for performance testing
- Concurrent operation scenarios

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL_DIRECT` | Direct database connection URL | Required |
| `MEMORY_INTERNAL_API_URL` | Internal API URL | `http://localhost:8001` |
| `MEMORY_EXTERNAL_API_URL` | External API URL | `http://localhost:8443` |
| `MEMORY_MCP_API_URL` | MCP API URL | `http://localhost:8002` |
| `VALIDATION_TIMEOUT` | Timeout in seconds | `30` |
| `TEST_CLIENT_COUNT` | Number of test clients | `3` |
| `TEST_ENTITY_COUNT` | Number of test entities | `50` |

### Configuration File Format

```json
{
  "database_url": "postgresql+asyncpg://user:pass@localhost/db",
  "internal_api_url": "http://localhost:8001",
  "external_api_url": "http://localhost:8443",
  "mcp_api_url": "http://localhost:8002",
  "timeout_seconds": 30,
  "test_client_count": 5,
  "test_entity_count": 100
}
```

## Validation Results

### Exit Codes

- `0`: All tests passed or warnings only
- `1`: One or more tests failed
- `130`: Interrupted by user (Ctrl+C)

### Report Format

When using `--save-report`, a detailed JSON report is generated containing:

```json
{
  "start_time": "2025-01-15T10:30:00Z",
  "end_time": "2025-01-15T10:32:30Z",
  "duration_seconds": 150.5,
  "total_tests": 15,
  "passed_tests": 13,
  "failed_tests": 1,
  "warning_tests": 1,
  "config": { ... },
  "results": [
    {
      "test_name": "integrity_table_schema_validation",
      "status": "passed",
      "execution_time_ms": 245.7,
      "details": { ... }
    }
  ]
}
```

## Understanding Test Results

### Critical Failures
These indicate serious issues that must be fixed:
- Database connectivity failures
- Schema validation failures
- Data corruption or loss
- Client isolation breaches

### Warnings
These indicate potential issues to investigate:
- Performance slower than expected
- Non-critical schema differences
- Degraded service availability

### Performance Benchmarks

The framework includes performance expectations:
- Entity creation: >10 entities/second
- Search operations: <100ms average
- Large metadata: <2000ms for 100KB objects
- Concurrent operations: No data corruption

## Extending the Framework

### Adding New Validators

1. Create a new validator class inheriting from `BaseValidator`:

```python
from .base import BaseValidator, ValidationResult, ValidationStatus

class MyCustomValidator(BaseValidator):
    def __init__(self):
        super().__init__("MyCustomValidator")
    
    async def my_test_method(self):
        # Your test logic here
        assert some_condition, "Test failed"
    
    async def run_validation(self) -> List[ValidationResult]:
        return [
            await self.run_test("my_test", self.my_test_method)
        ]
```

2. Add it to the validation framework:

```python
framework.add_validator(MyCustomValidator())
```

### Adding New Test Data Types

Extend the `TestDataGenerator` class:

```python
def generate_my_entity_type(self, client_id: str) -> TestEntity:
    return TestEntity(
        id=str(uuid.uuid4()),
        client_user_id=client_id,
        name="My Entity",
        entity_type="my_type",
        # ... other fields
    )
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `DATABASE_URL_DIRECT` is correct
   - Ensure database is running and accessible
   - Check network connectivity

2. **Schema Validation Failures**
   - Ensure memory system tables are created
   - Run database migrations if needed
   - Check table permissions

3. **Performance Issues**
   - Check database performance
   - Verify adequate system resources
   - Consider database indexing

4. **API Endpoint Failures**
   - Verify services are running
   - Check port availability
   - Validate service configurations

### Debug Mode

Run with verbose logging for detailed information:

```bash
python tests/memory_validation/run_validation.py --verbose
```

### Selective Testing

To run only specific validation components, modify the framework setup in the runner scripts or create custom test scripts using individual validators.

## Integration with CI/CD

The validation framework is designed for integration with continuous integration:

```bash
# In your CI pipeline
python tests/memory_validation/run_validation.py --save-report --report-dir ./artifacts/
```

The exit codes and report files can be used to determine deployment readiness and track validation history over time.
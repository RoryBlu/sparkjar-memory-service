#!/usr/bin/env python3
"""
Run data integrity validation for memory system.

This script executes comprehensive data integrity tests to validate:
- Entity uniqueness and deduplication
- Client data isolation 
- Referential integrity maintenance
- Schema compliance
- Concurrent operation handling
- Large data handling
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent

from tests.memory_validation.base import ValidationFramework, setup_validation_logging
from tests.memory_validation.data_integrity_validator import DataIntegrityValidator
from tests.memory_validation.health_checker import MemorySystemHealthChecker

async def main():
    """Run data integrity validation suite."""
    # Set up logging
    logger = setup_validation_logging(logging.INFO)
    logger.info("Starting Memory System Data Integrity Validation")
    
    # Check for database URL
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL_DIRECT or DATABASE_URL environment variable must be set")
        logger.error("Example: export DATABASE_URL_DIRECT='postgresql+asyncpg://user:pass@localhost/dbname'")
        return 1
    
    # Create validation framework
    framework = ValidationFramework("Memory System Data Integrity Validation")
    
    # Add health checker first to ensure system is ready
    health_checker = MemorySystemHealthChecker()
    framework.add_validator(health_checker)
    
    # Add data integrity validator
    integrity_validator = DataIntegrityValidator(database_url)
    framework.add_validator(integrity_validator)
    
    try:
        # Run all validations
        report = await framework.run_all_validations()
        
        # Print summary
        framework.print_summary(report)
        
        # Return appropriate exit code
        if report.failed_tests > 0:
            logger.error(f"Data integrity validation failed: {report.failed_tests} tests failed")
            return 1
        elif report.warning_tests > 0:
            logger.warning(f"Data integrity validation completed with warnings: {report.warning_tests} warnings")
            return 0
        else:
            logger.info("Data integrity validation passed successfully!")
            return 0
            
    except Exception as e:
        logger.error(f"Data integrity validation failed with exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
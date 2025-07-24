#!/usr/bin/env python3
"""
Run scalability validation tests for the memory system.

This script runs comprehensive scalability tests including:
- Large dataset performance (6.1)
- Cleanup and maintenance operations (6.2) 
- System resource limits measurement (6.3)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent

from tests.memory_validation.scalability_validator import ScalabilityValidator
from tests.memory_validation.base import ValidationFramework, setup_validation_logging

async def run_scalability_validation():
    """Run comprehensive scalability validation."""
    
    # Set up logging
    logger = setup_validation_logging(logging.INFO)
    logger.info("Starting Memory System Scalability Validation")
    
    # Check environment
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not configured. Please set DATABASE_URL or DATABASE_URL_DIRECT environment variable.")
        return False
    
    # Configuration for scalability tests
    config = {
        "database_url": database_url,
        "large_dataset_size": int(os.getenv("LARGE_DATASET_SIZE", "10000")),  # Start with 10K
        "max_test_entities": int(os.getenv("MAX_TEST_ENTITIES", "50000")),  # Max 50K for CI
        "batch_size": int(os.getenv("BATCH_SIZE", "1000")),
        "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "600")),  # 10 minutes
        "cleanup_enabled": os.getenv("CLEANUP_ENABLED", "true").lower() == "true",
        "concurrent_users": int(os.getenv("CONCURRENT_USERS", "20"))
    }
    
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    try:
        # Create validation framework
        framework = ValidationFramework("Memory System Scalability Validation")
        
        # Add scalability validator
        scalability_validator = ScalabilityValidator(config)
        framework.add_validator(scalability_validator)
        
        # Run validation
        logger.info("Running scalability validation tests...")
        report = await framework.run_all_validations()
        
        # Print summary
        framework.print_summary(report)
        
        # Save detailed report
        report_data = {
            "test_suite": report.test_suite_name,
            "timestamp": report.start_time.isoformat(),
            "duration_seconds": report.duration_seconds,
            "summary": {
                "total_tests": report.total_tests,
                "passed": report.passed_tests,
                "failed": report.failed_tests,
                "warnings": report.warning_tests,
                "success_rate": report.success_rate
            },
            "results": []
        }
        
        for result in report.results:
            result_data = {
                "test_name": result.test_name,
                "status": result.status.value,
                "execution_time_ms": result.execution_time_ms,
                "error_message": result.error_message,
                "warning_message": result.warning_message,
                "details": result.details
            }
            report_data["results"].append(result_data)
        
        # Save report to file
        report_file = "scalability_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Detailed report saved to {report_file}")
        
        # Return success status
        success = report.failed_tests == 0
        if success:
            logger.info("✅ All scalability validation tests passed!")
        else:
            logger.error(f"❌ {report.failed_tests} scalability validation tests failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Scalability validation failed with error: {e}", exc_info=True)
        return False

def main():
    """Main entry point."""
    success = asyncio.run(run_scalability_validation())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
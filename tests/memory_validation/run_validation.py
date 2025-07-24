#!/usr/bin/env python3
"""
Run comprehensive memory system validation.

This script executes the complete memory system validation suite including:
- System health and readiness checks
- Data integrity and consistency validation
- Client isolation verification
- Performance testing under load
- Error handling and recovery testing

Usage:
    python run_validation.py [--save-report] [--config-file CONFIG]

Environment Variables:
    DATABASE_URL_DIRECT - Direct database connection URL
    MEMORY_INTERNAL_API_URL - Internal API URL (default: http://localhost:8001)
    MEMORY_EXTERNAL_API_URL - External API URL (default: http://localhost:8443)
    MEMORY_MCP_API_URL - MCP API URL (default: http://localhost:8002)
    VALIDATION_TIMEOUT - Timeout in seconds (default: 30)
    TEST_CLIENT_COUNT - Number of test clients (default: 3)
    TEST_ENTITY_COUNT - Number of test entities (default: 50)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent

from tests.memory_validation.base import ValidationFramework, setup_validation_logging
from tests.memory_validation.comprehensive_validator import ComprehensiveMemoryValidator

def load_config_file(config_path: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        return {}

async def main():
    """Run comprehensive memory system validation."""
    parser = argparse.ArgumentParser(description="Run comprehensive memory system validation")
    parser.add_argument("--save-report", action="store_true", 
                       help="Save detailed validation report to file")
    parser.add_argument("--config-file", type=str,
                       help="Path to JSON configuration file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--report-dir", type=str, default=".",
                       help="Directory to save validation reports")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_validation_logging(log_level)
    logger.info("Starting Comprehensive Memory System Validation")
    
    # Load configuration
    config = {}
    if args.config_file:
        config = load_config_file(args.config_file)
    
    # Check for required environment variables
    database_url = config.get("database_url") or os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL_DIRECT or DATABASE_URL environment variable must be set")
        logger.error("Example: export DATABASE_URL_DIRECT='postgresql+asyncpg://user:pass@localhost/dbname'")
        return 1
    
    # Ensure database URL is in config
    if "database_url" not in config:
        config["database_url"] = database_url
    
    # Create validation framework
    framework = ValidationFramework("Comprehensive Memory System Validation")
    
    # Add comprehensive validator
    comprehensive_validator = ComprehensiveMemoryValidator(config)
    framework.add_validator(comprehensive_validator)
    
    try:
        # Run all validations
        logger.info("Executing comprehensive validation suite...")
        report = await framework.run_all_validations()
        
        # Print summary
        framework.print_summary(report)
        
        # Save detailed report if requested
        if args.save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"memory_validation_report_{timestamp}.json"
            report_path = Path(args.report_dir) / report_filename
            
            comprehensive_validator.save_report(str(report_path))
            logger.info(f"Detailed validation report saved to: {report_path}")
        
        # Print additional insights
        print(f"\n{'='*60}")
        print("VALIDATION INSIGHTS")
        print(f"{'='*60}")
        
        if report.failed_tests == 0:
            print("✅ All validation tests passed!")
            print("   The memory system appears ready for production use.")
        elif report.failed_tests <= 2:
            print("⚠️  Minor issues detected.")
            print("   Review failed tests and consider fixes before production use.")
        else:
            print("❌ Significant issues detected.")
            print("   The memory system requires fixes before production use.")
        
        print(f"\nTest Execution Summary:")
        print(f"   • Total Tests: {report.total_tests}")
        print(f"   • Passed: {report.passed_tests}")
        print(f"   • Failed: {report.failed_tests}")
        print(f"   • Warnings: {report.warning_tests}")
        print(f"   • Success Rate: {report.success_rate:.1%}")
        print(f"   • Duration: {report.duration_seconds:.1f} seconds")
        
        # Return appropriate exit code
        if report.failed_tests > 0:
            logger.error(f"Comprehensive validation failed: {report.failed_tests} tests failed")
            return 1
        elif report.warning_tests > 0:
            logger.warning(f"Comprehensive validation completed with warnings: {report.warning_tests} warnings")
            return 0
        else:
            logger.info("Comprehensive validation passed successfully!")
            return 0
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Comprehensive validation failed with exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
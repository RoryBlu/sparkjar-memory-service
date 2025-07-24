#!/usr/bin/env python3
"""
Run data migration validation tests for the memory system.

This script executes comprehensive migration validation tests including:
- Development to production migration procedures
- Relationship preservation during migration
- Schema version migration procedures
- Client data isolation during migration
- Migration rollback procedures
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

from tests.memory_validation.migration_validator import MigrationValidator
from tests.memory_validation.base import ValidationStatus

async def main():
    """Run data migration validation tests."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('migration_validation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Memory System Data Migration Validation")
    
    # Load configuration
    config = {
        "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
        "migration_timeout_seconds": int(os.getenv("MIGRATION_TIMEOUT", "600")),
        "backup_enabled": os.getenv("BACKUP_ENABLED", "true").lower() == "true",
        "test_large_datasets": os.getenv("TEST_LARGE_DATASETS", "false").lower() == "true"
    }
    
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Check prerequisites
    if not config["database_url"]:
        logger.error("DATABASE_URL not configured. Please set DATABASE_URL or DATABASE_URL_DIRECT environment variable.")
        return 1
    
    try:
        # Initialize migration validator
        migration_validator = MigrationValidator()
        
        # Run migration validation tests
        logger.info("Running data migration validation tests...")
        start_time = datetime.utcnow()
        
        results = await migration_validator.run_validation()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # Generate report
        report = {
            "test_suite": "Data Migration Validation",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "config": config,
            "migration_metadata": migration_validator.migration_metadata,
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
        
        # Save detailed report
        report_file = f"migration_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("DATA MIGRATION VALIDATION SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warning_tests}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Report saved to: {report_file}")
        
        # Print individual test results
        print("\nTEST RESULTS:")
        print("-" * 80)
        for result in results:
            status_symbol = "✓" if result.status == ValidationStatus.PASSED else "✗" if result.status == ValidationStatus.FAILED else "⚠"
            print(f"{status_symbol} {result.test_name:<50} {result.status.value:<10} {result.execution_time_ms:>8.1f}ms")
            
            if result.error_message:
                print(f"  Error: {result.error_message}")
            if result.warning_message:
                print(f"  Warning: {result.warning_message}")
        
        # Print migration metadata
        if migration_validator.migration_metadata:
            print("\nMIGRATION METADATA:")
            print("-" * 80)
            for key, value in migration_validator.migration_metadata.items():
                if isinstance(value, dict):
                    print(f"{key}:")
                    for sub_key, sub_value in value.items():
                        print(f"  {sub_key}: {sub_value}")
                else:
                    print(f"{key}: {value}")
        
        # Print failed tests details
        failed_results = [r for r in results if r.status == ValidationStatus.FAILED]
        if failed_results:
            print("\nFAILED TESTS DETAILS:")
            print("-" * 80)
            for result in failed_results:
                print(f"\n{result.test_name}:")
                print(f"  Error: {result.error_message}")
                if result.details:
                    print(f"  Details: {json.dumps(result.details, indent=4)}")
        
        # Print recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 80)
        
        if failed_tests == 0:
            print("✓ All data migration tests passed!")
            print("✓ System demonstrates reliable migration capabilities")
            print("✓ Data relationships preserved during migration")
            print("✓ Client isolation maintained during migration")
            print("✓ Schema version migration working correctly")
            print("✓ Migration rollback procedures functional")
        else:
            print(f"⚠ {failed_tests} migration tests failed")
            print("⚠ Review migration procedures and data integrity")
            print("⚠ Test migration rollback capabilities")
            print("⚠ Verify relationship preservation mechanisms")
            print("⚠ Check client data isolation during migration")
        
        if warning_tests > 0:
            print(f"⚠ {warning_tests} tests had warnings - review for potential improvements")
            print("⚠ Consider optimizing migration performance")
            print("⚠ Review backup and recovery procedures")
        
        # Return appropriate exit code
        return 0 if failed_tests == 0 else 1
        
    except Exception as e:
        logger.error(f"Migration validation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
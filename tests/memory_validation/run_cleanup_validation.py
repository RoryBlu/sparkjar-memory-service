#!/usr/bin/env python3
"""
Run cleanup and maintenance validation tests for the memory system.

This script executes comprehensive cleanup validation tests including:
- Generic entity cleanup procedures
- Entity grade decay mechanisms
- Database maintenance operations
- Cleanup performance impact measurement
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

from tests.memory_validation.cleanup_validator import CleanupValidator
from tests.memory_validation.base import ValidationStatus

async def main():
    """Run cleanup and maintenance validation tests."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cleanup_validation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Memory System Cleanup and Maintenance Validation")
    
    # Load configuration
    config = {
        "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
        "cleanup_batch_size": int(os.getenv("CLEANUP_BATCH_SIZE", "100")),
        "grade_decay_threshold": float(os.getenv("GRADE_DECAY_THRESHOLD", "0.1")),
        "generic_entity_age_days": int(os.getenv("GENERIC_ENTITY_AGE_DAYS", "30")),
        "maintenance_timeout_seconds": int(os.getenv("MAINTENANCE_TIMEOUT", "300"))
    }
    
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Check prerequisites
    if not config["database_url"]:
        logger.error("DATABASE_URL not configured. Please set DATABASE_URL or DATABASE_URL_DIRECT environment variable.")
        return 1
    
    try:
        # Initialize cleanup validator
        cleanup_validator = CleanupValidator(config)
        
        # Run cleanup validation tests
        logger.info("Running cleanup and maintenance validation tests...")
        start_time = datetime.utcnow()
        
        results = await cleanup_validator.run_validation()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # Generate report
        report = {
            "test_suite": "Cleanup and Maintenance Validation",
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
            "cleanup_metrics": cleanup_validator.cleanup_metrics,
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
        report_file = f"cleanup_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("CLEANUP AND MAINTENANCE VALIDATION SUMMARY")
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
            print(f"{status_symbol} {result.test_name:<40} {result.status.value:<10} {result.execution_time_ms:>8.1f}ms")
            
            if result.error_message:
                print(f"  Error: {result.error_message}")
            if result.warning_message:
                print(f"  Warning: {result.warning_message}")
        
        # Print cleanup metrics
        if cleanup_validator.cleanup_metrics:
            print("\nCLEANUP METRICS:")
            print("-" * 80)
            for metric_name, metrics in cleanup_validator.cleanup_metrics.items():
                print(f"{metric_name}:")
                for key, value in metrics.items():
                    if isinstance(value, list) and len(value) > 3:
                        print(f"  {key}: [{len(value)} items]")
                    else:
                        print(f"  {key}: {value}")
        
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
            print("✓ All cleanup and maintenance tests passed!")
            print("✓ System demonstrates good cleanup capabilities")
            print("✓ Entity grade decay mechanisms working correctly")
            print("✓ Database maintenance operations functional")
            print("✓ Cleanup performance impact is acceptable")
        else:
            print(f"⚠ {failed_tests} cleanup tests failed")
            print("⚠ Review cleanup procedures and maintenance operations")
            print("⚠ Consider optimizing cleanup performance")
            print("⚠ Verify entity grade decay mechanisms")
        
        if warning_tests > 0:
            print(f"⚠ {warning_tests} tests had warnings - review for potential improvements")
            print("⚠ Consider tuning cleanup parameters for better performance")
        
        # Return appropriate exit code
        return 0 if failed_tests == 0 else 1
        
    except Exception as e:
        logger.error(f"Cleanup validation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
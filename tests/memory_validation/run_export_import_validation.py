#!/usr/bin/env python3
"""
Run data export and import validation tests for the memory system.

This script executes comprehensive export/import validation tests including:
- Complete client data export procedures
- Data import with integrity validation
- Large dataset export/import performance
- Export completeness verification
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

from tests.memory_validation.export_import_validator import ExportImportValidator
from tests.memory_validation.base import ValidationStatus

async def main():
    """Run data export and import validation tests."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('export_import_validation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Memory System Data Export/Import Validation")
    
    # Load configuration
    config = {
        "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
        "export_batch_size": int(os.getenv("EXPORT_BATCH_SIZE", "1000")),
        "import_batch_size": int(os.getenv("IMPORT_BATCH_SIZE", "1000")),
        "export_timeout_seconds": int(os.getenv("EXPORT_TIMEOUT", "300")),
        "temp_dir": os.getenv("TEMP_DIR", "/tmp")
    }
    
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Check prerequisites
    if not config["database_url"]:
        logger.error("DATABASE_URL not configured. Please set DATABASE_URL or DATABASE_URL_DIRECT environment variable.")
        return 1
    
    try:
        # Initialize export/import validator
        export_import_validator = ExportImportValidator(config)
        
        # Run export/import validation tests
        logger.info("Running data export/import validation tests...")
        start_time = datetime.utcnow()
        
        results = await export_import_validator.run_validation()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # Generate report
        report = {
            "test_suite": "Data Export/Import Validation",
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
            "export_import_metrics": export_import_validator.export_import_metrics,
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
        report_file = f"export_import_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("DATA EXPORT/IMPORT VALIDATION SUMMARY")
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
        
        # Print export/import metrics
        if export_import_validator.export_import_metrics:
            print("\nEXPORT/IMPORT METRICS:")
            print("-" * 80)
            for metric_name, metrics in export_import_validator.export_import_metrics.items():
                print(f"{metric_name}:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
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
            print("✓ All data export/import tests passed!")
            print("✓ System demonstrates reliable export/import capabilities")
            print("✓ Data integrity maintained during export/import")
            print("✓ Export completeness verified")
            print("✓ Large dataset export/import working correctly")
        else:
            print(f"⚠ {failed_tests} export/import tests failed")
            print("⚠ Review export/import procedures and data integrity")
            print("⚠ Verify export completeness mechanisms")
            print("⚠ Check import validation procedures")
            print("⚠ Test large dataset export/import performance")
        
        if warning_tests > 0:
            print(f"⚠ {warning_tests} tests had warnings - review for potential improvements")
            print("⚠ Consider optimizing export/import performance")
            print("⚠ Review temporary file cleanup procedures")
        
        # Return appropriate exit code
        return 0 if failed_tests == 0 else 1
        
    except Exception as e:
        logger.error(f"Export/import validation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
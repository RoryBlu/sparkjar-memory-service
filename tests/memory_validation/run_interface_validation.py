#!/usr/bin/env python3
"""
Run interface consistency validation for the memory system.

This script executes comprehensive interface consistency tests including:
- CrewAI tool integration validation
- FastAPI endpoint consistency testing
- MCP interface compliance validation
- Cross-interface data consistency verification
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

from tests.memory_validation.interface_consistency_validator import InterfaceConsistencyValidator
from tests.memory_validation.base import ValidationStatus

async def main():
    """Run interface consistency validation tests."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('interface_consistency_validation.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Memory System Interface Consistency Validation")
    
    # Load configuration
    config = {
        "database_url": os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL"),
        "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
        "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
        "mcp_api_url": os.getenv("MEMORY_MCP_API_URL", "http://localhost:8002"),
        "mcp_registry_url": os.getenv("MCP_REGISTRY_URL", "http://localhost:8001"),
        "api_secret_key": os.getenv("API_SECRET_KEY", "test_secret_key"),
        "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
        "test_client_id": "interface_validation_client"
    }
    
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    try:
        # Initialize interface consistency validator
        interface_validator = InterfaceConsistencyValidator(config)
        
        # Run interface consistency tests
        logger.info("Running interface consistency validation...")
        start_time = datetime.utcnow()
        
        results = await interface_validator.run_validation()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Analyze results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # Generate report
        report = {
            "test_suite": "Interface Consistency Validation",
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
        report_file = f"interface_consistency_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*80)
        print("INTERFACE CONSISTENCY VALIDATION SUMMARY")
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
        
        # Print interface-specific summaries
        comprehensive_result = next((r for r in results if r.test_name == "comprehensive_interface_validation"), None)
        if comprehensive_result and comprehensive_result.details:
            validation_results = comprehensive_result.details.get("validation_results", {})
            
            print("\nINTERFACE-SPECIFIC RESULTS:")
            print("-" * 80)
            
            for interface_name, interface_results in validation_results.items():
                print(f"\n{interface_name.upper()}:")
                print(f"  Total Tests: {interface_results['total_tests']}")
                print(f"  Passed: {interface_results['passed']}")
                print(f"  Failed: {interface_results['failed']}")
                print(f"  Warnings: {interface_results['warnings']}")
                
                if interface_results['failed'] > 0:
                    failed_interface_tests = [
                        r for r in interface_results['results']
                        if r.status == ValidationStatus.FAILED
                    ]
                    print(f"  Failed Tests: {[r.test_name for r in failed_interface_tests]}")
        
        # Print recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 80)
        
        if failed_tests == 0:
            print("✓ All interface consistency tests passed!")
            print("✓ Memory system interfaces are consistent and reliable")
            print("✓ Ready for production multi-interface usage")
        else:
            print(f"⚠ {failed_tests} interface consistency tests failed")
            print("⚠ Review interface implementations for consistency")
            print("⚠ Ensure all interfaces handle the same operations identically")
            print("⚠ Verify authentication and error handling consistency")
        
        if warning_tests > 0:
            print(f"⚠ {warning_tests} tests had warnings - review for potential improvements")
        
        # Interface-specific recommendations
        if comprehensive_result and comprehensive_result.details:
            validation_results = comprehensive_result.details.get("validation_results", {})
            
            for interface_name, interface_results in validation_results.items():
                if interface_results['failed'] > 0:
                    print(f"⚠ {interface_name}: {interface_results['failed']} tests failed - review implementation")
                elif interface_results['warnings'] > 0:
                    print(f"⚠ {interface_name}: {interface_results['warnings']} warnings - consider improvements")
        
        # Return appropriate exit code
        return 0 if failed_tests == 0 else 1
        
    except Exception as e:
        logger.error(f"Interface consistency validation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
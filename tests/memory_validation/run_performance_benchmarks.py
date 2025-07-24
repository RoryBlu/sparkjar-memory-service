#!/usr/bin/env python3
"""
Run performance benchmarking tests for the memory system.

This script executes comprehensive performance tests including:
- Text processing performance across different sizes
- Concurrent operation handling
- Search and retrieval performance
- Resource usage monitoring

Usage:
    python run_performance_benchmarks.py [--save-report] [--config-file CONFIG]

Environment Variables:
    DATABASE_URL_DIRECT - Direct database connection URL
    VALIDATION_TIMEOUT - Timeout in seconds (default: 60)
    TEST_ENTITY_COUNT - Number of test entities (default: 1000)
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
from tests.memory_validation.performance_benchmarker import PerformanceBenchmarker

def load_config_file(config_path: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        return {}

async def main():
    """Run performance benchmarking tests."""
    parser = argparse.ArgumentParser(description="Run memory system performance benchmarks")
    parser.add_argument("--save-report", action="store_true", 
                       help="Save detailed benchmark report to file")
    parser.add_argument("--config-file", type=str,
                       help="Path to JSON configuration file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--report-dir", type=str, default=".",
                       help="Directory to save benchmark reports")
    parser.add_argument("--test-size", choices=["small", "medium", "large"], default="medium",
                       help="Test size: small (100 entities), medium (1000), large (5000)")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_validation_logging(log_level)
    logger.info("Starting Memory System Performance Benchmarking")
    
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
    
    # Set test size based on argument
    test_sizes = {
        "small": 100,
        "medium": 1000,
        "large": 5000
    }
    config["test_entity_count"] = test_sizes[args.test_size]
    
    # Extend timeout for performance tests
    config["timeout_seconds"] = int(os.getenv("VALIDATION_TIMEOUT", "120"))
    
    # Create validation framework
    framework = ValidationFramework("Memory System Performance Benchmarking")
    
    # Add performance benchmarker
    benchmarker = PerformanceBenchmarker(config)
    framework.add_validator(benchmarker)
    
    try:
        # Run all performance tests
        logger.info(f"Executing performance benchmarks with {args.test_size} test size...")
        logger.info(f"Test configuration: {config['test_entity_count']} entities, {config['timeout_seconds']}s timeout")
        
        report = await framework.run_all_validations()
        
        # Print summary
        framework.print_summary(report)
        
        # Print performance insights
        print(f"\n{'='*60}")
        print("PERFORMANCE BENCHMARK RESULTS")
        print(f"{'='*60}")
        
        # Analyze results for performance insights
        performance_summary = {}
        for result in report.results:
            if hasattr(result, 'details') and isinstance(result.details, dict):
                if 'operations_per_second' in result.details:
                    performance_summary[result.test_name] = {
                        'ops_per_second': result.details.get('operations_per_second', 0),
                        'avg_response_ms': result.details.get('avg_response_time_ms', 0),
                        'p95_response_ms': result.details.get('p95_response_time_ms', 0),
                        'error_rate': result.details.get('error_rate', 0)
                    }
        
        if performance_summary:
            print("\nPerformance Metrics:")
            for test_name, metrics in performance_summary.items():
                print(f"\n{test_name.replace('_', ' ').title()}:")
                print(f"  • Operations/sec: {metrics['ops_per_second']:.1f}")
                print(f"  • Avg Response: {metrics['avg_response_ms']:.1f}ms")
                print(f"  • P95 Response: {metrics['p95_response_ms']:.1f}ms")
                print(f"  • Error Rate: {metrics['error_rate']:.1%}")
        
        # Performance assessment
        if report.failed_tests == 0 and report.warning_tests == 0:
            print("\n✅ All performance benchmarks passed!")
            print("   The memory system meets performance requirements.")
        elif report.failed_tests == 0:
            print("\n⚠️  Performance benchmarks completed with warnings.")
            print("   Some performance metrics may need optimization.")
        else:
            print("\n❌ Performance benchmarks failed.")
            print("   Significant performance issues detected.")
        
        # Save detailed report if requested
        if args.save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"performance_benchmark_report_{timestamp}.json"
            report_path = Path(args.report_dir) / report_filename
            
            # Create detailed report
            detailed_report = {
                "timestamp": timestamp,
                "test_size": args.test_size,
                "config": config,
                "summary": {
                    "total_tests": report.total_tests,
                    "passed_tests": report.passed_tests,
                    "failed_tests": report.failed_tests,
                    "warning_tests": report.warning_tests,
                    "success_rate": report.success_rate,
                    "duration_seconds": report.duration_seconds
                },
                "performance_metrics": performance_summary,
                "detailed_results": [
                    {
                        "test_name": r.test_name,
                        "status": r.status.value,
                        "execution_time_ms": r.execution_time_ms,
                        "error_message": r.error_message,
                        "warning_message": r.warning_message,
                        "details": r.details
                    }
                    for r in report.results
                ]
            }
            
            with open(report_path, 'w') as f:
                json.dump(detailed_report, f, indent=2, default=str)
            
            logger.info(f"Detailed performance report saved to: {report_path}")
        
        print(f"\nBenchmark Execution Summary:")
        print(f"   • Total Tests: {report.total_tests}")
        print(f"   • Passed: {report.passed_tests}")
        print(f"   • Failed: {report.failed_tests}")
        print(f"   • Warnings: {report.warning_tests}")
        print(f"   • Success Rate: {report.success_rate:.1%}")
        print(f"   • Duration: {report.duration_seconds:.1f} seconds")
        
        # Return appropriate exit code
        if report.failed_tests > 0:
            logger.error(f"Performance benchmarking failed: {report.failed_tests} tests failed")
            return 1
        elif report.warning_tests > 0:
            logger.warning(f"Performance benchmarking completed with warnings: {report.warning_tests} warnings")
            return 0
        else:
            logger.info("Performance benchmarking passed successfully!")
            return 0
            
    except KeyboardInterrupt:
        logger.info("Performance benchmarking interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Performance benchmarking failed with exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
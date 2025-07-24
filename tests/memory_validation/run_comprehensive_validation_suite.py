#!/usr/bin/env python3
"""
Run the complete memory system validation suite.

This script executes all validation components in sequence:
1. Health checks and system readiness
2. Data integrity and consistency validation
3. Performance benchmarking
4. Error simulation and recovery testing
5. Interface consistency validation
6. Scalability testing

Usage:
    python run_comprehensive_validation_suite.py [--save-report] [--verbose]

Environment Variables:
    DATABASE_URL_DIRECT - Direct database connection URL (required)
    MEMORY_INTERNAL_API_URL - Internal API URL (default: http://localhost:8001)
    MEMORY_EXTERNAL_API_URL - External API URL (default: http://localhost:8443)
    MEMORY_MCP_API_URL - MCP API URL (default: http://localhost:8002)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent

from tests.memory_validation.base import ValidationFramework, setup_validation_logging, ValidationReport
from tests.memory_validation.health_checker import MemorySystemHealthChecker
from tests.memory_validation.data_integrity_validator import DataIntegrityValidator
from tests.memory_validation.performance_benchmarker import PerformanceBenchmarker
from tests.memory_validation.error_simulator import ErrorSimulator
from tests.memory_validation.interface_consistency_validator import InterfaceConsistencyValidator
from tests.memory_validation.scalability_validator import ScalabilityValidator
from tests.memory_validation.backup_validator import BackupValidator
from tests.memory_validation.migration_validator import MigrationValidator

class ComprehensiveValidationSuite:
    """Orchestrates the complete memory system validation suite."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation components and collect results."""
        self.start_time = datetime.now()
        self.logger.info("Starting comprehensive memory system validation suite")
        
        validation_components = [
            ("Health Checks", self._run_health_checks),
            ("Data Integrity", self._run_data_integrity_validation),
            ("Performance Benchmarks", self._run_performance_benchmarks),
            ("Error Simulation", self._run_error_simulation),
            ("Interface Consistency", self._run_interface_validation),
            ("Scalability Testing", self._run_scalability_validation),
            ("Backup & Migration", self._run_backup_migration_validation),
        ]
        
        total_passed = 0
        total_failed = 0
        total_warnings = 0
        total_tests = 0
        
        for component_name, validation_func in validation_components:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"RUNNING: {component_name}")
            self.logger.info(f"{'='*60}")
            
            try:
                result = await validation_func()
                self.results[component_name] = result
                
                # Aggregate results
                if isinstance(result, dict) and 'summary' in result:
                    summary = result['summary']
                    total_passed += summary.get('passed', 0)
                    total_failed += summary.get('failed', 0)
                    total_warnings += summary.get('warnings', 0)
                    total_tests += summary.get('total', 0)
                
                self.logger.info(f"✅ {component_name} completed")
                
            except Exception as e:
                self.logger.error(f"❌ {component_name} failed: {e}")
                self.logger.error(traceback.format_exc())
                self.results[component_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                total_failed += 1
                total_tests += 1
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Create comprehensive summary
        summary = {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': duration,
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_failed,
            'warning_tests': total_warnings,
            'success_rate': (total_passed / total_tests) if total_tests > 0 else 0,
            'components': list(self.results.keys()),
            'results': self.results,
            'config': self.config
        }
        
        return summary
    
    async def _run_health_checks(self) -> Dict[str, Any]:
        """Run system health validation."""
        framework = ValidationFramework("Health Checks")
        health_checker = MemorySystemHealthChecker(self.config)
        framework.add_validator(health_checker)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_data_integrity_validation(self) -> Dict[str, Any]:
        """Run data integrity validation."""
        framework = ValidationFramework("Data Integrity")
        integrity_validator = DataIntegrityValidator(self.config)
        framework.add_validator(integrity_validator)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarking."""
        framework = ValidationFramework("Performance Benchmarks")
        performance_benchmarker = PerformanceBenchmarker(self.config)
        framework.add_validator(performance_benchmarker)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_error_simulation(self) -> Dict[str, Any]:
        """Run error simulation and recovery testing."""
        framework = ValidationFramework("Error Simulation")
        error_simulator = ErrorSimulator(self.config)
        framework.add_validator(error_simulator)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_interface_validation(self) -> Dict[str, Any]:
        """Run interface consistency validation."""
        framework = ValidationFramework("Interface Consistency")
        interface_validator = InterfaceConsistencyValidator(self.config)
        framework.add_validator(interface_validator)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_scalability_validation(self) -> Dict[str, Any]:
        """Run scalability testing."""
        framework = ValidationFramework("Scalability Testing")
        scalability_validator = ScalabilityValidator(self.config)
        framework.add_validator(scalability_validator)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    async def _run_backup_migration_validation(self) -> Dict[str, Any]:
        """Run backup and migration validation."""
        framework = ValidationFramework("Backup & Migration")
        backup_validator = BackupValidator(self.config)
        migration_validator = MigrationValidator(self.config)
        
        framework.add_validator(backup_validator)
        framework.add_validator(migration_validator)
        
        report = await framework.run_all_validations()
        return {
            'status': 'passed' if report.failed_tests == 0 else 'failed',
            'summary': {
                'total': report.total_tests,
                'passed': report.passed_tests,
                'failed': report.failed_tests,
                'warnings': report.warning_tests
            },
            'details': report.results,
            'duration_seconds': report.duration_seconds
        }
    
    def save_report(self, report_path: str, results: Dict[str, Any]):
        """Save comprehensive validation report to file."""
        try:
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"Comprehensive validation report saved to: {report_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of all validation results."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE MEMORY SYSTEM VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        print(f"Start Time: {results['start_time']}")
        print(f"End Time: {results['end_time']}")
        print(f"Duration: {results['duration_seconds']:.1f} seconds")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Warnings: {results['warning_tests']}")
        print(f"Success Rate: {results['success_rate']:.1%}")
        
        print(f"\n{'='*80}")
        print("COMPONENT RESULTS")
        print(f"{'='*80}")
        
        for component_name, component_result in results['results'].items():
            status = component_result.get('status', 'unknown')
            if status == 'passed':
                status_icon = "✅"
            elif status == 'failed':
                status_icon = "❌"
            else:
                status_icon = "⚠️"
            
            print(f"{status_icon} {component_name}: {status.upper()}")
            
            if 'summary' in component_result:
                summary = component_result['summary']
                print(f"   Tests: {summary.get('total', 0)} | "
                      f"Passed: {summary.get('passed', 0)} | "
                      f"Failed: {summary.get('failed', 0)} | "
                      f"Warnings: {summary.get('warnings', 0)}")
            
            if 'error' in component_result:
                print(f"   Error: {component_result['error']}")
        
        print(f"\n{'='*80}")
        print("OVERALL ASSESSMENT")
        print(f"{'='*80}")
        
        if results['failed_tests'] == 0:
            print("🎉 EXCELLENT: All validation tests passed!")
            print("   The memory system is ready for production use.")
            print("   All components are functioning correctly.")
        elif results['failed_tests'] <= 3:
            print("⚠️  GOOD: Minor issues detected.")
            print("   Most validation tests passed successfully.")
            print("   Review failed tests and consider fixes before production.")
        elif results['failed_tests'] <= 10:
            print("⚠️  MODERATE: Several issues detected.")
            print("   Some validation tests failed.")
            print("   Address failed tests before production deployment.")
        else:
            print("❌ CRITICAL: Significant issues detected.")
            print("   Many validation tests failed.")
            print("   The memory system requires substantial fixes before production.")
        
        print(f"\n{'='*80}")

async def main():
    """Run the comprehensive validation suite."""
    parser = argparse.ArgumentParser(description="Run comprehensive memory system validation suite")
    parser.add_argument("--save-report", action="store_true", 
                       help="Save detailed validation report to file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--report-dir", type=str, default=".",
                       help="Directory to save validation reports")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_validation_logging(log_level)
    
    # Check for required environment variables
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL_DIRECT or DATABASE_URL environment variable must be set")
        logger.error("Example: export DATABASE_URL_DIRECT='postgresql+asyncpg://user:pass@localhost/dbname'")
        return 1
    
    # Build configuration
    config = {
        "database_url": database_url,
        "internal_api_url": os.getenv("MEMORY_INTERNAL_API_URL", "http://localhost:8001"),
        "external_api_url": os.getenv("MEMORY_EXTERNAL_API_URL", "http://localhost:8443"),
        "mcp_api_url": os.getenv("MEMORY_MCP_API_URL", "http://localhost:8002"),
        "timeout_seconds": int(os.getenv("VALIDATION_TIMEOUT", "30")),
        "test_client_count": int(os.getenv("TEST_CLIENT_COUNT", "3")),
        "test_entity_count": int(os.getenv("TEST_ENTITY_COUNT", "50"))
    }
    
    # Create and run comprehensive validation suite
    suite = ComprehensiveValidationSuite(config)
    
    try:
        logger.info("Starting comprehensive memory system validation suite...")
        results = await suite.run_all_validations()
        
        # Print summary
        suite.print_summary(results)
        
        # Save detailed report if requested
        if args.save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"comprehensive_validation_report_{timestamp}.json"
            report_path = Path(args.report_dir) / report_filename
            suite.save_report(str(report_path), results)
        
        # Return appropriate exit code
        if results['failed_tests'] > 0:
            logger.error(f"Comprehensive validation failed: {results['failed_tests']} tests failed")
            return 1
        elif results['warning_tests'] > 0:
            logger.warning(f"Comprehensive validation completed with warnings: {results['warning_tests']} warnings")
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
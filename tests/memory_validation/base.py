"""Base classes and interfaces for memory system validation."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid

class ValidationStatus(str, Enum):
    """Status of validation tests."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    status: ValidationStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASSED

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    test_name: str
    operations_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    total_operations: int
    resource_usage: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    test_suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    skipped_tests: int
    results: List[ValidationResult] = field(default_factory=list)
    health_checks: List[HealthCheckResult] = field(default_factory=list)
    benchmarks: List[BenchmarkResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or logging.getLogger(f"validation.{name}")
        self.results: List[ValidationResult] = []
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> ValidationResult:
        """Run a single test and record the result."""
        start_time = time.perf_counter()
        
        try:
            self.logger.info(f"Running test: {test_name}")
            await test_func(*args, **kwargs)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            result = ValidationResult(
                test_name=test_name,
                status=ValidationStatus.PASSED,
                execution_time_ms=execution_time
            )
            
            self.logger.info(f"Test passed: {test_name} ({execution_time:.2f}ms)")
            
        except AssertionError as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            result = ValidationResult(
                test_name=test_name,
                status=ValidationStatus.FAILED,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
            
            self.logger.error(f"Test failed: {test_name} - {e}")
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            result = ValidationResult(
                test_name=test_name,
                status=ValidationStatus.FAILED,
                execution_time_ms=execution_time,
                error_message=f"Unexpected error: {str(e)}"
            )
            
            self.logger.error(f"Test error: {test_name} - {e}", exc_info=True)
        
        self.results.append(result)
        return result
    
    @abstractmethod
    async def run_validation(self) -> List[ValidationResult]:
        """Run all validation tests for this validator."""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        
        return {
            "validator": self.name,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": passed / total if total > 0 else 0.0,
            "avg_execution_time_ms": sum(r.execution_time_ms for r in self.results) / total if total > 0 else 0.0
        }

class ValidationFramework:
    """Main validation framework coordinator."""
    
    def __init__(self, name: str = "Memory System Validation"):
        self.name = name
        self.logger = logging.getLogger("validation.framework")
        self.validators: List[BaseValidator] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def add_validator(self, validator: BaseValidator):
        """Add a validator to the framework."""
        self.validators.append(validator)
        self.logger.info(f"Added validator: {validator.name}")
    
    async def run_all_validations(self) -> ValidationReport:
        """Run all registered validators and generate a report."""
        self.start_time = datetime.utcnow()
        self.logger.info(f"Starting validation suite: {self.name}")
        
        all_results = []
        
        for validator in self.validators:
            self.logger.info(f"Running validator: {validator.name}")
            try:
                results = await validator.run_validation()
                all_results.extend(results)
                
                summary = validator.get_summary()
                self.logger.info(f"Validator {validator.name} completed: "
                               f"{summary['passed']}/{summary['total_tests']} passed "
                               f"({summary['success_rate']:.1%})")
                
            except Exception as e:
                self.logger.error(f"Validator {validator.name} failed: {e}", exc_info=True)
                # Add a failed result for the validator itself
                all_results.append(ValidationResult(
                    test_name=f"{validator.name}_execution",
                    status=ValidationStatus.FAILED,
                    execution_time_ms=0.0,
                    error_message=f"Validator execution failed: {str(e)}"
                ))
        
        self.end_time = datetime.utcnow()
        
        # Generate report
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
        failed_tests = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
        warning_tests = sum(1 for r in all_results if r.status == ValidationStatus.WARNING)
        skipped_tests = sum(1 for r in all_results if r.status == ValidationStatus.SKIPPED)
        
        report = ValidationReport(
            test_suite_name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            skipped_tests=skipped_tests,
            results=all_results
        )
        
        self.logger.info(f"Validation suite completed: {passed_tests}/{total_tests} passed "
                        f"({report.success_rate:.1%}) in {report.duration_seconds:.1f}s")
        
        return report
    
    def print_summary(self, report: ValidationReport):
        """Print a summary of the validation report."""
        print(f"\n{'='*60}")
        print(f"MEMORY SYSTEM VALIDATION REPORT")
        print(f"{'='*60}")
        print(f"Test Suite: {report.test_suite_name}")
        print(f"Duration: {report.duration_seconds:.1f} seconds")
        print(f"Total Tests: {report.total_tests}")
        print(f"Passed: {report.passed_tests}")
        print(f"Failed: {report.failed_tests}")
        print(f"Warnings: {report.warning_tests}")
        print(f"Skipped: {report.skipped_tests}")
        print(f"Success Rate: {report.success_rate:.1%}")
        
        if report.failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in report.results:
                if result.status == ValidationStatus.FAILED:
                    print(f"   • {result.test_name}: {result.error_message}")
        
        if report.warning_tests > 0:
            print(f"\n⚠️  WARNING TESTS:")
            for result in report.results:
                if result.status == ValidationStatus.WARNING:
                    print(f"   • {result.test_name}: {result.warning_message}")
        
        print(f"\n{'='*60}")

def setup_validation_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up logging for validation framework."""
    logger = logging.getLogger("validation")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(level)
    return logger
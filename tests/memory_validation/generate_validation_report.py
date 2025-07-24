#!/usr/bin/env python3
"""
Generate comprehensive validation report for memory system.

This script generates a detailed validation report including:
- Executive summary
- Test results by category
- Performance metrics
- Risk assessment
- Production readiness recommendation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class ValidationReportGenerator:
    """Generate comprehensive validation report from test results."""
    
    def __init__(self):
        self.report_sections = []
        self.metrics = {}
        self.issues = []
        self.recommendations = []
        
    def load_test_results(self, results_dir: str = ".") -> Dict[str, Any]:
        """Load all test result files from a directory."""
        results = {}
        result_files = [
            "health_validation_report.json",
            "data_integrity_validation_report.json",
            "performance_benchmark_report.json",
            "error_simulation_validation_report.json",
            "interface_validation_report.json",
            "scalability_validation_report.json",
            "backup_validation_report.json",
            "migration_validation_report.json",
            "comprehensive_validation_report.json"
        ]
        
        for filename in result_files:
            filepath = Path(results_dir) / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    component_name = filename.replace("_report.json", "")
                    results[component_name] = json.load(f)
        
        return results
    
    def generate_executive_summary(self, test_results: Dict[str, Any]) -> str:
        """Generate executive summary of validation results."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        critical_issues = []
        
        for component, data in test_results.items():
            if "summary" in data:
                summary = data["summary"]
                total_tests += summary.get("total_tests", 0)
                total_passed += summary.get("passed", 0)
                total_failed += summary.get("failed", 0)
            
            if "results" in data:
                for result in data["results"]:
                    if result.get("status") == "failed":
                        critical_issues.append({
                            "component": component,
                            "test": result.get("test_name"),
                            "error": result.get("error_message")
                        })
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        summary = f"""# Memory System Validation Report

## Executive Summary

**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

**Overall Assessment:** {"PASSED" if total_failed == 0 else "FAILED" if total_failed > 5 else "PASSED WITH WARNINGS"}

**Test Coverage:**
- Total Tests Executed: {total_tests}
- Tests Passed: {total_passed}
- Tests Failed: {total_failed}
- Success Rate: {success_rate:.1f}%

**Critical Issues:** {len(critical_issues)}

**Recommendation:** {"System ready for production" if total_failed == 0 else "Address critical issues before production deployment"}
"""
        return summary
    
    def generate_detailed_results(self, test_results: Dict[str, Any]) -> str:
        """Generate detailed results section."""
        sections = []
        
        # Health Checks
        if "health_validation" in test_results:
            health_data = test_results["health_validation"]
            sections.append(self._format_health_results(health_data))
        
        # Data Integrity
        if "data_integrity_validation" in test_results:
            integrity_data = test_results["data_integrity_validation"]
            sections.append(self._format_integrity_results(integrity_data))
        
        # Performance
        if "performance_benchmark" in test_results:
            perf_data = test_results["performance_benchmark"]
            sections.append(self._format_performance_results(perf_data))
        
        # Error Recovery
        if "error_simulation_validation" in test_results:
            error_data = test_results["error_simulation_validation"]
            sections.append(self._format_error_recovery_results(error_data))
        
        # Scalability
        if "scalability_validation" in test_results:
            scale_data = test_results["scalability_validation"]
            sections.append(self._format_scalability_results(scale_data))
        
        return "\n".join(sections)
    
    def _format_health_results(self, data: Dict[str, Any]) -> str:
        """Format health check results."""
        section = """
## Health Check Results

### Database Connectivity
"""
        if "results" in data:
            for result in data["results"]:
                if "database" in result.get("test_name", "").lower():
                    status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                    section += f"- {result.get('test_name')}: {status}\n"
                    if result.get("details"):
                        section += f"  - Response Time: {result['details'].get('response_time_ms', 'N/A')}ms\n"
        
        section += "\n### API Endpoints\n"
        for result in data.get("results", []):
            if "api" in result.get("test_name", "").lower():
                status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                section += f"- {result.get('test_name')}: {status}\n"
        
        return section
    
    def _format_integrity_results(self, data: Dict[str, Any]) -> str:
        """Format data integrity results."""
        section = """
## Data Integrity Results

### Entity Management
"""
        if "results" in data:
            for result in data["results"]:
                if "entity" in result.get("test_name", "").lower():
                    status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                    section += f"- {result.get('test_name')}: {status}\n"
                    if result.get("error_message"):
                        section += f"  - Error: {result['error_message']}\n"
        
        section += "\n### Client Isolation\n"
        for result in data.get("results", []):
            if "client" in result.get("test_name", "").lower():
                status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                section += f"- {result.get('test_name')}: {status}\n"
        
        return section
    
    def _format_performance_results(self, data: Dict[str, Any]) -> str:
        """Format performance benchmark results."""
        section = """
## Performance Results

### Response Time Benchmarks
"""
        if "results" in data:
            for result in data["results"]:
                if result.get("details") and "response_times" in result["details"]:
                    times = result["details"]["response_times"]
                    section += f"\n**{result.get('test_name')}:**\n"
                    section += f"- Average: {times.get('avg_ms', 'N/A')}ms\n"
                    section += f"- 95th Percentile: {times.get('p95_ms', 'N/A')}ms\n"
                    section += f"- 99th Percentile: {times.get('p99_ms', 'N/A')}ms\n"
        
        section += "\n### Throughput Metrics\n"
        for result in data.get("results", []):
            if result.get("details") and "operations_per_second" in result["details"]:
                ops = result["details"]["operations_per_second"]
                section += f"- {result.get('test_name')}: {ops:.1f} ops/sec\n"
        
        return section
    
    def _format_error_recovery_results(self, data: Dict[str, Any]) -> str:
        """Format error recovery results."""
        section = """
## Error Recovery Results

### Database Failure Recovery
"""
        if "results" in data:
            for result in data["results"]:
                if "database" in result.get("test_name", "").lower():
                    status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                    section += f"- {result.get('test_name')}: {status}\n"
                    if result.get("details") and "recovery_time_ms" in result["details"]:
                        section += f"  - Recovery Time: {result['details']['recovery_time_ms']}ms\n"
        
        section += "\n### Service Failure Handling\n"
        for result in data.get("results", []):
            if "service" in result.get("test_name", "").lower():
                status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                section += f"- {result.get('test_name')}: {status}\n"
        
        return section
    
    def _format_scalability_results(self, data: Dict[str, Any]) -> str:
        """Format scalability test results."""
        section = """
## Scalability Results

### Large Dataset Performance
"""
        if "results" in data:
            for result in data["results"]:
                if "large_dataset" in result.get("test_name", "").lower():
                    status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                    section += f"- Dataset Size Tested: {result.get('details', {}).get('dataset_size', 'N/A')} entities\n"
                    section += f"- Status: {status}\n"
                    if result.get("details"):
                        details = result["details"]
                        section += f"- Search Performance: {details.get('p95_response_time_ms', 'N/A')}ms (95th percentile)\n"
                        section += f"- Memory Usage: {details.get('memory_usage_mb', 'N/A')}MB\n"
        
        section += "\n### Concurrent User Capacity\n"
        for result in data.get("results", []):
            if "concurrent" in result.get("test_name", "").lower():
                status = "✅ PASSED" if result.get("status") == "passed" else "❌ FAILED"
                section += f"- Maximum Concurrent Users: {result.get('details', {}).get('max_concurrent_users', 'N/A')}\n"
                section += f"- Status: {status}\n"
        
        return section
    
    def generate_risk_assessment(self, test_results: Dict[str, Any]) -> str:
        """Generate risk assessment section."""
        risks = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        # Analyze results for risks
        for component, data in test_results.items():
            if "results" in data:
                for result in data["results"]:
                    if result.get("status") == "failed":
                        # Categorize risks
                        test_name = result.get("test_name", "")
                        if any(critical in test_name.lower() for critical in ["database", "security", "data_integrity"]):
                            risks["high"].append({
                                "component": component,
                                "issue": result.get("error_message", test_name)
                            })
                        elif any(moderate in test_name.lower() for moderate in ["performance", "concurrent"]):
                            risks["medium"].append({
                                "component": component,
                                "issue": result.get("error_message", test_name)
                            })
                        else:
                            risks["low"].append({
                                "component": component,
                                "issue": result.get("error_message", test_name)
                            })
        
        section = """
## Risk Assessment

### High Priority Risks
"""
        if risks["high"]:
            for risk in risks["high"]:
                section += f"- **{risk['component']}**: {risk['issue']}\n"
        else:
            section += "- No high priority risks identified\n"
        
        section += "\n### Medium Priority Risks\n"
        if risks["medium"]:
            for risk in risks["medium"]:
                section += f"- **{risk['component']}**: {risk['issue']}\n"
        else:
            section += "- No medium priority risks identified\n"
        
        section += "\n### Low Priority Risks\n"
        if risks["low"]:
            for risk in risks["low"]:
                section += f"- **{risk['component']}**: {risk['issue']}\n"
        else:
            section += "- No low priority risks identified\n"
        
        return section
    
    def generate_recommendations(self, test_results: Dict[str, Any]) -> str:
        """Generate recommendations section."""
        recommendations = []
        
        # Analyze results and generate recommendations
        total_failed = sum(
            data.get("summary", {}).get("failed", 0) 
            for data in test_results.values() 
            if "summary" in data
        )
        
        if total_failed == 0:
            recommendations.append("✅ System is ready for production deployment")
            recommendations.append("✅ All validation tests passed successfully")
            recommendations.append("📋 Establish regular monitoring and maintenance procedures")
            recommendations.append("📋 Set up automated validation runs for continuous monitoring")
        elif total_failed <= 3:
            recommendations.append("⚠️ Address minor issues before production deployment")
            recommendations.append("🔧 Fix failed validation tests")
            recommendations.append("📋 Re-run validation suite after fixes")
            recommendations.append("📋 Consider staging environment testing")
        else:
            recommendations.append("❌ System requires significant improvements before production")
            recommendations.append("🔧 Address all critical failures immediately")
            recommendations.append("🔧 Implement missing functionality")
            recommendations.append("📋 Conduct thorough code review")
            recommendations.append("📋 Re-run complete validation suite after fixes")
        
        section = """
## Recommendations

### Immediate Actions
"""
        for rec in recommendations[:2]:
            section += f"- {rec}\n"
        
        section += "\n### Follow-up Actions\n"
        for rec in recommendations[2:]:
            section += f"- {rec}\n"
        
        section += """
### Monitoring Setup
- Implement continuous health monitoring
- Set up performance alerting thresholds
- Create automated backup validation
- Schedule regular scalability assessments
"""
        
        return section
    
    def generate_full_report(self, results_dir: str = ".") -> str:
        """Generate complete validation report."""
        # Load all test results
        test_results = self.load_test_results(results_dir)
        
        if not test_results:
            return "# Memory System Validation Report\n\n**Error:** No test results found. Please run validation tests first."
        
        # Generate report sections
        report_sections = [
            self.generate_executive_summary(test_results),
            self.generate_detailed_results(test_results),
            self.generate_risk_assessment(test_results),
            self.generate_recommendations(test_results)
        ]
        
        # Add appendix
        report_sections.append("""
## Appendix

### Test Environment
- Database: PostgreSQL with pgvector extension
- Memory Service: FastAPI-based REST API
- Vector Storage: ChromaDB
- Test Framework: Custom Python-based validation suite

### Test Coverage
- Health Checks: Database, API endpoints, authentication
- Data Integrity: Entity management, client isolation, referential integrity
- Performance: Response times, throughput, concurrent operations
- Error Recovery: Database failures, service failures, resource exhaustion
- Scalability: Large datasets, concurrent users, resource limits
- Migration: Backup/restore, data export/import, schema updates

### Report Generation
- Generated: {}
- Generator Version: 1.0.0
- Test Suite Version: Memory System Validation v1.0
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')))
        
        return "\n".join(report_sections)
    
    def save_report(self, report_content: str, output_path: str = "memory_system_validation_report.md"):
        """Save report to file."""
        with open(output_path, 'w') as f:
            f.write(report_content)
        print(f"Report saved to: {output_path}")

def main():
    """Generate validation report."""
    generator = ValidationReportGenerator()
    
    # Generate report
    report = generator.generate_full_report()
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"memory_system_validation_report_{timestamp}.md"
    generator.save_report(report, output_filename)
    
    # Also save a latest version
    generator.save_report(report, "memory_system_validation_report_latest.md")
    
    print("\nValidation report generated successfully!")

if __name__ == "__main__":
    main()
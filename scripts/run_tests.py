#!/usr/bin/env python3
"""
Test Runner for Apex Tactics Integration Tests

Runs comprehensive test suites with proper environment setup and reporting.
"""

import sys
import os
import asyncio
import argparse
import subprocess
import time
from pathlib import Path

import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = structlog.get_logger()


class TestRunner:
    """Comprehensive test runner for Apex Tactics"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "tests"
        self.services_ready = False
    
    async def check_service_health(self) -> dict:
        """Check health of all required services"""
        import httpx
        
        services = {
            "game_engine": "http://localhost:8002/api/health",
            "mcp_gateway": "http://localhost:8004/health", 
            "ai_service": "http://localhost:8001/health"
        }
        
        health_status = {}
        
        for service_name, health_url in services.items():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(health_url)
                    health_status[service_name] = {
                        "healthy": response.status_code == 200,
                        "status_code": response.status_code,
                        "data": response.json() if response.status_code == 200 else None
                    }
                    
            except Exception as e:
                health_status[service_name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return health_status
    
    async def wait_for_services(self, timeout: int = 60) -> bool:
        """Wait for all services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            health_status = await self.check_service_health()
            
            all_healthy = all(
                service["healthy"] 
                for service in health_status.values()
            )
            
            if all_healthy:
                logger.info("All services are healthy")
                self.services_ready = True
                return True
            
            # Show which services are not ready
            unhealthy = [
                name for name, status in health_status.items()
                if not status["healthy"]
            ]
            
            logger.info(f"Waiting for services: {', '.join(unhealthy)}")
            await asyncio.sleep(2.0)
        
        logger.error("Services did not become ready within timeout")
        return False
    
    def run_pytest(self, test_pattern: str = None, markers: str = None, 
                   verbose: bool = True, fail_fast: bool = False,
                   output_file: str = None) -> int:
        """Run pytest with specified parameters"""
        
        cmd = ["python", "-m", "pytest"]
        
        if test_pattern:
            cmd.append(test_pattern)
        else:
            cmd.append(str(self.test_dir))
        
        if markers:
            cmd.extend(["-m", markers])
        
        if verbose:
            cmd.append("-v")
        
        if fail_fast:
            cmd.append("-x")
        
        if output_file:
            cmd.extend(["--junitxml", output_file])
        
        # Add coverage if requested
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )
            return result.returncode
        
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return 1
    
    async def run_integration_tests(self, args) -> int:
        """Run integration tests with service checks"""
        
        if args.check_services:
            if not await self.wait_for_services(args.service_timeout):
                if args.skip_service_check:
                    logger.warning("Services not ready, but continuing due to --skip-service-check")
                else:
                    logger.error("Services not ready, aborting tests")
                    return 1
        
        # Run tests
        return self.run_pytest(
            test_pattern=args.test_pattern,
            markers=args.markers,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            output_file=args.output_file
        )
    
    def run_unit_tests(self, args) -> int:
        """Run unit tests (fast, no service dependencies)"""
        return self.run_pytest(
            test_pattern="tests/unit" if Path("tests/unit").exists() else None,
            markers="unit" if not args.markers else f"unit and ({args.markers})",
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            output_file=args.output_file
        )
    
    def generate_test_report(self, output_dir: str = "test_reports"):
        """Generate comprehensive test report"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate HTML coverage report
        if Path("htmlcov").exists():
            logger.info(f"Coverage report available at: {Path('htmlcov/index.html').absolute()}")
        
        # Generate test results summary
        if Path("test_results.xml").exists():
            logger.info(f"JUnit XML report: {Path('test_results.xml').absolute()}")
        
        logger.info(f"Test reports generated in: {output_path.absolute()}")


async def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Apex Tactics Test Runner")
    
    # Test type selection
    parser.add_argument(
        "test_type",
        choices=["integration", "unit", "all", "performance", "smoke"],
        help="Type of tests to run"
    )
    
    # Test filtering
    parser.add_argument(
        "--test-pattern",
        help="Specific test file or pattern to run"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Pytest markers to filter tests (e.g., 'not slow')"
    )
    
    # Service management
    parser.add_argument(
        "--check-services",
        action="store_true",
        default=True,
        help="Check service health before running tests"
    )
    
    parser.add_argument(
        "--skip-service-check",
        action="store_true",
        help="Skip service health check and run tests anyway"
    )
    
    parser.add_argument(
        "--service-timeout",
        type=int,
        default=60,
        help="Timeout for waiting for services (seconds)"
    )
    
    # Test execution options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose test output"
    )
    
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first test failure"
    )
    
    parser.add_argument(
        "--output-file",
        help="Output file for JUnit XML results"
    )
    
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    runner = TestRunner()
    exit_code = 0
    
    try:
        if args.test_type == "unit":
            logger.info("Running unit tests...")
            exit_code = runner.run_unit_tests(args)
            
        elif args.test_type == "integration":
            logger.info("Running integration tests...")
            exit_code = await runner.run_integration_tests(args)
            
        elif args.test_type == "performance":
            logger.info("Running performance tests...")
            args.markers = "performance" if not args.markers else f"performance and ({args.markers})"
            exit_code = await runner.run_integration_tests(args)
            
        elif args.test_type == "smoke":
            logger.info("Running smoke tests...")
            args.markers = "not slow" if not args.markers else f"not slow and ({args.markers})"
            exit_code = await runner.run_integration_tests(args)
            
        elif args.test_type == "all":
            logger.info("Running all tests...")
            
            # Run unit tests first (faster)
            logger.info("=== Running Unit Tests ===")
            unit_exit_code = runner.run_unit_tests(args)
            
            if unit_exit_code != 0 and args.fail_fast:
                exit_code = unit_exit_code
            else:
                # Run integration tests
                logger.info("=== Running Integration Tests ===")
                integration_exit_code = await runner.run_integration_tests(args)
                exit_code = unit_exit_code or integration_exit_code
        
        # Generate report if requested
        if args.generate_report:
            runner.generate_test_report()
        
        # Summary
        if exit_code == 0:
            logger.info("✅ All tests passed!")
        else:
            logger.error(f"❌ Tests failed with exit code {exit_code}")
    
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        exit_code = 130
    
    except Exception as e:
        logger.error(f"Test runner error: {e}")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
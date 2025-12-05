#!/usr/bin/env python3
"""
Test runner script for the pytest testing framework.
"""
import os
import sys
import subprocess
from pathlib import Path


def setup_test_environment():
    """Setup test environment variables."""
    # Load test environment variables
    test_env_file = Path("tests/.env.test")
    if test_env_file.exists():
        with open(test_env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')


def run_unit_tests():
    """Run unit tests only."""
    setup_test_environment()
    cmd = ["python", "-m", "pytest", "tests/unit", "-m", "unit", "-v"]
    return subprocess.run(cmd)


def run_integration_tests():
    """Run integration tests only."""
    setup_test_environment()
    cmd = ["python", "-m", "pytest", "tests/integration", "-m", "integration", "-v"]
    return subprocess.run(cmd)


def run_all_tests():
    """Run all tests."""
    setup_test_environment()
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    return subprocess.run(cmd)


def run_coverage_report():
    """Run tests with coverage report."""
    setup_test_environment()
    cmd = ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=term"]
    return subprocess.run(cmd)


def main():
    """Main test runner function."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|all|coverage]")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "unit":
        result = run_unit_tests()
    elif test_type == "integration":
        result = run_integration_tests()
    elif test_type == "all":
        result = run_all_tests()
    elif test_type == "coverage":
        result = run_coverage_report()
    else:
        print(f"Unknown test type: {test_type}")
        print("Available options: unit, integration, all, coverage")
        sys.exit(1)
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
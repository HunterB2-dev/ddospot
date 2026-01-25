#!/usr/bin/env python3
"""
Test runner script for DDoSPoT test suite.
Provides convenient commands for running different test categories.
"""

import subprocess
import sys
from pathlib import Path

def run_tests(args):
    """Run pytest with given arguments"""
    test_dir = Path(__file__).parent
    cmd = ["python3", "-m", "pytest", str(test_dir)] + args
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("""
DDoSPoT Test Runner
═══════════════════════════════════════════════════════════════

Usage: ./run_tests.py [command] [options]

Commands:
  all            Run all tests
  core           Run core module tests (database, geolocation, etc)
  api            Run API endpoint tests
  security       Run security-specific tests
  cli            Run CLI tests
  quick          Run fast tests only (excludes slow/integration)
  integration    Run integration tests
  coverage       Run tests with coverage report
  verbose        Run all tests with verbose output
  
Examples:
  ./run_tests.py all
  ./run_tests.py security -v
  ./run_tests.py quick
  ./run_tests.py coverage
  ./run_tests.py api --tb=short
  
Pytest Options:
  -v, --verbose      Verbose output
  -s                 Show print statements
  -k KEYWORD         Run tests matching keyword
  --tb=short         Shorter traceback format
  -x, --exitfirst    Exit on first failure
  
See pytest --help for more options.
═══════════════════════════════════════════════════════════════
        """)
        return 1
    
    command = sys.argv[1]
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Map commands to pytest arguments
    commands = {
        'all': [],
        'core': ['tests/test_core_modules.py'] + extra_args,
        'api': ['tests/test_api_endpoints.py'] + extra_args,
        'security': ['tests/test_security.py', '-m', 'security'] + extra_args,
        'cli': ['tests/test_cli.py'] + extra_args,
        'quick': ['-m', 'not slow', '--ignore=tests/test_api_endpoints.py'] + extra_args,
        'integration': ['-m', 'integration'] + extra_args,
        'coverage': ['--cov=.', '--cov-report=html', '--cov-report=term'] + extra_args,
        'verbose': ['-v'] + extra_args,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print("Available commands: " + ", ".join(commands.keys()))
        return 1
    
    args = commands[command]
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main())


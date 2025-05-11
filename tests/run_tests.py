#!/usr/bin/env python3
"""
Test runner for the Garmin data downloader project
Run this script to execute all tests in the tests directory
"""

import os
import sys
import unittest
import argparse
import getpass
from pathlib import Path

# Set environment variable to indicate we're in test mode
os.environ['GARMIN_TEST_MODE'] = 'true'

# Add main project directory and tests directory to sys.path for robust imports
main_dir = str(Path(__file__).parent.parent)
tests_dir_path = str(Path(__file__).parent)
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)
if tests_dir_path not in sys.path:
    sys.path.insert(0, tests_dir_path)
# Remove src from sys.path if present
src_dir = os.path.join(main_dir, 'src')
if src_dir in sys.path:
    sys.path.remove(src_dir)

def run_all_tests():
    """Run all tests in the tests directory"""
    # Get the tests directory path
    tests_dir = Path(tests_dir_path)
    
    # Discover all tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=str(tests_dir), pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return success if all tests passed
    return 0 if result.wasSuccessful() else 1

def run_specific_tests(test_name):
    """Run a specific test module"""
    # Get the tests directory path
    tests_dir = Path(tests_dir_path)
    
    # Add pattern prefix if needed
    if not test_name.startswith('test_'):
        test_name = f'test_{test_name}'
    
    # Add .py extension if not provided
    if not test_name.endswith('.py'):
        test_name = f'{test_name}.py'
    
    # Check if the specified test file exists
    test_file = tests_dir / test_name
    if not test_file.exists():
        print(f"Error: Test file {test_file} not found.")
        return 1
    
    # Import the test module
    sys.path.append(str(tests_dir.parent))
    sys.path.append(str(tests_dir))
    
    # Import the test module and run it
    import importlib
    module_name = test_name[:-3]  # Remove .py extension
    test_module = importlib.import_module(module_name)
    
    # Run the tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromModule(test_module)
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return success if all tests passed
    return 0 if result.wasSuccessful() else 1

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run tests for the Garmin data downloader")
    parser.add_argument('test_name', nargs='?', help='Specific test to run (e.g., downloader, auth)')
    parser.add_argument('--use-mfa', action='store_true', help='Enable real MFA for authentication tests')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Configure test environment
    if args.use_mfa:
        print("Running with real MFA enabled. You may be prompted for MFA codes.")
        os.environ['GARMIN_USE_MFA'] = 'true'
    else:
        print("Running with MFA mocked (default test mode).")
        os.environ['GARMIN_USE_MFA'] = 'false'
    
    if args.test_name:
        return run_specific_tests(args.test_name)
    else:
        return run_all_tests()

if __name__ == "__main__":
    sys.exit(main())

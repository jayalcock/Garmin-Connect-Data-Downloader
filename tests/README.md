# Garmin Downloader Test Suite

This directory contains tests for the Garmin data downloader application. These tests validate the functionality of authentication, data retrieval, exporting, and other core features.

## Test Files

- `test_downloader.py`: Tests for the core downloader functions (credentials, exports)
- `test_auth.py`: Tests for Garmin Connect authentication functions
- `test_data_retrieval.py`: Tests for data retrieval and processing functions
- `test_daily_export.py`: Tests for the daily automated export functionality

## Running Tests

You can use the provided test runner script to run all tests or specific test modules:

### Run all tests:

```bash
python tests/run_tests.py
```

### Run a specific test module:

```bash
python tests/run_tests.py downloader
python tests/run_tests.py auth
python tests/run_tests.py data_retrieval
python tests/run_tests.py daily_export
```

## Test Dependencies

The tests use Python's built-in `unittest` framework and rely on the following modules:

- `unittest`: Core testing framework
- `unittest.mock`: For mocking external dependencies
- `datetime`: For date manipulation
- `pathlib`: For path handling

## Test Coverage

These tests cover the following areas:

1. **Credential Management**
   - Saving/loading credentials
   - Password encryption/decryption
   - Secure handling of user credentials

2. **Authentication**
   - Interactive and non-interactive Garmin Connect login
   - Error handling during authentication
   - MFA handling (simulated)

3. **Data Retrieval**
   - Fetching various types of health data
   - Date parsing and handling
   - Retrieving data for specific dates and date ranges

4. **Export Functionality**
   - CSV file creation and formatting
   - iCloud Drive integration
   - Field selection and data formatting

5. **Automation**
   - Daily export process
   - Error handling in automated scenarios
   - Notification system (simulated)

## Adding New Tests

To add new tests, simply create a new test file following the naming convention `test_*.py` and place it in this directory. The test runner will automatically discover and run your tests.

# Garmin Connect Data Downloader

This project allows you to automatically download your health and fitness data from Garmin Connect and save it as CSV files.

## Project Structure

```
Data download/
├── __init__.py               # Root init file for Python package
├── run_daily_export.py      # Script to run the daily export
├── run_manual_export.py     # Script to run manual export with MFA support
├── downloader.py            # Symlink to src/downloader.py for backward compatibility
├── setup.py                 # Python package setup file
├── APP_PASSWORD_GUIDE.md    # Instructions for setting up app passwords
├── src/                     # Source code directory
│   ├── __init__.py          # Package init file
│   ├── downloader.py        # Core functionality for connecting to Garmin Connect
│   ├── daily_export.py      # Daily automated export script
│   └── manual_export.py     # Manual export script with MFA support
├── tests/                   # Test directory
│   ├── __init__.py          # Test package init file
│   ├── run_tests.py         # Script to run all tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_daily_export.py # Daily export tests
│   ├── test_downloader.py   # Core downloader tests
│   ├── test_mfa.py          # MFA testing script
│   └── test_data_retrieval.py # Data retrieval tests
├── exports/                 # Directory for exported CSV files
│   ├── garmin_stats.csv     # Main CSV file with all data (each row is a date)
│   ├── archive/             # Archive of date-specific CSV files
│   └── garmin_stats_backup_*.csv # Daily backups in Nextcloud
└── logs/                    # Directory for log files
    └── auth_status.json     # Authentication status log
```

## Usage

1. **Daily Export (Automated)**: 
   ```
   python run_daily_export.py
   ```
   This script is designed for automated runs (e.g., via cron job) and will not prompt for MFA codes.

2. **Manual Export (with MFA support)**:
   ```
   python run_manual_export.py
   ```
   Use this when you're available to enter an MFA code if required.

3. **Running Tests**:
   ```
   cd tests
   python run_tests.py
   ```
   
   To run specific tests:
   ```
   python run_tests.py downloader
   ```
   
   To run tests with real MFA:
   ```
   python run_tests.py --use-mfa
   ```

## MFA Support

The system supports Multi-Factor Authentication (MFA) but needs to be explicitly enabled for interactive sessions. For automated runs, you should use an app password as described in the APP_PASSWORD_GUIDE.md file.

## Data Storage

The application stores all your Garmin Connect health data in a single CSV file:

- The main data file is `exports/garmin_stats.csv`
- Each row represents data for a specific date
- The file is automatically backed up to Nextcloud 
- Daily backups are created in Nextcloud as `garmin_stats_backup_YYYY-MM-DD.csv` 

### Legacy Data Migration

If you have existing date-specific CSV files from previous versions, you can merge them using:

```
python merge_csv_files.py
```

This will:
1. Merge all `garmin_stats_YYYY-MM-DD.csv` files into a single `garmin_stats.csv` file
2. Archive the original date-specific files in `exports/archive/`

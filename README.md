# Garmin Connect Data Downloader

This project allows you to automatically download your health and fitness data from Garmin Connect and save it as CSV files. It now includes OpenAI integration for analyzing your workout data.

## Project Structure

```
Data download/
├── __init__.py             # Root init file for Python package
├── garmin_sync.py          # Main implementation file (core functionality)
├── daily_export.py         # Symlink to src/daily_export.py script for automated export
├── manual_export.py        # Symlink to src/manual_export.py script with MFA support
├── download_today.sh       # Shell script to download today's activities
├── analyze_workout.py      # CLI tool for analyzing workout data with ChatGPT
├── setup.py                # Python package setup file
├── docs/                   # Documentation directory
│   ├── APP_PASSWORD_GUIDE.md    # Instructions for setting up app passwords
│   ├── BACKUP_LOCATION_CHANGES.md # Information on backup location changes
│   ├── CHANGELOG.md       # Project changelog
│   ├── OPENAI_INTEGRATION.md # Guide for using the OpenAI integration
│   └── README.md          # Additional documentation
├── src/                     # Source code directory
│   ├── __init__.py          # Package init file
│   ├── daily_export.py      # Daily automated export script
│   └── manual_export.py     # Manual export script with MFA support
├── utils/                   # Utility scripts and helper functions
│   ├── check_json.py        # JSON validation utility
│   ├── check_empty.py       # Check for empty data in exports
│   ├── merge_csv_files.py   # Utility to merge CSV files
│   ├── check_hrv.py         # HRV data validation utility
│   ├── dump_sleep_data.py   # Sleep data extraction utility
│   └── openai_integration.py # OpenAI integration for workout analysis
├── tests/                   # Test directory 
│   ├── __init__.py          # Test package init file
│   ├── run_tests.py         # Script to run all tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_daily_export.py # Daily export tests
│   ├── test_downloader.py   # Core downloader tests
│   ├── test_weight_data.py  # Weight data mapping tests
│   ├── test_mfa.py          # MFA testing script
│   └── test_data_retrieval.py # Data retrieval tests
├── utils/                   # Utility scripts 
│   ├── check_empty.py       # Check for empty fields in CSV exports
│   ├── check_hrv.py         # Check HRV data from Garmin Connect
│   ├── check_json.py        # Examine raw JSON data from Garmin API
│   ├── dump_sleep_data.py   # Extract detailed sleep data
│   └── merge_csv_files.py   # Merge multiple CSV exports
├── data/                    # Sample data directory
│   ├── hrv_data.json        # Sample HRV data for testing
│   └── sleep_data_2025-05-11.json # Sample sleep data for testing
├── exports/                 # Output directory for CSV and JSON exports
│   ├── archive/             # Archive of dated exports
│   └── activities/          # Directory for exported activity files
└── archive/                 # Old code archive for reference
    └── backups/             # Backup of old script versions
│       └── test_today_activities.py # Today's activities test script
├── exports/                 # Directory for exported CSV files
│   ├── garmin_stats.csv     # Main CSV file with all data (each row is a date)
│   ├── archive/             # Archive of date-specific CSV files
│   └── garmin_stats_backup_*.csv # Daily backups in Nextcloud
└── logs/                    # Directory for log files
    └── auth_status.json     # Authentication status log
├── CHANGELOG.md            # Comprehensive history of changes
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

## Features

* Download daily health statistics (steps, heart rate, sleep, etc.)
* Export data to CSV files for analysis
* Automatically back up to Nextcloud
* Download activity files (workouts, runs, etc.) in FIT format
* Automatic download of today's activities without manual confirmation
* Set up scheduled daily exports via crontab

## File Formats

### FIT Format

All activities are now downloaded in the native FIT (Flexible and Interoperable Data Transfer) format. This is Garmin's proprietary format that contains the raw, complete data for your activities. Benefits include:

- Complete and accurate activity data with no loss of fidelity
- Direct compatibility with Garmin's ecosystem and many third-party tools
- Efficient binary format that preserves all sensor data
- Better support for advanced metrics like running dynamics, power data, etc.

### CSV Format

Daily statistics (steps, heart rate, sleep, etc.) continue to be exported in CSV format which allows for:
- Easy analysis in spreadsheets and data analysis tools
- Human-readable format for quick inspection
- Simple integration with other systems

## New Features

### Automatic Download of Today's Activities

The latest version allows you to automatically download all of today's activities with a single command:

1. Choose option 7 from the menu: "Download today's activities automatically (ORIGINAL format)"
2. All activities recorded today will be downloaded in ORIGINAL format without requiring manual confirmation

This makes it easy to quickly back up your daily workout data without having to manually confirm each download. All activities are now downloaded in the native ORIGINAL format (Garmin's native format) for maximum data fidelity and compatibility with other fitness analysis tools.

### OpenAI Integration for Workout Analysis

The newest feature allows you to send your workout data to ChatGPT for personalized analysis and recommendations:

```
python analyze_workout.py
```

Key capabilities:
- Configure your OpenAI API key with `--configure`
- List recent activities with `--list-activities`
- Analyze a specific activity using `--activity-id <ID>`
- Analyze activities from a specific date with `--date YYYY-MM-DD`

The analysis includes:
- Performance insights based on your metrics
- Recovery recommendations
- Training suggestions
- Comparisons to your previous workouts (when available)

All analyses are saved to `exports/analysis/` for future reference.

For detailed instructions, see [OpenAI Integration Guide](docs/OPENAI_INTEGRATION.md).

To run the automatic download directly from the command line:

```bash
cd "/Users/jay/Projects/Garmin Apps/Data download"
python3 test_today_activities.py
```

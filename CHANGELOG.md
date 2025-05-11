# Changelog

This document provides a comprehensive history of changes made to the Garmin Connect Data Downloader.

## Version History

### 2025-05-10: Automatic Activity Download

#### Features Added
- Added automatic download of today's activities without requiring manual confirmation
- Created dedicated function `download_today_activities(garmin_client, format_type)` 
- Added menu option #7 for quick access to this functionality
- Created shell script `download_today.sh` for command-line execution

#### Benefits
- Saves time by downloading all today's activities in one step
- Provides format selection (TCX, GPX, KML, CSV, ORIGINAL)
- Works with both menu and command-line interfaces

### 2025-05-01: CSV Storage Consolidation

#### Changes Made
- Changed from date-specific files to a single consolidated CSV file
- Each row in the CSV represents data for a specific date
- Date-specific files preserved in the `archive` directory
- Added daily timestamped backups to Nextcloud
- Created utility script `merge_csv_files.py` for consolidating existing files

#### Benefits
- Easier data analysis with all data in a single file
- More efficient storage with headers stored only once
- Better backup protection with daily Nextcloud copies
- Maintained backward compatibility

### 2025-04-25: Date Field Enhancements

#### Features Added
- Enhanced date information in CSV files:
  - `year`: Four-digit year (e.g., 2025)
  - `month`: Two-digit month (e.g., 05)
  - `day`: Two-digit day (e.g., 10)
  - `day_of_week`: Number representing the day of the week (0=Monday, 6=Sunday)
- Original `date` field preserved for backward compatibility
- Automatic creation of date-specific archives

#### Benefits
- Improved data analysis capabilities
- Easier filtering by year, month, day, or day of week
- Better support for time series analysis

### 2025-04-15: Code Cleanup & Structure Improvements

#### Changes Made
- Date-specific CSV files moved to `exports/archive/`
- Made `daily_export.py` a symlink to `src/daily_export.py`
- Created `src/exports` directory for consistency
- Removed temporary/backup files
- Standardized code location in `src` directory

#### Benefits
- Simpler maintenance with all core code in `src` directory
- Cleaner file structure with no duplicate executables
- Better organization of CSV files in appropriate directories
- Preserved backward compatibility through symlinks

### 2025-04-01: Initial Public Release

- First public release of the Garmin Connect Data Downloader
- Basic functionality for downloading health and activity data
- Support for authentication with and without MFA
- CSV export capabilities

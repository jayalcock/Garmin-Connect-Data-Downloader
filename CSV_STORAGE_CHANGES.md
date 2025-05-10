# CSV Data Storage Changes

## Changes Made

1. **Changed the export_to_csv function** to use a single CSV file for all data
   - Modified the file naming from date-specific files to a single `garmin_stats.csv`
   - Kept the existing append functionality that adds new rows to this file

2. **Enhanced the backup_data_file function** to create daily backups
   - Main file `garmin_stats.csv` is copied to Nextcloud 
   - A timestamped backup is also created each day: `garmin_stats_backup_YYYY-MM-DD.csv`

3. **Created a merge utility** to consolidate existing CSV files
   - Added `merge_csv_files.py` script to merge existing date-specific files
   - The script creates backups of the original files in `exports/archive/`
   - All data is preserved with consistent headers

4. **Updated tests and documentation**
   - Fixed references to file paths in the test code
   - Updated the README.md with information about the new data storage approach
   - Added instructions for legacy data migration

## Benefits of This Approach

- **Easier Data Analysis**: Having all data in a single file makes it simpler to analyze trends over time
- **Better Backup Protection**: Daily backups in Nextcloud provide protection against data corruption
- **Backward Compatibility**: Original date-specific files are kept in an archive
- **More Efficient Storage**: Avoids duplication of header information in multiple files

The system now appends new data to the existing CSV file each day while maintaining daily backups in Nextcloud for additional safety.

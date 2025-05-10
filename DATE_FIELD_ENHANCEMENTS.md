# Date Field Enhancements

## Overview

The Garmin Connect data downloader now includes enhanced date information in the exported CSV files, making data analysis and filtering easier.

## Changes Implemented

1. **New Date Fields Added**
   - `date`: The original date field (YYYY-MM-DD format) is preserved for backward compatibility
   - `year`: Four-digit year (e.g., 2025)
   - `month`: Two-digit month (e.g., 05)
   - `day`: Two-digit day (e.g., 10)
   - `day_of_week`: Number representing the day of the week (0=Monday, 6=Sunday)

2. **Automatic Date-Specific Archives**
   - Each day's data is now automatically saved in a date-specific file in the archive directory
   - Format: `exports/archive/garmin_stats_YYYY-MM-DD.csv`
   - Contains the same enhanced date fields as the main consolidated file

3. **Updated Export Process**
   - The main consolidated file (`garmin_stats.csv`) continues to be updated with all data
   - Date-specific archives are created automatically for each new data export
   - Both files contain identical data structure with enhanced date fields

## Benefits

1. **Improved Data Analysis**
   - Easily filter data by year, month, day, or day of week
   - Better support for time series analysis and trend spotting
   - Simpler querying by specific time periods (e.g., all Mondays, all data from May)

2. **Automatic Archiving**
   - Both consolidated and date-specific formats maintained automatically
   - No manual steps needed to preserve data in different formats
   - Historical data preserved in both formats for backward compatibility

3. **Better Data Organization**
   - Clean separation between current consolidated file and archive files
   - All dates explicitly stored in the data, not just in filenames
   - Consistent data structure across all files

## Example Usage

When analyzing the data, you can now easily:

1. Filter by specific days of the week to compare patterns
2. Group data by month to observe seasonal trends
3. Extract data from specific years for long-term analysis
4. Use the day_of_week field to analyze weekday vs weekend patterns

The enhanced date fields make these operations more straightforward in data analysis tools like Excel, Python pandas, or SQL databases.

# Garmin Data Download - Technical Notes

This document provides technical details about the Garmin data download scripts and the fixes implemented to address various issues.

## Script Architecture

The download system consists of several key components:

### Core Scripts
1. `download_health_data.sh` - Downloads health metrics data
2. `download_activities.sh` - Downloads activity summaries

### Desktop Shortcuts
1. `Download Garmin Health Data.command` - Executes health data download
2. `Download Garmin Activities.command` - Executes activities download
3. `Garmin Activities Diagnostic.command` - Runs diagnostic tools

## Fixes Implemented

### 1. Python Path Handling

**Issue:** Scripts were failing with "no such file or directory: .venv/bin/python" errors.

**Fix:**
- Implemented robust Python executable detection
- Added fallback to system Python when virtual environment is not available
- Used `${PYTHON_PATH:-python3}` pattern to define the Python executable
- Added explicit checks to verify that the Python executable exists before running

```bash
# Determine which Python executable to use
PYTHON_EXEC=${PYTHON_PATH:-python3}
echo "Using Python: ${PYTHON_EXEC}"

# Check if Python executable exists before running
if [ ! -f "$PYTHON_EXEC" ] && [ "$PYTHON_EXEC" != "python3" ]; then
    echo "× Error: The Python executable '$PYTHON_EXEC' does not exist!"
    echo "Trying system Python as fallback..."
    PYTHON_EXEC="python3"
fi
```

### 2. String Quoting in Python Commands

**Issue:** Single quotes in shell scripts caused issues with variable interpolation in Python commands.

**Fix:**
- Changed single quotes to double quotes for shell command strings
- Used single quotes for Python string literals within the Python code
- Consistent quoting pattern across all scripts

Before:
```bash
$PYTHON_EXEC -c 'import sys; sys.path.append("."); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(non_interactive=True, allow_mfa=False); download_today_activities(client, "ORIGINAL") if client else print("Failed to connect to Garmin Connect")'
```

After:
```bash
$PYTHON_EXEC -c "import sys; sys.path.append('.'); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(non_interactive=True, allow_mfa=False); download_today_activities(client, 'ORIGINAL') if client else print('Failed to connect to Garmin Connect')"
```

### 3. Date Handling for Health Data

**Issue:** Health data was only downloading yesterday's data instead of today's.

**Fix:**
- Attempt to download today's data first
- Fall back to yesterday's data if today's data is not available
- Added date display in the output to clarify which date's data was downloaded

```bash
# First try to get today's data
echo "Attempting to download health data for today (${TODAY})..."
$PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;today=datetime.date.today().isoformat();client = connect_to_garmin(non_interactive=True, allow_mfa=False);get_stats(client, date_str=today, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')"

# Check if today's data file was created
if [ ! -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
    echo "Today's data not available yet. Attempting to download yesterday's data as fallback..."
    $PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;yesterday=(datetime.date.today() - datetime.timedelta(days=1)).isoformat();client = connect_to_garmin(non_interactive=True, allow_mfa=False);get_stats(client, date_str=yesterday, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')"
fi
```

## Diagnostic Tools

Several diagnostic tools were added to help troubleshoot download issues:

1. **test_date_download.sh** - Tests which dates are available for download.
2. **test_activities_download.sh** - Tests the activities download functionality.

## Best Practices Implemented

1. **Error Handling:**
   - Robust error detection and reporting
   - Clear error messages with suggested remedies
   - Fallback mechanisms when primary approaches fail

2. **Diagnostic Output:**
   - Timestamps for all operations
   - Clear success/failure indicators using ✓ and × symbols
   - Detailed information about file paths and contents

3. **Script Organization:**
   - Consistent variable naming across scripts
   - Common approach to Python executable detection
   - Shared patterns for credential handling

## Future Improvements

1. Consider implementing a unified configuration file to centralize settings.
2. Add more automated tests to verify script functionality.
3. Consider adding a "force download" option to override cached data.
4. Implement logging to keep a record of download attempts and results.

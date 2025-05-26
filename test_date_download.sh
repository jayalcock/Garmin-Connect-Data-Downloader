#!/bin/zsh
# test_date_download.sh - Test which date is being used for health data downloads

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Print current date information
echo "===== Date Information ====="
echo "Today's date: $(date +"%Y-%m-%d")"
echo "Yesterday's date: $(date -v-1d +"%Y-%m-%d")"
echo

# Set Python executable
PYTHON_EXEC=${PYTHON_PATH:-python3}

# Just run a simple test to show which date will be used
echo "===== Testing Date Logic ====="
$PYTHON_EXEC -c 'import sys; import datetime; sys.path.append("."); from garmin_sync import get_stats; print(f"Default date with None parameter: {datetime.date.today().isoformat()}"); print(f"Today\'s date from Python: {datetime.date.today().isoformat()}"); print(f"Yesterday\'s date from Python: {(datetime.date.today() - datetime.timedelta(days=1)).isoformat()}")'

echo
echo "===== Checking File Paths ====="
echo "Looking for today's JSON data..."
TODAY=$(date +"%Y-%m-%d")
if [ -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
    echo "✓ Today's data exists at: ./exports/garmin_stats_${TODAY}_raw.json"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${TODAY}_raw.json")"
else
    echo "× Today's data not found at: ./exports/garmin_stats_${TODAY}_raw.json"
fi

echo "Looking for yesterday's JSON data..."
YESTERDAY=$(date -v-1d +"%Y-%m-%d")
if [ -f "./exports/garmin_stats_${YESTERDAY}_raw.json" ]; then
    echo "✓ Yesterday's data exists at: ./exports/garmin_stats_${YESTERDAY}_raw.json"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${YESTERDAY}_raw.json")"
else
    echo "× Yesterday's data not found at: ./exports/garmin_stats_${YESTERDAY}_raw.json"
fi

echo
echo "===== Python Version Information ====="
$PYTHON_EXEC --version
$PYTHON_EXEC -c 'import garminconnect; print(f"Using garminconnect version: {garminconnect.__version__}")'

echo
echo "Test completed. This information can help diagnose any date-related issues."

#!/bin/zsh
# quick_data_check.sh - A quick diagnostic tool to check data availability and timing

echo "===== Garmin Data Availability Check ====="
echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Today's date: $(date +"%Y-%m-%d")"
echo "Yesterday's date: $(date -v-1d +"%Y-%m-%d")"
echo ""

# Set working directory
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Check for JSON data files
TODAY=$(date +"%Y-%m-%d")
YESTERDAY=$(date -v-1d +"%Y-%m-%d")

echo "Checking for health data JSON files..."
if [ -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
    echo "✓ Today's data exists (${TODAY})"
    FILESIZE=$(stat -f%z "./exports/garmin_stats_${TODAY}_raw.json")
    echo "  File size: $FILESIZE bytes"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${TODAY}_raw.json")"
    
    # Check for timestamps within the file
    echo "  Data timestamp check:"
    if command -v grep &>/dev/null; then
        # Use grep to find the earliest and latest timestamps
        TIMESTAMPS=$(grep -o '"readingTimeLocal": "[^"]*"' "./exports/garmin_stats_${TODAY}_raw.json" | sort | head -1; grep -o '"readingTimeLocal": "[^"]*"' "./exports/garmin_stats_${TODAY}_raw.json" | sort | tail -1)
        echo "  $TIMESTAMPS"
    fi
else
    echo "× Today's data (${TODAY}) not found"
fi

if [ -f "./exports/garmin_stats_${YESTERDAY}_raw.json" ]; then
    echo "✓ Yesterday's data exists (${YESTERDAY})"
    FILESIZE=$(stat -f%z "./exports/garmin_stats_${YESTERDAY}_raw.json")
    echo "  File size: $FILESIZE bytes"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${YESTERDAY}_raw.json")"
else
    echo "× Yesterday's data (${YESTERDAY}) not found"
fi

echo ""
echo "Checking CSV file..."
if [ -f "./exports/garmin_stats.csv" ]; then
    echo "✓ CSV data file exists"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats.csv")"
    
    # Check which dates are in the CSV file
    echo "  Dates in CSV (last 3):"
    if command -v head &>/dev/null; then
        head -1 "./exports/garmin_stats.csv" | tr ',' '\n' | head -1
        tail -3 "./exports/garmin_stats.csv" | cut -d',' -f1
    fi
else
    echo "× CSV data file not found"
fi

echo ""
echo "===== Running Updated Download Script ====="
./download_health_data.sh

echo ""
echo "===== After Download Check ====="
if [ -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
    echo "✓ Today's data exists (${TODAY})"
    FILESIZE=$(stat -f%z "./exports/garmin_stats_${TODAY}_raw.json")
    echo "  File size: $FILESIZE bytes"
    echo "  Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${TODAY}_raw.json")"
    
    # Check if the file was just updated
    MODIFIED_TIME=$(stat -f "%m" "./exports/garmin_stats_${TODAY}_raw.json")
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - MODIFIED_TIME))
    if [ $TIME_DIFF -lt 60 ]; then
        echo "  ✓ File was just updated (within the last minute)"
    else
        echo "  × File was not recently updated ($TIME_DIFF seconds ago)"
    fi
else
    echo "× Today's data (${TODAY}) still not found after download attempt"
fi

echo ""
echo "Test completed. Check the output above to determine if the download was successful."

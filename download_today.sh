#!/bin/zsh
# Script to download today's Garmin Connect activities

# Change to the project directory
cd "$(dirname "$0")"

# Set up logging
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/download_$(date +%Y-%m-%d).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Starting Garmin Connect download at $(date) ==="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment"
fi

# Define Nextcloud export directory
NEXTCLOUD_PATH="$HOME/Nextcloud/GarminExports"
CSV_PATH="$NEXTCLOUD_PATH/csv"
mkdir -p "$NEXTCLOUD_PATH"
mkdir -p "$CSV_PATH"

# Run the garmin_sync script with the today's activities option
# Download to exports/ as usual, then move to Nextcloud

echo "Downloading today's activities..."
python3 -c "
import sys
import os
from pathlib import Path
# Get the current directory since __file__ is not available in -c mode
current_dir = os.path.abspath('.')
sys.path.append(current_dir)
from garmin_sync import connect_to_garmin, download_today_activities
client = connect_to_garmin(non_interactive=True)
if client:
    download_today_activities(client, 'ORIGINAL')
"

# Move/copy only new files to Nextcloud
EXPORTS_DIR="./exports"
if [ -d "$EXPORTS_DIR" ]; then
    echo "Moving new FIT files to Nextcloud folder: $NEXTCLOUD_PATH"
    for file in "$EXPORTS_DIR/activities"/*.fit 2>/dev/null; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$NEXTCLOUD_PATH/$filename" ]; then
            mv "$file" "$NEXTCLOUD_PATH/" && echo "  ✓ Moved: $filename"
        fi
    done
    
    echo "Copying new JSON files to Nextcloud folder: $NEXTCLOUD_PATH"
    for file in "$EXPORTS_DIR"/*.json 2>/dev/null; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$NEXTCLOUD_PATH/$filename" ]; then
            cp "$file" "$NEXTCLOUD_PATH/" && echo "  ✓ Copied: $filename"
        fi
    done
    
    echo "Copying new CSV files to Nextcloud CSV folder: $CSV_PATH"
    for file in "$EXPORTS_DIR"/*.csv "$EXPORTS_DIR/activities"/*.csv 2>/dev/null; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$CSV_PATH/$filename" ]; then
            cp "$file" "$CSV_PATH/" && echo "  ✓ Copied: $filename"
        fi
    done
else
    echo "No exports directory found."
fi

echo "\nFinished downloading today's activities."

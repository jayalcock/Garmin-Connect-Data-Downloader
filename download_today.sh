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

# Move downloaded FIT files to Nextcloud
EXPORTS_DIR="./exports"
if [ -d "$EXPORTS_DIR" ]; then
    echo "Moving FIT files to Nextcloud folder: $NEXTCLOUD_PATH"
    mv "$EXPORTS_DIR/activities"/*.fit "$NEXTCLOUD_PATH" 2>/dev/null || echo "No FIT files to move."
    echo "Copying JSON files to Nextcloud folder: $NEXTCLOUD_PATH"
    cp "$EXPORTS_DIR"/*.json "$NEXTCLOUD_PATH" 2>/dev/null || echo "No JSON files to copy."
    echo "Copying CSV files to Nextcloud CSV folder: $CSV_PATH"
    cp "$EXPORTS_DIR"/*.csv "$CSV_PATH" 2>/dev/null || echo "No health CSV files to copy."
    cp "$EXPORTS_DIR/activities"/*.csv "$CSV_PATH" 2>/dev/null || echo "No activity CSV files to copy."
else
    echo "No exports directory found."
fi

echo "\nFinished downloading today's activities."

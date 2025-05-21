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

# Run the garmin_sync script with the today's activities option
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

echo "\nFinished downloading today's activities."

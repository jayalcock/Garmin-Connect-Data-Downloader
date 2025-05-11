#!/bin/zsh
# Script to download today's Garmin Connect activities

# Change to the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the downloader script with the today's activities option
python3 -c "
from src.downloader import connect_to_garmin, download_today_activities
client = connect_to_garmin()
if client:
    download_today_activities(client, 'TCX')
"

echo "\nFinished downloading today's activities."

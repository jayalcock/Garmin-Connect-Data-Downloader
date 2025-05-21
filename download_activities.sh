#!/bin/zsh
# download_activities.sh - Script to download today's activities in ORIGINAL format
# 
# This script automatically connects to Garmin Connect and downloads all
# of today's activities in ORIGINAL format without requiring manual intervention.

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Define a function to handle the Python script interaction
download_activities() {
    # Use expect to handle the interaction with the Python script
    expect << EOD
spawn python3 -c 'import sys; sys.path.append("."); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(allow_mfa=True); download_today_activities(client, "ORIGINAL") if client else print("Failed to connect to Garmin Connect")'
expect "Enter your Garmin Connect email: "
send "$GARMIN_EMAIL\r"
expect "Enter your Garmin Connect password: "
send "$GARMIN_PASSWORD\r"
expect "Save credentials for future use? (y/n): "
send "n\r"
interact
EOD
}

# Check if environment variables are set
if [ -n "$GARMIN_EMAIL" ] && [ -n "$GARMIN_PASSWORD" ]; then
    # Use the environment variables
    download_activities
else
    # Try to load saved credentials
    if [ -f "$HOME/.garmin_config.json" ]; then
        echo "Using saved credentials from ~/.garmin_config.json"
        # Use the Python script with saved credentials in non-interactive mode
        python3 -c 'import sys; sys.path.append("."); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(non_interactive=True, allow_mfa=False); download_today_activities(client, "ORIGINAL") if client else print("Failed to connect to Garmin Connect")'
    else
        echo "Error: Garmin credentials not found."
        echo "Please either:"
        echo "1. Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables, or"
        echo "2. Run garmin_sync.py first to save your credentials"
        exit 1
    fi
fi

echo "Done!"

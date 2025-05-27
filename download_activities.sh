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
    # Determine which Python executable to use
    PYTHON_EXEC=${PYTHON_PATH:-python3}
    echo "Using Python: ${PYTHON_EXEC}"

    # Check if Python executable exists and is executable before running
    if [ ! -x "$PYTHON_EXEC" ] && [ "$PYTHON_EXEC" != "python3" ]; then
        echo "× Error: The Python executable '$PYTHON_EXEC' does not exist or is not executable!"
        echo "Trying system Python as fallback..."
        PYTHON_EXEC="python3"
    fi
    
    # Check if the 'expect' command is available
    if ! command -v expect &> /dev/null; then
        echo "The 'expect' command is not installed. Using alternate method."
        echo "Email: $GARMIN_EMAIL"
        echo "Password: [hidden]"
        echo "Save credentials: n"
        
        # Use a temporary file to hold the responses
        RESP_FILE=$(mktemp)
        echo "$GARMIN_EMAIL" > "$RESP_FILE"
        echo "$GARMIN_PASSWORD" >> "$RESP_FILE"
        echo "n" >> "$RESP_FILE"
        
        # Run Python with input from the response file - using double quotes for better string handling
        $PYTHON_EXEC -c "import sys; sys.path.append('.'); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(allow_mfa=True); download_today_activities(client, 'ORIGINAL') if client else print('Failed to connect to Garmin Connect')" < "$RESP_FILE"
        
        # Remove the temporary file
        rm -f "$RESP_FILE"
    else
        # Use expect to handle the interaction with the Python script
        expect << EOD
spawn $PYTHON_EXEC -c "import sys; sys.path.append('.'); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(allow_mfa=True); download_today_activities(client, 'ORIGINAL') if client else print('Failed to connect to Garmin Connect')"
expect "Enter your Garmin Connect email: "
send "$GARMIN_EMAIL\r"
expect "Enter your Garmin Connect password: "
send "$GARMIN_PASSWORD\r"
expect "Save credentials for future use? (y/n): "
send "n\r"
interact
EOD
    fi
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
        # Double-check Python executable before running
        if [ ! -x "$PYTHON_EXEC" ] && [ "$PYTHON_EXEC" != "python3" ]; then
            echo "× Error: The Python executable '$PYTHON_EXEC' does not exist or is not executable!"
            echo "Trying system Python as fallback..."
            PYTHON_EXEC="python3"
        fi
        $PYTHON_EXEC -c "import sys; sys.path.append('.'); from garmin_sync import connect_to_garmin, download_today_activities; client = connect_to_garmin(non_interactive=True, allow_mfa=False); download_today_activities(client, 'ORIGINAL') if client else print('Failed to connect to Garmin Connect')"
    else
        echo "Error: Garmin credentials not found."
        echo "Please either:"
        echo "1. Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables, or"
        echo "2. Run garmin_sync.py first to save your credentials"
        exit 1
    fi
fi

# Define Nextcloud export directory and activities subfolder
NEXTCLOUD_PATH="$HOME/Nextcloud/GarminExports"
ACTIVITIES_PATH="$NEXTCLOUD_PATH/activities"
CSV_PATH="$NEXTCLOUD_PATH/csv"
mkdir -p "$NEXTCLOUD_PATH"
mkdir -p "$ACTIVITIES_PATH"
mkdir -p "$CSV_PATH"

# Copy downloaded files to Nextcloud
EXPORTS_DIR="./exports"
if [ -d "$EXPORTS_DIR" ]; then
    echo "Copying FIT files to Nextcloud activities folder: $ACTIVITIES_PATH"
    cp "$EXPORTS_DIR/activities"/*.fit "$ACTIVITIES_PATH" 2>/dev/null || echo "No FIT files to copy."
    echo "Copying JSON files to Nextcloud folder: $NEXTCLOUD_PATH"
    cp "$EXPORTS_DIR"/*.json "$NEXTCLOUD_PATH" 2>/dev/null || echo "No JSON files to copy."
    echo "Copying CSV files to Nextcloud CSV folder: $CSV_PATH"
    cp "$EXPORTS_DIR"/*.csv "$CSV_PATH" 2>/dev/null || echo "No health CSV files to copy."
    cp "$EXPORTS_DIR/activities"/*.csv "$CSV_PATH" 2>/dev/null || echo "No activity CSV files to copy."
else
    echo "No exports directory found."
fi

echo "Done!"

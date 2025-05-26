#!/bin/zsh
# download_health_data.sh - Script to download today's health data to Desktop
# 
# This script automatically connects to Garmin Connect and downloads
# your daily health metrics (steps, sleep, HRV, etc) and saves the files
# to your Desktop for easy access.

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Define the user's desktop path
DESKTOP_PATH="$HOME/Desktop"

# Make sure desktop directory exists
if [ ! -d "$DESKTOP_PATH" ]; then
  echo "Error: Could not find Desktop folder at $DESKTOP_PATH"
  exit 1
fi

# Current date in YYYY-MM-DD format
TODAY=$(date +"%Y-%m-%d")
YESTERDAY=$(date -v-1d +"%Y-%m-%d")

# Define a function to handle the Python script interaction
download_health_data() {
    # Determine which Python executable to use
    PYTHON_EXEC=${PYTHON_PATH:-python3}
    
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
        
        # First try to get today's data with a more robust approach
        echo "Attempting to download health data for today (${TODAY})..."
        $PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;today=datetime.date.today().isoformat();client = connect_to_garmin(allow_mfa=True);get_stats(client, date_str=today, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')" < "$RESP_FILE"
        
        # Check if today's data file was created
        if [ ! -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
            echo "Today's data not available yet. Attempting to download yesterday's data as fallback..."
            # Use a new temporary file to hold the responses
            RESP_FILE2=$(mktemp)
            echo "$GARMIN_EMAIL" > "$RESP_FILE2"
            echo "$GARMIN_PASSWORD" >> "$RESP_FILE2"
            echo "n" >> "$RESP_FILE2"
            
            # Try yesterday's data as fallback
            $PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;yesterday=(datetime.date.today() - datetime.timedelta(days=1)).isoformat();client = connect_to_garmin(allow_mfa=True);get_stats(client, date_str=yesterday, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')" < "$RESP_FILE2"
            
            # Remove the second temporary file
            rm -f "$RESP_FILE2"
        fi
        
        # Remove the first temporary file
        rm -f "$RESP_FILE"
    else
        # Use expect to handle the interaction with the Python script
        echo "Attempting to download health data for today (${TODAY})..."
        expect << EOD
spawn $PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;today=datetime.date.today().isoformat();client = connect_to_garmin(allow_mfa=True);get_stats(client, date_str=today, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')"
expect "Enter your Garmin Connect email: "
send "$GARMIN_EMAIL\r"
expect "Enter your Garmin Connect password: "
send "$GARMIN_PASSWORD\r"
expect "Save credentials for future use? (y/n): "
send "n\r"
interact
EOD
        # Check if today's data file was created
        if [ ! -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
            echo "Today's data not available yet. Attempting to download yesterday's data as fallback..."
            expect << EOD
spawn $PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;yesterday=(datetime.date.today() - datetime.timedelta(days=1)).isoformat();client = connect_to_garmin(allow_mfa=True);get_stats(client, date_str=yesterday, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')"
expect "Enter your Garmin Connect email: "
send "$GARMIN_EMAIL\r"
expect "Enter your Garmin Connect password: "
send "$GARMIN_PASSWORD\r"
expect "Save credentials for future use? (y/n): "
send "n\r"
interact
EOD
        fi
    fi
}

# Function to copy files to desktop with proper names
copy_to_desktop() {
    # Create today's date folder on desktop
    DESKTOP_FOLDER="$DESKTOP_PATH/Garmin_Health_$TODAY"
    mkdir -p "$DESKTOP_FOLDER"
    
    # Copy the main CSV file
    if [ -f "./exports/garmin_stats.csv" ]; then
        cp "./exports/garmin_stats.csv" "$DESKTOP_FOLDER/garmin_health_stats_$TODAY.csv"
        echo "✓ Health stats CSV file saved to $DESKTOP_FOLDER/garmin_health_stats_$TODAY.csv"
        # Add a timestamp of when the file was last modified
        echo "  CSV File last updated: $(stat -f "%Sm" "./exports/garmin_stats.csv")"
    else
        echo "× Health stats CSV file not found"
    fi
    
    # Copy the raw JSON data - prioritize TODAY's data
    if [ -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
        cp "./exports/garmin_stats_${TODAY}_raw.json" "$DESKTOP_FOLDER/garmin_health_stats_$TODAY.json"
        echo "✓ Health stats JSON file saved to $DESKTOP_FOLDER/garmin_health_stats_$TODAY.json"
        echo "  JSON File last updated: $(stat -f "%Sm" "./exports/garmin_stats_${TODAY}_raw.json")"
        
        # Check for the timestamp within the JSON data to show when Garmin processed it
        if command -v grep &>/dev/null && command -v jq &>/dev/null; then
            # If jq is available, use it to extract timestamps
            LATEST_TIMESTAMP=$(jq -r '.readingTimeLocal' "./exports/garmin_stats_${TODAY}_raw.json" 2>/dev/null || echo "")
            if [ -n "$LATEST_TIMESTAMP" ]; then
                echo "  Latest data timestamp from Garmin: $LATEST_TIMESTAMP"
            fi
        fi
    elif [ -f "./exports/garmin_stats_${YESTERDAY}_raw.json" ]; then
        # If today's data isn't available yet, copy yesterday's as a fallback
        cp "./exports/garmin_stats_${YESTERDAY}_raw.json" "$DESKTOP_FOLDER/garmin_health_stats_$YESTERDAY.json"
        echo "× Today's data not found. Yesterday's health stats JSON file saved to $DESKTOP_FOLDER/garmin_health_stats_$YESTERDAY.json"
        echo "  Yesterday's JSON File last updated: $(stat -f "%Sm" "./exports/garmin_stats_${YESTERDAY}_raw.json")"
        echo "  Note: Today's data might not be available from Garmin yet - they typically process data with a delay."
        echo "  Try running the download again later in the day when more data is available."
    else
        echo "× Health stats JSON file not found for either today or yesterday"
        echo "  Note: Garmin might not have processed any recent data yet, or there might be connection issues."
        echo "  Please check your internet connection and Garmin account status."
    fi
    
    # Add diagnostic information
    echo 
    echo "===== Download Diagnostic Info ====="
    echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Requested date: $TODAY"
    echo "Available files in exports directory:"
    ls -la "./exports/" | grep "garmin_stats"
    
    # Copy any archive files if they exist
    if [ -d "./exports/archive" ]; then
        mkdir -p "$DESKTOP_FOLDER/archive"
        find "./exports/archive" -name "garmin_stats_*.csv" -type f -newermt "$YESTERDAY" -exec cp {} "$DESKTOP_FOLDER/archive/" \;
        echo "✓ Archive files copied to $DESKTOP_FOLDER/archive/"
    fi
    
    # Create a diagnostic report
    DIAG_FILE="$DESKTOP_FOLDER/download_diagnostic.txt"
    {
        echo "===== Garmin Health Data Download Diagnostic ====="
        echo "Download performed at: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Requested date: $TODAY"
        echo "Yesterday's date: $YESTERDAY"
        echo 
        echo "Files found:"
        echo "CSV: $([ -f "./exports/garmin_stats.csv" ] && echo "Yes" || echo "No")"
        echo "Today's JSON: $([ -f "./exports/garmin_stats_${TODAY}_raw.json" ] && echo "Yes" || echo "No")"
        echo "Yesterday's JSON: $([ -f "./exports/garmin_stats_${YESTERDAY}_raw.json" ] && echo "Yes" || echo "No")"
        echo
        echo "Available files in exports directory:"
        ls -la "./exports/" | grep "garmin_stats"
    } > "$DIAG_FILE"
    
    echo ""
    echo "Health data download complete! Files saved to $DESKTOP_FOLDER"
    echo "You can open these files with Excel, Numbers or a text editor."
    echo "A diagnostic report has been saved to $DESKTOP_FOLDER/download_diagnostic.txt"
}

echo "===== Garmin Health Data Downloader ====="
echo "This script will download your latest health data from Garmin Connect"
echo "and save it to your Desktop for easy access."
echo ""

# Check if environment variables are set
if [ -n "$GARMIN_EMAIL" ] && [ -n "$GARMIN_PASSWORD" ]; then
    # Use the environment variables
    download_health_data
    copy_to_desktop
else
    # Try to load saved credentials
    if [ -f "$HOME/.garmin_config.json" ]; then
        echo "Using saved credentials from ~/.garmin_config.json"
        # Determine which Python executable to use
        PYTHON_EXEC=${PYTHON_PATH:-python3}

        # Ensure exports directory exists
        mkdir -p "./exports"

        # Print working directory and list files before download
        echo "Current directory: $(pwd)"
        echo "Files in ./exports before download:"
        ls -l ./exports

        # First try to get today's data
        echo "Attempting to download health data for today (${TODAY})..."
        PY_OUT=$($PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;today=datetime.date.today().isoformat();client = connect_to_garmin(non_interactive=True, allow_mfa=False);get_stats(client, date_str=today, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')" 2>&1)
        echo "$PY_OUT"

        # Check if today's data file was created
        if [ ! -f "./exports/garmin_stats_${TODAY}_raw.json" ]; then
            echo "Today's data not available yet. Attempting to download yesterday's data as fallback..."
            PY_OUT2=$($PYTHON_EXEC -c "import sys; sys.path.append('.');from garmin_sync import connect_to_garmin, get_stats;import datetime;yesterday=(datetime.date.today() - datetime.timedelta(days=1)).isoformat();client = connect_to_garmin(non_interactive=True, allow_mfa=False);get_stats(client, date_str=yesterday, export=True, interactive=False) if client else print('Failed to connect to Garmin Connect')" 2>&1)
            echo "$PY_OUT2"
        fi

        # List files after download
        echo "Files in ./exports after download:"
        ls -l ./exports

        copy_to_desktop
    else
        echo "Error: Garmin credentials not found."
        echo "Please either:"
        echo "1. Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables, or"
        echo "2. Run garmin_sync.py first to save your credentials"
        exit 1
    fi
fi

echo "✓ Done!"

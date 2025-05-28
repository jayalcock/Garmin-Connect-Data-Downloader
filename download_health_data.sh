#!/bin/zsh
# download_health_data.sh - Script to download today's health data to Nextcloud
# 
# This script automatically connects to Garmin Connect and downloads
# your daily health metrics (steps, sleep, HRV, etc) and saves the files
# to your Nextcloud folder for easy access.

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

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
# Copy to Nextcloud using new-files-only logic
copy_to_nextcloud() {
    # Define Nextcloud export directory
    NEXTCLOUD_PATH="$HOME/Nextcloud/GarminExports"
    CSV_PATH="$NEXTCLOUD_PATH/csv"
    mkdir -p "$NEXTCLOUD_PATH"
    mkdir -p "$CSV_PATH"
    
    echo ""
    echo "===== Copying to Nextcloud ====="
    
    # Copy only new JSON files to Nextcloud
    echo "Copying new health JSON files to Nextcloud folder: $NEXTCLOUD_PATH"
    for file in "./exports"/garmin_stats_*_raw.json; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$NEXTCLOUD_PATH/$filename" ]; then
            cp "$file" "$NEXTCLOUD_PATH/" && echo "  ✓ Copied: $filename"
        fi
    done
    
    # Copy only new CSV files to Nextcloud
    echo "Copying new health CSV files to Nextcloud CSV folder: $CSV_PATH"
    for file in "./exports"/*.csv; do
        [ -f "$file" ] || continue
        filename=$(basename "$file")
        if [ ! -f "$CSV_PATH/$filename" ]; then
            cp "$file" "$CSV_PATH/" && echo "  ✓ Copied: $filename"
        fi
    done
    
    # Add diagnostic information
    echo 
    echo "===== Download Diagnostic Info ====="
    echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Requested date: $TODAY"
    echo "Available files in exports directory:"
    ls -la "./exports/" | grep "garmin_stats"
    
    echo ""
    echo "Health data download complete! Files saved to Nextcloud folder: $NEXTCLOUD_PATH"
    echo "You can access these files through your Nextcloud sync folder."
}

echo "===== Garmin Health Data Downloader ====="
echo "This script will download your latest health data from Garmin Connect"
echo "and save it to your Nextcloud folder for easy access."
echo ""

# Check if environment variables are set
if [ -n "$GARMIN_EMAIL" ] && [ -n "$GARMIN_PASSWORD" ]; then
    # Use the environment variables
    download_health_data
    copy_to_nextcloud
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

        copy_to_nextcloud
    else
        echo "Error: Garmin credentials not found."
        echo "Please either:"
        echo "1. Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables, or"
        echo "2. Run garmin_sync.py first to save your credentials"
        exit 1
    fi
fi

echo "✓ Done!"

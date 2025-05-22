#!/bin/zsh
# filepath: /Users/jay/Projects/Garmin Apps/Data download/examples/download_and_analyze.sh
#
# Example script to download today's activities from Garmin Connect, 
# then process and analyze them

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# cd to the parent directory (Data download)
cd "$PARENT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Check if the CLI script exists
if [[ ! -f "./garmin_cli.py" ]]; then
    echo "Error: garmin_cli.py not found"
    exit 1
fi

# Download today's activities
echo "Downloading today's activities from Garmin Connect..."
python garmin_cli.py download --days=1

# Check if download was successful
if [[ $? -ne 0 ]]; then
    echo "Error: Failed to download activities"
    exit 1
fi

# Process the latest downloaded activity with advanced charts
echo "Processing the latest activity with advanced charts..."
python garmin_cli.py latest --advanced

# Exit with success
echo "Done! Your latest workout has been downloaded and analyzed."
echo "Check the exports/chatgpt_ready directory for the summary and charts."
exit 0

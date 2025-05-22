#!/bin/zsh
# filepath: /Users/jay/Projects/Garmin Apps/Data download/examples/process_latest.sh
#
# Example script to process the latest workout downloaded from Garmin Connect
# Demonstrates how to use the unified CLI tool

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

# Process the latest FIT file with advanced charts
echo "Processing latest FIT file with advanced charts..."
python garmin_cli.py latest --advanced

# Exit with the same status as the CLI command
exit $?

#!/bin/zsh
# filepath: /Users/jay/Projects/Garmin Apps/Data download/garmin-cli.sh
# 
# Simple wrapper for the garmin_cli.py unified CLI tool
# Makes the CLI easier to use as a command

# Get the directory where this script is located
SCRIPT_DIR="$(dirname "$0")"

# Make sure we're in the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Set Python executable
PYTHON=python3

# Make sure garmin_cli.py exists
if [[ ! -f "${SCRIPT_DIR}/garmin_cli.py" ]]; then
    echo "Error: garmin_cli.py not found in $SCRIPT_DIR"
    exit 1
fi

# Make the garmin_cli.py file executable
chmod +x "$SCRIPT_DIR/garmin_cli.py"

# Pass all arguments to the Python script
$PYTHON "$SCRIPT_DIR/garmin_cli.py" "$@"

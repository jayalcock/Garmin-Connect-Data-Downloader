#!/bin/zsh
# filepath: /Users/jay/Projects/Garmin Apps/Data download/examples/batch_process.sh
#
# Example script to batch process all FIT files in a directory

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

# Default directory if none provided
DIRECTORY="${1:-$PARENT_DIR/exports/activities}"

# Check if directory exists
if [[ ! -d "$DIRECTORY" ]]; then
    echo "Error: Directory not found: $DIRECTORY"
    echo "Usage: $0 [directory-path]"
    exit 1
fi

# Batch process all FIT files in the directory
echo "Processing all FIT files in: $DIRECTORY"
python garmin_cli.py batch "$DIRECTORY" --recursive --charts

# Exit with the same status as the CLI command
exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo "Successfully processed files"
    echo "Check the exports/chatgpt_ready directory for the summaries"
else
    echo "Warning: Some files may not have been processed successfully"
fi

exit $exit_code

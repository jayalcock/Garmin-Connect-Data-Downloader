#!/bin/zsh
# filepath: /Users/jay/Projects/Garmin Apps/Data download/examples/compare_workouts.sh
#
# Example script to compare multiple workouts and visualize trends

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

# Default parameters
SPORT=${1:-"running"}  # Default to running if no sport specified
DAYS=${2:-90}          # Default to last 90 days if not specified

# Compare workouts and generate trend charts
echo "Comparing $SPORT workouts from the last $DAYS days..."
python garmin_cli.py compare --sport="$SPORT" --days="$DAYS"

# Exit with the same status as the CLI command
exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo "Check the exports/workout_comparison directory for results"
else
    echo "Error comparing workouts"
fi

exit $exit_code

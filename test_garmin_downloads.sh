#!/bin/zsh
# test_downloads.sh - Test both activities and health data downloads

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

echo "===== Garmin Download Scripts Diagnostic ====="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Current Directory: $(pwd)"
echo ""

# Test Python environment
PYTHON_EXEC=${PYTHON_PATH:-python3}
echo "Using Python executable: $PYTHON_EXEC"
echo "Python version: $($PYTHON_EXEC --version 2>&1)"

# Check for required packages
echo ""
echo "Checking for required Python packages:"
packages=("garminconnect" "fitparse" "pandas" "matplotlib")
for pkg in "${packages[@]}"; do
    if $PYTHON_EXEC -c "import $pkg" 2>/dev/null; then
        echo "✓ $pkg is installed"
        # Get version if possible
        if [ "$pkg" = "garminconnect" ]; then
            VERSION=$($PYTHON_EXEC -c "import $pkg; print($pkg.__version__)" 2>/dev/null)
            echo "  Version: $VERSION"
        fi
    else
        echo "× $pkg is NOT installed"
    fi
done

echo ""
echo "===== Checking Script Commands ====="

# Check download_activities.sh
echo ""
echo "Examining download_activities.sh:"
if [ -f "download_activities.sh" ]; then
    PYTHON_COMMANDS=$(grep -A 2 "PYTHON_EXEC -c" "download_activities.sh" | grep -v "grep")
    echo "$PYTHON_COMMANDS"
else
    echo "× download_activities.sh not found in current directory"
fi

# Check download_health_data.sh
echo ""
echo "Examining download_health_data.sh:"
if [ -f "download_health_data.sh" ]; then
    PYTHON_COMMANDS=$(grep -A 2 "PYTHON_EXEC -c" "download_health_data.sh" | grep -v "grep")
    echo "$PYTHON_COMMANDS"
else
    echo "× download_health_data.sh not found in current directory"
fi

# Check for .garmin_config.json
echo ""
echo "Checking for saved Garmin credentials:"
if [ -f "$HOME/.garmin_config.json" ]; then
    echo "✓ Credentials file exists at ~/.garmin_config.json"
    echo "  Last modified: $(stat -f "%Sm" "$HOME/.garmin_config.json")"
    echo "  File permissions: $(stat -f "%Sp" "$HOME/.garmin_config.json")"
else
    echo "× No saved credentials found at ~/.garmin_config.json"
fi

# Check the desktop shortcuts
echo ""
echo "Checking desktop shortcuts:"
for shortcut in "$HOME/Desktop/Download Garmin Health Data.command" "$HOME/Desktop/Download Garmin Activities.command"; do
    if [ -f "$shortcut" ]; then
        echo "✓ $(basename "$shortcut") exists"
        echo "  Last modified: $(stat -f "%Sm" "$shortcut")"
        echo "  File permissions: $(stat -f "%Sp" "$shortcut")"
        # Check Python path export
        PYTHON_PATH_LINE=$(grep "export PYTHON_PATH" "$shortcut")
        echo "  Python path setting: $PYTHON_PATH_LINE"
    else
        echo "× $(basename "$shortcut") not found"
    fi
done

# Check for recent output files
echo ""
echo "Checking for recent data files:"
TODAY=$(date +"%Y-%m-%d")
YESTERDAY=$(date -v-1d +"%Y-%m-%d")

for date_str in "$TODAY" "$YESTERDAY"; do
    echo "  Looking for $date_str data:"
    
    if [ -f "./exports/garmin_stats_${date_str}_raw.json" ]; then
        echo "  ✓ Health data JSON found for $date_str"
        echo "    Last modified: $(stat -f "%Sm" "./exports/garmin_stats_${date_str}_raw.json")"
    else
        echo "  × No health data JSON found for $date_str"
    fi
    
    # Check for activity files from today
    if [ -d "./exports/activities" ]; then
        TODAY_ACTIVITIES=$(find "./exports/activities" -type f -name "*${date_str}*" | wc -l)
        if [ "$TODAY_ACTIVITIES" -gt 0 ]; then
            echo "  ✓ Found $TODAY_ACTIVITIES activity files for $date_str"
        else
            echo "  × No activity files found for $date_str"
        fi
    else
        echo "  × activities directory not found"
    fi
done

echo ""
echo "===== End of Diagnostic ====="
echo "If you're having issues, please check:"
echo "1. That Python and required packages are installed correctly"
echo "2. That your Garmin Connect credentials are valid"
echo "3. That the scripts have correct permissions"
echo ""

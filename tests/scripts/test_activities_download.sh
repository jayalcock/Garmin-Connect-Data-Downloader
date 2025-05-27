#!/bin/zsh
# test_activities_download.sh - Diagnostic tool for Garmin activities download

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

echo "===== Garmin Activities Download Diagnostic ====="
echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Current directory: $(pwd)"
echo ""

# Test Python environment
PYTHON_EXEC=${PYTHON_PATH:-python3}
echo "Using Python executable: $PYTHON_EXEC"
echo "Python version: $($PYTHON_EXEC --version 2>&1)"
echo "Python location: $(which $PYTHON_EXEC 2>/dev/null || echo 'Not in PATH')"

# Check if Python executable exists
if [ "$PYTHON_EXEC" != "python3" ] && [ ! -f "$PYTHON_EXEC" ]; then
    echo "× ERROR: Python executable $PYTHON_EXEC does not exist!"
    echo "Will try system python3 as fallback."
    PYTHON_EXEC=python3
fi

# Check for required packages
echo ""
echo "Checking for required packages:"
packages=("garminconnect" "fitparse" "pandas")
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

# Check for credentials
echo ""
echo "Checking for Garmin credentials:"
if [ -f "$HOME/.garmin_config.json" ]; then
    echo "✓ Credentials file exists at ~/.garmin_config.json"
    echo "  Last modified: $(stat -f "%Sm" "$HOME/.garmin_config.json")"
else
    echo "× No saved credentials found"
fi

# Check for existing activities
echo ""
TODAY=$(date +"%Y-%m-%d")
YESTERDAY=$(date -v-1d +"%Y-%m-%d")

if [ -d "./exports/activities" ]; then
    echo "Checking for recent activities:"
    TODAY_COUNT=$(find "./exports/activities" -type f -name "*${TODAY}*" | wc -l | tr -d ' ')
    echo "- Today (${TODAY}): ${TODAY_COUNT} files"
    if [ $TODAY_COUNT -gt 0 ]; then
        echo "  Most recent: $(find "./exports/activities" -type f -name "*${TODAY}*" -exec ls -lt {} \; | head -1)"
    fi
    
    YESTERDAY_COUNT=$(find "./exports/activities" -type f -name "*${YESTERDAY}*" | wc -l | tr -d ' ')
    echo "- Yesterday (${YESTERDAY}): ${YESTERDAY_COUNT} files"
    if [ $YESTERDAY_COUNT -gt 0 ]; then
        echo "  Most recent: $(find "./exports/activities" -type f -name "*${YESTERDAY}*" -exec ls -lt {} \; | head -1)"
    fi
else
    echo "× Activities directory not found"
fi

echo ""
echo "===== Testing Activities Download ====="
echo "Attempting to download activities using Python path: $PYTHON_EXEC"

# Attempt activities download with detailed output
$PYTHON_EXEC -c "
import sys
import datetime
sys.path.append('.')
try:
    from garmin_sync import connect_to_garmin, download_today_activities
    print(f'Successfully imported modules')
    
    # Try to connect
    print(f'Connecting to Garmin (non-interactive mode)...')
    client = connect_to_garmin(non_interactive=True, allow_mfa=False)
    
    if client:
        print(f'Successfully connected to Garmin')
        print(f'Downloading activities for today ({datetime.date.today().isoformat()})...')
        download_today_activities(client, 'ORIGINAL')
        print(f'Activity download complete')
    else:
        print(f'Failed to connect to Garmin Connect')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "===== Results After Download Attempt ====="
if [ -d "./exports/activities" ]; then
    NEW_TODAY_COUNT=$(find "./exports/activities" -type f -name "*${TODAY}*" | wc -l | tr -d ' ')
    
    if [ $NEW_TODAY_COUNT -gt 0 ]; then
        echo "✓ Found $NEW_TODAY_COUNT activities for today"
        echo "  Latest files:"
        find "./exports/activities" -type f -name "*${TODAY}*" -exec ls -lt {} \; | head -3
    else
        echo "× No activities found for today"
        echo "  You may not have any recorded activities today, or there may be an issue with the download."
    fi
else
    echo "× Activities directory still not found"
fi

echo ""
echo "Diagnostic complete. Use this information to troubleshoot any download issues."

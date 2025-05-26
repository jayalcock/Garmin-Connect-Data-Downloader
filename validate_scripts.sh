#!/bin/bash
# Garmin Download Scripts Validation Test
# This script tests that all the Garmin download scripts are properly configured

# Display header
echo "==========================================="
echo "Garmin Download Scripts Validation Test"
echo "==========================================="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo "Python: $(which python3) ($(python3 --version 2>&1))"

# Navigate to the script directory
cd "$(dirname "$0")" || { 
  echo "Error: Failed to change directory"; 
  exit 1; 
}

# List of scripts to check
SCRIPTS=(
  "download_health_data.sh"
  "download_activities.sh"
  "download_fit_activities.sh"
)

echo -e "\nChecking shell scripts..."
echo "-------------------------------------------"

# Check each script for common issues
for script in "${SCRIPTS[@]}"; do
  echo "Checking $script..."
  
  if [ ! -f "$script" ]; then
    echo "  × ERROR: Script not found!"
    continue
  fi
  
  # Check if script is executable
  if [ ! -x "$script" ]; then
    echo "  ! Warning: Script is not executable (fixing...)"
    chmod +x "$script"
  else
    echo "  ✓ Script is executable"
  fi
  
  # Check for Python path handling
  if grep -q "PYTHON_EXEC=\${PYTHON_PATH:-python3}" "$script"; then
    echo "  ✓ Script has proper Python path handling"
  else
    echo "  × ERROR: Script is missing proper Python path handling!"
  fi
  
  # Check for existence check on Python executable 
  if grep -q "if \[ ! -f \".*PYTHON" "$script"; then
    echo "  ✓ Script has Python executable existence check"
  else
    echo "  ! Warning: Script might be missing Python executable existence check"
  fi
  
  # Check for single quotes in Python commands
  if grep -q "\$PYTHON_EXEC -c '" "$script"; then
    echo "  × ERROR: Script is using single quotes for Python commands!"
  else
    echo "  ✓ Script is using proper double quotes for Python commands"
  fi
  
  echo ""
done

echo -e "\nChecking desktop shortcuts..."
echo "-------------------------------------------"
SHORTCUTS=(
  "$HOME/Desktop/Download Garmin Health Data.command"
  "$HOME/Desktop/Download Garmin Activities.command"
  "$HOME/Desktop/Download Garmin FIT Activities.command"
)

for shortcut in "${SHORTCUTS[@]}"; do
  echo "Checking $(basename "$shortcut")..."
  
  if [ ! -f "$shortcut" ]; then
    echo "  × ERROR: Shortcut not found!"
    continue
  fi
  
  # Check if shortcut is executable
  if [ ! -x "$shortcut" ]; then
    echo "  ! Warning: Shortcut is not executable (fixing...)"
    chmod +x "$shortcut"
  else
    echo "  ✓ Shortcut is executable"
  fi
  
  # Check for proper handling of Python paths
  if grep -q "PYTHON_PATH=\"\$PYTHON_TO_USE\"" "$shortcut"; then
    echo "  ✓ Shortcut has proper Python path setting"
  else
    echo "  ! Warning: Shortcut might be missing proper Python path setting"
  fi
  
  echo ""
done

echo "Validation complete!"
echo "==========================================="

#!/bin/zsh
# fit_to_chatgpt.sh - Convert a Garmin FIT file to ChatGPT-friendly format
#
# This script finds the most recently downloaded FIT file from Garmin Connect,
# converts it to CSV format, and creates a markdown summary suitable for
# importing into ChatGPT for workout analysis.

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Default locations
EXPORT_DIR="$SCRIPT_DIR/exports/activities"
CHATGPT_DIR="$SCRIPT_DIR/exports/chatgpt_ready"

# Create ChatGPT ready directory if it doesn't exist
mkdir -p "$CHATGPT_DIR"

# Find the most recently downloaded FIT file
echo "Looking for the most recent FIT file in $EXPORT_DIR..."
LATEST_FIT=$(find "$EXPORT_DIR" -name "*.fit" -type f -print0 | xargs -0 ls -t | head -1)

if [[ -z "$LATEST_FIT" ]]; then
    echo "No FIT files found in $EXPORT_DIR"
    exit 1
fi

echo "Found FIT file: $LATEST_FIT"

# Extract the basename without extension
BASENAME=$(basename "$LATEST_FIT" .fit)

# Set output filenames
CSV_FILE="$CHATGPT_DIR/${BASENAME}.csv"
SUMMARY_FILE="$CHATGPT_DIR/${BASENAME}_summary.md"

# Step 1: Convert FIT to CSV
echo "Converting FIT file to CSV..."
python3 -c "
import sys
from pathlib import Path
try:
    from fitparse import FitFile
    import pandas as pd
    
    fit_path = Path('$LATEST_FIT')
    csv_path = Path('$CSV_FILE')
    
    # Parse FIT file
    fitfile = FitFile(str(fit_path))
    
    # Extract records
    records = []
    for record in fitfile.get_messages():
        record_type = record.name
        
        data_dict = {'record_type': record_type}
        for field in record:
            field_name = field.name
            
            if field.value is not None:
                data_dict[field_name] = field.value
            
            if field.units:
                data_dict[f'{field_name}_units'] = field.units
        
        records.append(data_dict)
    
    # Convert to DataFrame and save CSV
    if records:
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False)
        print(f'Successfully converted to CSV: {csv_path}')
    else:
        print('No data found in FIT file')
        sys.exit(1)
except ImportError as e:
    print(f'Error: Required module not found - {e}')
    print('Please install required modules with: pip install fitparse pandas')
    sys.exit(1)
except Exception as e:
    print(f'Error processing file: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    echo "Error: Failed to convert FIT to CSV"
    exit 1
fi

# Step 2: Create ChatGPT-friendly summary from CSV
echo "Creating ChatGPT-friendly summary..."
python3 -c "
import sys
from pathlib import Path
try:
    import pandas as pd
    
    csv_path = Path('$CSV_FILE')
    summary_path = Path('$SUMMARY_FILE')
    
    # Load CSV data
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Extract session data
    session_df = df[df['record_type'] == 'session']
    
    if session_df.empty:
        print('No session data found in CSV file')
        sys.exit(1)
    
    # Get the first (and typically only) session
    session = session_df.iloc[0]
    sport_type = session.get('sport', 'activity').title()
    
    # Create markdown summary
    with open(summary_path, 'w') as f:
        f.write(f'# {sport_type} Workout Summary\n\n')
        
        # Basic metrics
        if 'total_distance' in session:
            distance = session['total_distance']
            distance_km = distance / 1000
            distance_mi = distance_km * 0.621371
            f.write(f'**Distance:** {distance_km:.2f} km ({distance_mi:.2f} miles)\n\n')
        
        if 'total_elapsed_time' in session:
            time = session['total_elapsed_time']
            minutes = int(time // 60)
            seconds = int(time % 60)
            f.write(f'**Duration:** {minutes} minutes {seconds} seconds\n\n')
        
        if 'start_time' in session:
            start_time = session['start_time']
            f.write(f'**Date/Time:** {start_time}\n\n')
        
        if 'total_calories' in session:
            f.write(f'**Calories Burned:** {int(session['total_calories'])}\n\n')
        
        # Heart rate data
        hr_info = []
        if 'avg_heart_rate' in session:
            hr_info.append(f\"Average: {int(session['avg_heart_rate'])} bpm\")
        if 'max_heart_rate' in session:
            hr_info.append(f\"Max: {int(session['max_heart_rate'])} bpm\")
        if hr_info:
            f.write(f'**Heart Rate:** {', '.join(hr_info)}\n\n')
            
        # Speed data
        if 'avg_speed' in session:
            avg_speed = session['avg_speed'] * 3.6  # Convert m/s to km/h
            avg_speed_mph = avg_speed * 0.621371
            f.write(f'**Average Speed:** {avg_speed:.1f} km/h ({avg_speed_mph:.1f} mph)\n\n')
            
            if 'max_speed' in session:
                max_speed = session['max_speed'] * 3.6
                f.write(f'**Max Speed:** {max_speed:.1f} km/h\n\n')
        
        # Elevation data if available
        if 'total_ascent' in session and 'total_descent' in session:
            ascent = session['total_ascent']
            descent = session['total_descent']
            f.write(f'**Elevation:** Gain {int(ascent)}m, Loss {int(descent)}m\n\n')
        
        # Add lap information if available
        lap_df = df[df['record_type'] == 'lap']
        if len(lap_df) > 1:  # Only show if multiple laps
            f.write('## Lap Information\n\n')
            f.write('| Lap | Distance | Time | Avg HR | Speed |\n')
            f.write('|-----|----------|------|--------|---------|\n')
            
            for i, lap in lap_df.iterrows():
                lap_num = i + 1
                
                # Distance
                lap_dist = lap.get('total_distance', 0)
                dist_str = f\"{(lap_dist/1000):.2f} km\"
                
                # Time
                lap_time = lap.get('total_elapsed_time', 0)
                minutes = int(lap_time // 60)
                seconds = int(lap_time % 60)
                time_str = f\"{minutes}:{seconds:02d}\"
                
                # Heart Rate
                hr = lap.get('avg_heart_rate', 0)
                hr_str = f\"{int(hr)}\" if hr > 0 else \"–\"
                
                # Speed
                speed = lap.get('avg_speed', 0)
                if speed > 0:
                    speed_kph = speed * 3.6
                    speed_str = f\"{speed_kph:.1f} km/h\"
                else:
                    speed_str = \"–\"
                
                f.write(f\"| {lap_num} | {dist_str} | {time_str} | {hr_str} | {speed_str} |\\n\")
            
            f.write('\\n')
        
        # Performance assessment
        f.write('## Performance Assessment\n\n')
        f.write(f'This was a {sport_type.lower()} workout covering {distance_km:.1f} km. ')
        
        if 'avg_heart_rate' in session:
            hr = int(session['avg_heart_rate'])
            if hr < 120:
                intensity = \"low\"
            elif hr < 150:
                intensity = \"moderate\"
            else:
                intensity = \"high\"
            f.write(f'The {hr} bpm average heart rate indicates a {intensity} intensity effort.\\n\\n')
        else:
            f.write('\\n\\n')
        
        # Analysis prompt
        f.write('## Questions for ChatGPT Analysis\n\n')
        f.write(f'1. How does this {sport_type.lower()} workout compare to typical performances?\n')
        f.write(f'2. What aspects of this {sport_type.lower()} workout indicate good performance?\n')
        f.write('3. What would be appropriate recovery and follow-up workouts?\n')
        f.write('4. How could I improve my performance based on these metrics?\n')
    
    print(f'Created ChatGPT-friendly summary: {summary_path}')
except Exception as e:
    print(f'Error creating summary: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    echo "Error: Failed to create ChatGPT summary"
    exit 1
fi

# Open the summary file if it exists
if [[ -f "$SUMMARY_FILE" ]]; then
    echo "Opening summary file..."
    open "$SUMMARY_FILE"
    echo "Done! You can now copy the contents of the summary file into ChatGPT for analysis."
else
    echo "Error: Summary file not created"
    exit 1
fi

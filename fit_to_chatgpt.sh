#!/bin/zsh
# fit_to_chatgpt.sh - Convert a Garmin FIT file to ChatGPT-friendly format
#
# This script finds the most recently downloaded FIT file from Garmin Connect,
# converts it to CSV format, and creates a markdown summary suitable for
# importing into ChatGPT for workout analysis.
#
# Usage:
#   fit_to_chatgpt.sh [options]
#
# Options:
#   -f, --file FILE    Process a specific FIT file instead of the latest
#   -c, --charts       Generate visualization charts
#   -a, --advanced     Generate advanced sport-specific charts
#   -h, --help         Show this help message

# Get the directory where this script is located
SCRIPT_DIR=$(dirname "$0")

# Change to the script directory
cd "$SCRIPT_DIR" || { echo "Error: Failed to change directory"; exit 1; }

# Default settings
EXPORT_DIR="$SCRIPT_DIR/exports/activities"
CHATGPT_DIR="$SCRIPT_DIR/exports/chatgpt_ready"
GENERATE_CHARTS=false
GENERATE_ADVANCED=false
SPECIFIC_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        -c|--charts)
            GENERATE_CHARTS=true
            shift
            ;;
        -a|--advanced)
            GENERATE_CHARTS=true  # Advanced charts include basic charts
            GENERATE_ADVANCED=true
            shift
            ;;
        -h|--help)
            echo "Usage: fit_to_chatgpt.sh [options]"
            echo ""
            echo "Options:"
            echo "  -f, --file FILE    Process a specific FIT file instead of the latest"
            echo "  -c, --charts       Generate visualization charts"
            echo "  -a, --advanced     Generate advanced sport-specific charts"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run 'fit_to_chatgpt.sh --help' for usage information"
            exit 1
            ;;
    esac
done

# Create ChatGPT ready directory if it doesn't exist
mkdir -p "$CHATGPT_DIR"

# Find the FIT file to process
if [[ -n "$SPECIFIC_FILE" ]]; then
    if [[ -f "$SPECIFIC_FILE" ]]; then
        LATEST_FIT="$SPECIFIC_FILE"
        echo "Using specified FIT file: $LATEST_FIT"
    else
        echo "Error: Specified file not found: $SPECIFIC_FILE"
        exit 1
    fi
else
    # Find the most recently downloaded FIT file
    echo "Looking for the most recent FIT file in $EXPORT_DIR..."
    LATEST_FIT=$(find "$EXPORT_DIR" -name "*.fit" -type f -print0 | xargs -0 ls -t | head -1)
fi

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
            
            # Use Pace for running, Speed for other activities
            if sport_type.lower() == 'running':
                f.write('| Lap | Distance | Time | Avg HR | Pace  |\n')
                f.write('|-----|----------|------|--------|-------|\n')
            else:
                f.write('| Lap | Distance | Time | Avg HR | Speed |\n')
                f.write('|-----|----------|------|--------|-------|\n')
            
            for lap_num, (i, lap) in enumerate(lap_df.iterrows(), 1):
                
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
                
                # Speed or Pace
                speed = lap.get('avg_speed', 0)
                if speed > 0:
                    if sport_type.lower() == 'running':
                        # Calculate pace in min/km
                        pace_seconds_per_km = 1000 / speed  # seconds per km
                        pace_minutes = int(pace_seconds_per_km // 60)
                        pace_seconds = int(pace_seconds_per_km % 60)
                        pace_str = f\"{pace_minutes}:{pace_seconds:02d}/km\"
                    else:
                        # Show speed in km/h for non-running activities
                        speed_kph = speed * 3.6
                        pace_str = f\"{speed_kph:.1f} km/h\"
                else:
                    pace_str = \"–\"
                
                # Format with exact widths to match headers
                f.write(f\"| {lap_num:3} | {dist_str:8} | {time_str:4} | {hr_str:6} | {pace_str:5} |\\n\")
            
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

# Step 3 (Optional): Generate charts if requested
if [[ "$GENERATE_CHARTS" == true ]]; then
    if [[ "$GENERATE_ADVANCED" == true ]]; then
        echo "Generating advanced visualization charts..."
        # Try to use the dedicated module for advanced charts
        python3 -c "
import sys
from pathlib import Path
try:
    from utils.advanced_charts import generate_advanced_charts
    
    csv_path = Path('$CSV_FILE')
    result = generate_advanced_charts(csv_path)
    
    if result:
        print(f'Advanced charts generated successfully in {result}')
    else:
        print('Failed to generate advanced charts')
        sys.exit(1)
except ImportError as e:
    print(f'Error: Could not import advanced_charts module - {e}')
    print('Falling back to basic chart generation...')
    sys.exit(1)
except Exception as e:
    print(f'Error generating advanced charts: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

        # If advanced charts failed, fall back to basic charts
        if [[ $? -ne 0 ]]; then
            echo "Falling back to basic chart generation..."
        else
            # Advanced charts were generated successfully, we're done
            echo "Advanced charts generated successfully"
        fi
    fi
    
    # Generate basic charts (if advanced charts weren't generated or failed)
    if [[ "$GENERATE_ADVANCED" == false || $? -ne 0 ]]; then
        echo "Generating basic visualization charts..."
        python3 -c "
import sys
from pathlib import Path
try:
    # Import required modules
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
    
    # Get file paths
    csv_path = Path('$CSV_FILE')
    charts_dir = csv_path.parent / 'charts'
    charts_dir.mkdir(exist_ok=True)
    
    # Load the CSV data
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Extract different record types
    record_df = df[df['record_type'] == 'record'].copy()
    session_df = df[df['record_type'] == 'session'].copy()
    
    # Skip if no record data available
    if record_df.empty:
        print('No detailed record data found for visualization.')
        sys.exit(0)
        
    # Get sport type for chart titles
    sport_type = 'Activity'
    if not session_df.empty:
        sport = session_df.iloc[0].get('sport', 'activity')
        sport_type = sport.title()
    
    # Process timestamps for x-axis
    if 'timestamp' in record_df.columns:
        record_df['timestamp'] = pd.to_datetime(record_df['timestamp'])
        
        # Create minutes from start for x-axis
        if not record_df['timestamp'].isna().all():
            start_time = record_df['timestamp'].min()
            record_df['minutes'] = (record_df['timestamp'] - start_time).dt.total_seconds() / 60
        else:
            record_df['minutes'] = range(len(record_df))
    else:
        record_df['minutes'] = range(len(record_df))
    
    # Set chart style
    sns.set_style('whitegrid')
    
    # Track generated charts
    charts_created = []
    
    # 1. Heart Rate Chart
    if 'heart_rate' in record_df.columns:
        plt.figure(figsize=(10, 5))
        sns.lineplot(x='minutes', y='heart_rate', data=record_df, color='red')
        plt.title(f'Heart Rate During {sport_type}')
        plt.xlabel('Time (minutes)')
        plt.ylabel('Heart Rate (bpm)')
        plt.tight_layout()
        
        hr_chart = charts_dir / f\"{csv_path.stem}_heart_rate.png\"
        plt.savefig(hr_chart, dpi=150)
        plt.close()
        
        charts_created.append(('Heart Rate', hr_chart))
        print(f'Created heart rate chart: {hr_chart}')
    
    # 2. Speed Chart
    if 'speed' in record_df.columns:
        plt.figure(figsize=(10, 5))
        
        # Convert m/s to km/h for display
        record_df['speed_kmh'] = record_df['speed'] * 3.6
        
        sns.lineplot(x='minutes', y='speed_kmh', data=record_df, color='blue')
        plt.title(f'Speed During {sport_type}')
        plt.xlabel('Time (minutes)')
        plt.ylabel('Speed (km/h)')
        plt.tight_layout()
        
        speed_chart = charts_dir / f\"{csv_path.stem}_speed.png\"
        plt.savefig(speed_chart, dpi=150)
        plt.close()
        
        charts_created.append(('Speed', speed_chart))
        print(f'Created speed chart: {speed_chart}')
    
    # 3. Elevation Profile
    if 'altitude' in record_df.columns:
        plt.figure(figsize=(10, 4))
        sns.lineplot(x='minutes', y='altitude', data=record_df, color='green')
        plt.title(f'Elevation Profile for {sport_type}')
        plt.xlabel('Time (minutes)')
        plt.ylabel('Altitude (m)')
        plt.tight_layout()
        
        elev_chart = charts_dir / f\"{csv_path.stem}_elevation.png\"
        plt.savefig(elev_chart, dpi=150)
        plt.close()
        
        charts_created.append(('Elevation', elev_chart))
        print(f'Created elevation chart: {elev_chart}')
    
    # Update the summary file with chart links
    if charts_created and Path('$SUMMARY_FILE').exists():
        summary_path = Path('$SUMMARY_FILE')
        
        with open(summary_path, 'r') as f:
            content = f.read()
        
        # Add charts section
        charts_section = '\\n\\n## Workout Visualizations\\n\\n'
        charts_section += 'The following charts show your workout data:\\n\\n'
        
        for chart_name, chart_path in charts_created:
            rel_path = chart_path.name
            charts_section += f'- {chart_name} Chart: Available in the charts folder\\n'
        
        # Write updated summary
        with open(summary_path, 'w') as f:
            f.write(content + charts_section)
        
        print(f'Updated summary file with chart references')
    
except ImportError as e:
    print(f'Error: Missing dependency - {e}')
    print('To generate charts, install required packages: pip install matplotlib seaborn pandas')
except Exception as e:
    print(f'Error generating charts: {e}')
    import traceback
    traceback.print_exc()
"

    if [[ $? -ne 0 ]]; then
        echo "Warning: Chart generation failed, but continuing..."
    fi
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

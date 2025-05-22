#!/usr/bin/env python3
"""
Create a ChatGPT-friendly summary of a Garmin workout from CSV data
"""

import os
import sys
import pandas as pd
from pathlib import Path
import json

def create_chatgpt_summary(csv_file, output_file=None):
    """Create a ChatGPT-friendly summary of a workout from CSV data"""
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return None
    
    if not output_file:
        output_file = csv_path.with_suffix('.md')
    
    try:
        # Load the CSV data
        df = pd.read_csv(csv_path)
        
        # Extract record_type data for easier analysis
        record_df = df[df['record_type'] == 'record'].copy()
        session_df = df[df['record_type'] == 'session'].copy()
        lap_df = df[df['record_type'] == 'lap'].copy()
        
        # Create a summary markdown file
        with open(output_file, 'w') as f:
            f.write("# Garmin Activity Summary\n\n")
            
            # Basic activity info
            if not session_df.empty:
                session = session_df.iloc[0]
                sport = session.get('sport', 'Unknown')
                f.write(f"## Activity Type: {sport.title()}\n\n")
                
                # Date and time
                if 'start_time' in session:
                    start_time = session['start_time']
                    f.write(f"**Date and Time:** {start_time}\n\n")
                
                # Duration and Distance
                if 'total_elapsed_time' in session:
                    minutes = int(session['total_elapsed_time'] / 60)
                    seconds = int(session['total_elapsed_time'] % 60)
                    f.write(f"**Duration:** {minutes} minutes {seconds} seconds\n")
                
                if 'total_distance' in session:
                    distance_km = session['total_distance'] / 1000
                    distance_miles = distance_km * 0.621371
                    f.write(f"**Distance:** {distance_km:.2f} km ({distance_miles:.2f} miles)\n")
                
                # Calories
                if 'total_calories' in session:
                    f.write(f"**Calories Burned:** {int(session['total_calories'])}\n")
                
                # Heart Rate
                if 'avg_heart_rate' in session and 'max_heart_rate' in session:
                    f.write(f"**Heart Rate:** Avg {int(session['avg_heart_rate'])} bpm, Max {int(session['max_heart_rate'])} bpm\n")
                
                # Speed or Pace
                if 'avg_speed' in session and 'max_speed' in session:
                    avg_speed_kph = session['avg_speed'] * 3.6 if session['avg_speed'] < 100 else session['avg_speed']
                    max_speed_kph = session['max_speed'] * 3.6 if session['max_speed'] < 100 else session['max_speed']
                    avg_speed_mph = avg_speed_kph * 0.621371
                    max_speed_mph = max_speed_kph * 0.621371
                    
                    # If it's running, also show pace
                    if sport == 'running':
                        if avg_speed_kph > 0:
                            avg_pace_min_km = 60 / avg_speed_kph
                            avg_pace_min = int(avg_pace_min_km)
                            avg_pace_sec = int((avg_pace_min_km - avg_pace_min) * 60)
                            f.write(f"**Average Pace:** {avg_pace_min}:{avg_pace_sec:02d} min/km\n")
                    else:
                        f.write(f"**Speed:** Avg {avg_speed_kph:.1f} km/h ({avg_speed_mph:.1f} mph), " +
                                f"Max {max_speed_kph:.1f} km/h ({max_speed_mph:.1f} mph)\n")
                
                # Cadence (depends on sport)
                if 'avg_cadence' in session and 'max_cadence' in session:
                    multiplier = 2 if sport == 'running' else 1  # Running cadence is often one-sided
                    f.write(f"**Cadence:** Avg {int(session['avg_cadence']) * multiplier} spm, " +
                            f"Max {int(session['max_cadence']) * multiplier} spm\n")
                
                # Elevation if available
                if 'total_ascent' in session and 'total_descent' in session:
                    f.write(f"**Elevation:** Gain {int(session['total_ascent'])}m, Loss {int(session['total_descent'])}m\n")
                
                f.write("\n")
            
            # Lap information
            if not lap_df.empty and len(lap_df) > 1:  # Only show if multiple laps
                f.write("## Lap Information\n\n")
                f.write("| Lap | Distance (km) | Time | Avg HR | Avg Pace/Speed |\n")
                f.write("|-----|--------------|------|--------|---------------|\n")
                
                for i, lap in lap_df.iterrows():
                    lap_num = i + 1
                    lap_distance = lap.get('total_distance', 0) / 1000
                    
                    # Format lap time
                    lap_time = lap.get('total_elapsed_time', 0)
                    lap_minutes = int(lap_time / 60)
                    lap_seconds = int(lap_time % 60)
                    time_str = f"{lap_minutes}:{lap_seconds:02d}"
                    
                    # Heart rate
                    hr = lap.get('avg_heart_rate', 0)
                    hr_str = f"{int(hr)}" if hr > 0 else "N/A"
                    
                    # Pace or speed
                    speed = lap.get('avg_speed', 0)
                    if sport == 'running' and speed > 0:
                        # Calculate pace for running
                        pace_min_km = 60 / (speed * 3.6) if speed > 0 else 0
                        pace_min = int(pace_min_km)
                        pace_sec = int((pace_min_km - pace_min) * 60)
                        pace_str = f"{pace_min}:{pace_sec:02d} min/km"
                    else:
                        # Calculate speed for other activities
                        speed_kph = speed * 3.6 if speed < 100 else speed
                        pace_str = f"{speed_kph:.1f} km/h"
                    
                    f.write(f"| {lap_num} | {lap_distance:.2f} | {time_str} | {hr_str} | {pace_str} |\n")
                
                f.write("\n")
            
            # Record data visualization suggestion
            if not record_df.empty:
                f.write("## Data Points\n\n")
                f.write(f"This activity contains {len(record_df)} data points with details like heart rate, pace, cadence, and GPS coordinates.\n\n")
                
                # Available metrics
                metrics = []
                for col in ['heart_rate', 'speed', 'cadence', 'altitude', 'temperature', 'power']:
                    if col in record_df.columns:
                        metrics.append(col)
                
                if metrics:
                    f.write(f"**Available metrics:** {', '.join(metrics)}\n\n")
                
                # Add a note about GPS data
                if 'position_lat' in record_df.columns and 'position_long' in record_df.columns:
                    f.write("GPS position data is available for this activity.\n\n")
            
            f.write("## Analysis Tips\n\n")
            f.write("When analyzing this workout, consider:\n\n")
            f.write("1. How did your heart rate respond during different intensities?\n")
            if sport == 'cycling':
                f.write("2. Was your cadence consistent throughout the ride?\n")
                f.write("3. How did your performance change on hills versus flat sections?\n")
            elif sport == 'running':
                f.write("2. Was your pace consistent or did it vary throughout?\n")
                f.write("3. How did elevation changes affect your performance?\n")
            else:
                f.write("2. Were there any patterns in your performance over time?\n")
                f.write("3. Did any sections of the workout stand out as particularly challenging?\n")
            
        print(f"Created ChatGPT-friendly summary at {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error creating ChatGPT summary: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_chatgpt_summary.py <csv_file> [output_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    create_chatgpt_summary(csv_file, output_file)

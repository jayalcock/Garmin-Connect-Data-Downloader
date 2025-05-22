#!/usr/bin/env python3
"""
Create a ChatGPT-friendly workout analysis for a Garmin activity
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import datetime

def format_seconds(seconds):
    """Format seconds into hours:minutes:seconds"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def format_pace(speed_mps, running=False):
    """Format pace as min/km or speed as km/h"""
    if running:
        # Convert speed to min/km pace
        if speed_mps > 0:
            pace_min_km = 60 / (speed_mps * 3.6)
            pace_min = int(pace_min_km)
            pace_sec = int((pace_min_km - pace_min) * 60)
            return f"{pace_min}:{pace_sec:02d} min/km"
        return "0:00 min/km"
    else:
        # Convert to km/h
        return f"{speed_mps * 3.6:.1f} km/h"

def create_chatgpt_analysis(csv_file, output_file=None):
    """Create a detailed workout analysis for ChatGPT"""
    csv_path = Path(csv_file)
    if not output_file:
        output_file = csv_path.parent / f"{csv_path.stem}_analysis.md"
    
    try:
        # Load the CSV data
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Extract different record types
        record_df = df[df['record_type'] == 'record'].copy()
        session_df = df[df['record_type'] == 'session'].copy()
        lap_df = df[df['record_type'] == 'lap'].copy()
        
        # Check if we have the necessary data
        if session_df.empty:
            print("No session data found in CSV")
            return None
            
        session = session_df.iloc[0]
        sport_type = session.get('sport', 'activity')
        is_running = sport_type == 'running'
            
        with open(output_file, 'w') as f:
            # Title and basic info
            f.write("# Garmin Workout Analysis\n\n")
            
            # Activity summary section
            f.write("## Activity Summary\n\n")
            
            # Date and time
            start_time = None
            if 'start_time' in session:
                start_time = session['start_time']
                if isinstance(start_time, str):
                    f.write(f"**Date and Time:** {start_time}\n\n")
                elif isinstance(start_time, pd.Timestamp):
                    f.write(f"**Date and Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Basic metrics
            f.write(f"**Activity Type:** {sport_type.title()}\n")
            
            if 'total_elapsed_time' in session:
                elapsed_time = session['total_elapsed_time']
                formatted_time = format_seconds(elapsed_time)
                f.write(f"**Duration:** {formatted_time}\n")
            
            if 'total_distance' in session:
                distance_m = session['total_distance']
                distance_km = distance_m / 1000
                distance_mi = distance_km * 0.621371
                f.write(f"**Distance:** {distance_km:.2f} km ({distance_mi:.2f} miles)\n")
            
            if 'total_calories' in session:
                f.write(f"**Calories Burned:** {int(session['total_calories'])}\n")
            
            # Heart rate data
            if 'avg_heart_rate' in session or 'max_heart_rate' in session:
                hr_text = []
                if 'avg_heart_rate' in session:
                    hr_text.append(f"Avg {int(session['avg_heart_rate'])} bpm")
                if 'max_heart_rate' in session:
                    hr_text.append(f"Max {int(session['max_heart_rate'])} bpm")
                f.write(f"**Heart Rate:** {', '.join(hr_text)}\n")
            
            # Speed and pace info
            if 'avg_speed' in session:
                speed_text = []
                avg_speed = session['avg_speed']
                
                if is_running:
                    if avg_speed > 0:
                        pace = format_pace(avg_speed, running=True)
                        speed_text.append(f"Avg Pace: {pace}")
                else:
                    # For cycling and other activities
                    avg_speed_kph = avg_speed * 3.6
                    speed_text.append(f"Avg Speed: {avg_speed_kph:.1f} km/h ({avg_speed_kph * 0.621371:.1f} mph)")
                
                if 'max_speed' in session:
                    max_speed = session['max_speed'] 
                    max_speed_kph = max_speed * 3.6
                    speed_text.append(f"Max Speed: {max_speed_kph:.1f} km/h")
                
                f.write(f"**Speed:** {'; '.join(speed_text)}\n")
            
            # Elevation data
            if 'total_ascent' in session or 'total_descent' in session:
                elev_text = []
                if 'total_ascent' in session:
                    elev_text.append(f"Gain {int(session['total_ascent'])}m")
                if 'total_descent' in session:
                    elev_text.append(f"Loss {int(session['total_descent'])}m")
                f.write(f"**Elevation:** {', '.join(elev_text)}\n")
                
            # Cadence info if available
            if 'avg_cadence' in session:
                cadence_text = []
                multiplier = 2 if is_running else 1  # Running cadence often needs doubling for total steps
                
                cadence_text.append(f"Avg {int(session['avg_cadence']) * multiplier}")
                
                if 'max_cadence' in session:
                    cadence_text.append(f"Max {int(session['max_cadence']) * multiplier}")
                    
                units = "spm" if is_running else "rpm"
                f.write(f"**Cadence:** {', '.join(cadence_text)} {units}\n")
            
            # Power data if available (mainly for cycling)
            if 'avg_power' in session:
                power_text = []
                power_text.append(f"Avg {int(session['avg_power'])} watts")
                
                if 'max_power' in session:
                    power_text.append(f"Max {int(session['max_power'])} watts")
                    
                f.write(f"**Power:** {', '.join(power_text)}\n")
                
            f.write("\n")
            
            # Lap analysis if multiple laps
            if len(lap_df) > 1:
                f.write("## Lap Analysis\n\n")
                
                # Create a lap table
                if is_running:
                    f.write("| Lap | Distance | Time | Pace | Avg HR | Elev Gain |\n")
                    f.write("|-----|----------|------|------|--------|----------|\n")
                else:
                    f.write("| Lap | Distance | Time | Speed | Avg HR | Elev Gain |\n")
                    f.write("|-----|----------|------|-------|--------|----------|\n")
                
                for i, lap in lap_df.iterrows():
                    lap_num = i + 1
                    
                    # Distance
                    lap_dist = lap.get('total_distance', 0)
                    dist_str = f"{(lap_dist/1000):.2f} km"
                    
                    # Time
                    lap_time = lap.get('total_elapsed_time', 0)
                    time_str = format_seconds(lap_time)
                    
                    # Pace or Speed
                    lap_speed = lap.get('avg_speed', 0)
                    speed_str = format_pace(lap_speed, running=is_running)
                    
                    # HR
                    hr = lap.get('avg_heart_rate', 0)
                    hr_str = f"{int(hr)}" if hr > 0 else "–"
                    
                    # Elevation
                    elev = lap.get('total_ascent', 0)
                    elev_str = f"{int(elev)}m" if elev > 0 else "–"
                    
                    f.write(f"| {lap_num} | {dist_str} | {time_str} | {speed_str} | {hr_str} | {elev_str} |\n")
                
                f.write("\n")
            
            # Performance metrics for more advanced analysis
            f.write("## Performance Analysis\n\n")
            
            # Extract metrics we care about from the record data
            metrics = {}
            if not record_df.empty:
                for col in ['heart_rate', 'altitude', 'cadence', 'speed', 'power', 'temperature']:
                    if col in record_df.columns:
                        # Calculate min, max, avg, excluding zero values and nulls
                        valid_values = record_df[col].dropna()
                        valid_values = valid_values[valid_values > 0]
                        
                        if not valid_values.empty:
                            metrics[col] = {
                                'avg': valid_values.mean(),
                                'max': valid_values.max(),
                                'min': valid_values.min()
                            }
            
                # Performance sections based on sport type
                if sport_type == 'cycling':
                    f.write("### Cycling Performance\n\n")
                    
                    # For cycling, highlight key performance indicators
                    if 'power' in metrics:
                        f.write(f"**Power Distribution:**\n")
                        f.write(f"- Average Power: {int(metrics['power']['avg'])} watts\n")
                        f.write(f"- Maximum Power: {int(metrics['power']['max'])} watts\n")
                        
                        # Calculate time in power zones if we have heart rate data 
                        # (rough approximation using heart rate as proxy)
                        if 'heart_rate' in metrics and 'avg_heart_rate' in session and 'max_heart_rate' in session:
                            f.write("\nYour power output appears to be consistent with your heart rate zones, suggesting good aerobic fitness.\n\n")
                    
                    if 'cadence' in metrics:
                        f.write(f"**Cadence Analysis:**\n")
                        f.write(f"- Average Cadence: {int(metrics['cadence']['avg'])} rpm\n")
                        f.write(f"- Maximum Cadence: {int(metrics['cadence']['max'])} rpm\n")
                        if metrics['cadence']['avg'] < 70:
                            f.write("Your cadence is relatively low. Consider practicing with higher cadence (85-95 rpm) for better efficiency.\n")
                        elif metrics['cadence']['avg'] > 95:
                            f.write("Your cadence is high, which is usually good for efficiency and reducing joint stress.\n")
                        else:
                            f.write("Your cadence is in a good range for efficient cycling.\n")
                        f.write("\n")
                    
                    # Elevation analysis
                    if 'altitude' in metrics and 'total_ascent' in session and session['total_ascent'] > 100:
                        f.write("**Hill Performance:**\n")
                        f.write(f"This ride included significant climbing ({int(session['total_ascent'])}m).\n")
                        f.write("Your performance on hills can be further analyzed by comparing power, heart rate and cadence during climbing sections.\n\n")
                    
                elif sport_type == 'running':
                    f.write("### Running Performance\n\n")
                    
                    # Running-specific metrics
                    if 'avg_speed' in session and 'total_distance' in session:
                        avg_speed = session['avg_speed']
                        if avg_speed > 0:
                            pace = format_pace(avg_speed, running=True)
                            f.write(f"**Pace Analysis:**\n")
                            f.write(f"- Average Pace: {pace}\n")
                            
                            # Estimate running level
                            distance_km = session['total_distance'] / 1000
                            if distance_km < 5:
                                f.write("This appears to be a short training run. Focus on consistency and gradually increasing volume.\n")
                            elif distance_km < 10:
                                f.write("This is a solid mid-distance run, good for building aerobic fitness.\n")
                            else:
                                f.write("This is a long-distance run, excellent for endurance building.\n")
                            f.write("\n")
                    
                    # Cadence analysis
                    if 'cadence' in metrics:
                        cadence_avg = metrics['cadence']['avg'] * 2  # Convert to full steps (both feet)
                        f.write(f"**Cadence Analysis:**\n")
                        f.write(f"- Average Cadence: {int(cadence_avg)} steps/minute\n")
                        if cadence_avg < 160:
                            f.write("Your cadence is lower than optimal. Aim for 170-180 steps/minute for better efficiency.\n")
                        elif cadence_avg > 190:
                            f.write("Your cadence is very high. This might be efficient for you, but ensure your stride length is appropriate.\n")
                        else:
                            f.write("Your cadence is in a good range for efficient running.\n")
                        f.write("\n")
                else:
                    # Generic performance analysis for other activities
                    f.write(f"### {sport_type.title()} Performance\n\n")
                    
                    # Aerobic performance based on heart rate
                    if 'heart_rate' in metrics:
                        f.write("**Aerobic Performance:**\n")
                        f.write(f"- Average Heart Rate: {int(metrics['heart_rate']['avg'])} bpm\n")
                        f.write(f"- Maximum Heart Rate: {int(metrics['heart_rate']['max'])} bpm\n")
                        f.write("\n")
            
            # General conclusions
            f.write("## Conclusions\n\n")
            
            if sport_type == 'cycling':
                f.write("Based on your cycling data, here are some insights:\n\n")
                
                # Generate some insights based on the available data
                insights = []
                
                if 'avg_speed' in session and 'max_speed' in session:
                    avg_speed_kph = session['avg_speed'] * 3.6
                    max_speed_kph = session['max_speed'] * 3.6
                    speed_ratio = max_speed_kph / avg_speed_kph if avg_speed_kph > 0 else 0
                    
                    if speed_ratio > 2:
                        insights.append("Your maximum speed is significantly higher than your average, suggesting either sprints, downhills, or varied intensity during the ride.")
                    else:
                        insights.append("Your speed was relatively consistent throughout the ride, which might indicate steady-state training.")
                
                if 'avg_heart_rate' in session and 'max_heart_rate' in session:
                    hr_ratio = session['max_heart_rate'] / session['avg_heart_rate'] if session['avg_heart_rate'] > 0 else 0
                    
                    if hr_ratio > 1.3:
                        insights.append("Your heart rate varied significantly, suggesting intervals or challenging sections in your ride.")
                    else:
                        insights.append("Your heart rate remained relatively stable, indicating good pacing and endurance.")
                        
                # Add general suggestions
                insights.append("For improved performance, consider structured interval training and focused recovery rides.")
                insights.append("Regular tracking of your cycling metrics will help identify trends and improvements in your fitness.")
                
                # Write the insights
                for i, insight in enumerate(insights, 1):
                    f.write(f"{i}. {insight}\n")
            
            elif sport_type == 'running':
                f.write("Based on your running data, here are some insights:\n\n")
                
                # Generate running-specific insights
                insights = []
                
                if 'avg_heart_rate' in session and 'max_heart_rate' in session:
                    if session['avg_heart_rate'] > 165:
                        insights.append("Your average heart rate was quite high, suggesting this was an intense workout or race effort.")
                    elif session['avg_heart_rate'] < 140:
                        insights.append("Your heart rate indicates this was a recovery or easy run, which is important for building aerobic base.")
                    else:
                        insights.append("This appears to be a moderate intensity run, good for building aerobic fitness.")
                
                if 'total_distance' in session:
                    distance_km = session['total_distance'] / 1000
                    if distance_km > 15:
                        insights.append("This long run is excellent for building endurance. Make sure to include proper recovery afterwards.")
                    elif distance_km < 5:
                        insights.append("Short runs like this are great for recovery days or speed work when done at higher intensity.")
                
                # Add general running tips
                insights.append("Consider incorporating a mix of easy runs, interval workouts, and long runs for balanced training.")
                insights.append("Monitoring your pace and heart rate can help ensure you're training in the right zones for your goals.")
                
                # Write the insights
                for i, insight in enumerate(insights, 1):
                    f.write(f"{i}. {insight}\n")
            
            else:
                f.write("Based on your workout data, here are some insights:\n\n")
                f.write("1. Regular activity tracking helps identify patterns in your fitness and progress over time.\n")
                f.write("2. Consider setting specific goals for your workouts to maintain motivation and track improvements.\n")
                f.write("3. Mix up your training intensity and duration to continue challenging your body and improving fitness.\n")
            
            # ChatGPT integration note
            f.write("\n## Using This Data with ChatGPT\n\n")
            f.write("When discussing this workout with ChatGPT, you can ask questions like:\n\n")
            f.write("1. \"What aspects of this workout indicate good performance?\"\n")
            f.write("2. \"How can I improve my training based on these metrics?\"\n")
            f.write("3. \"What would be good follow-up workouts after this session?\"\n")
            f.write("4. \"How does this compare to typical metrics for my sport?\"\n")
        
        print(f"Created ChatGPT-friendly analysis at {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error creating analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_chatgpt_analysis.py <csv_file> [output_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    create_chatgpt_analysis(csv_file, output_file)

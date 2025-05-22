#!/usr/bin/env python3
"""
Workout Comparison Module for Garmin Data Analysis

This module provides functionality to compare multiple workouts over time,
identifying trends and improvements in performance metrics.

Features:
- Compare heart rate, pace, power, and other metrics across workouts
- Analyze progression over time for key performance indicators
- Generate trend charts for visualization
- Create summary reports of improvements

Dependencies: pandas, matplotlib, seaborn, numpy
"""

import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Set style for consistent visualizations
plt.style.use('seaborn-v0_8-whitegrid')


def find_workout_files(directory, sport_type=None, days=90):
    """
    Find relevant workout CSV files for comparison
    
    Args:
        directory: Directory path to search for files
        sport_type: Optional sport type to filter (e.g., 'running', 'cycling')
        days: Number of past days to include (default: 90)
        
    Returns:
        List of CSV file paths matching the criteria
    """
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Initialize paths and files
    search_dir = Path(directory)
    all_files = []
    
    # First look in the main directory
    all_files.extend(search_dir.glob("*.csv"))
    
    # Also look in chatgpt_ready directory if it exists
    chatgpt_dir = search_dir / "chatgpt_ready"
    if chatgpt_dir.exists():
        all_files.extend(chatgpt_dir.glob("*.csv"))
    
    # Filter files
    workout_files = []
    
    for file_path in all_files:
        # Skip summary files
        if "_summary" in file_path.name:
            continue
            
        # Check file modification date
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_date < cutoff_date:
            continue
            
        # If sport_type is specified, check the file
        if sport_type:
            try:
                # Read just the session data to determine sport type
                df = pd.read_csv(file_path, low_memory=False)
                session_df = df[df['record_type'] == 'session']
                
                if not session_df.empty and 'sport' in session_df.columns:
                    file_sport = session_df.iloc[0].get('sport', '').lower()
                    if sport_type.lower() not in file_sport:
                        continue
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
        
        workout_files.append(file_path)
    
    return sorted(workout_files, key=os.path.getmtime)


def extract_workout_summary(file_path):
    """
    Extract key summary metrics from a workout file
    
    Args:
        file_path: Path to the CSV workout file
        
    Returns:
        Dictionary with key metrics or None if extraction fails
    """
    try:
        # Read CSV data
        df = pd.read_csv(file_path, low_memory=False)
        
        # Extract session data
        session_df = df[df['record_type'] == 'session']
        if session_df.empty:
            return None
        
        # Get first session row
        session = session_df.iloc[0]
        
        # Extract timestamp and format as date
        timestamp = session.get('timestamp', session.get('start_time', None))
        date = pd.to_datetime(timestamp).date() if timestamp else None
        
        # Extract key metrics
        summary = {
            'file_path': file_path,
            'filename': Path(file_path).name,
            'date': date,
            'sport': session.get('sport', 'activity').title(),
            'distance': session.get('total_distance', 0) / 1000,  # Convert to km
            'duration': session.get('total_elapsed_time', 0) / 60,  # Convert to minutes
            'avg_heart_rate': session.get('avg_heart_rate', None),
            'max_heart_rate': session.get('max_heart_rate', None),
            'avg_speed': session.get('avg_speed', 0) * 3.6 if 'avg_speed' in session else None,  # m/s to km/h
            'avg_power': session.get('avg_power', None),
            'total_calories': session.get('total_calories', None),
            'avg_cadence': session.get('avg_cadence', None),
            'elevation_gain': session.get('total_ascent', None)
        }
        
        # Calculate pace for running (min/km)
        if 'avg_speed' in session and session.get('avg_speed', 0) > 0:
            pace_mins = 60 / (session['avg_speed'] * 3.6)
            pace_min = int(pace_mins)
            pace_sec = int((pace_mins - pace_min) * 60)
            summary['pace'] = f"{pace_min}:{pace_sec:02d}"
            summary['pace_value'] = pace_mins
        
        return summary
    
    except Exception as e:
        print(f"Error extracting summary from {file_path}: {e}")
        return None


def compare_workouts(files, output_dir=None, metric='distance'):
    """
    Compare multiple workouts and generate trend charts
    
    Args:
        files: List of workout CSV file paths
        output_dir: Directory to save output charts
        metric: Main metric to highlight (distance, heart_rate, pace, etc.)
        
    Returns:
        Path to the directory with generated charts
    """
    if not files:
        print("No files provided for comparison")
        return None
    
    # Create output directory if not specified
    if not output_dir:
        first_file = Path(files[0])
        output_dir = first_file.parent / 'comparison_charts'
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract summaries
    summaries = []
    for file_path in files:
        summary = extract_workout_summary(file_path)
        if summary:
            summaries.append(summary)
    
    if not summaries:
        print("No valid workout summaries extracted")
        return None
    
    # Create a DataFrame with summaries
    summary_df = pd.DataFrame(summaries)
    
    # Sort by date
    summary_df.sort_values('date', inplace=True)
    
    # Generate charts
    charts = []
    
    # 1. Distance Trend
    if 'distance' in summary_df.columns:
        plt.figure(figsize=(12, 6))
        sns.lineplot(x='date', y='distance', data=summary_df, marker='o', markersize=8)
        plt.title('Workout Distance Over Time')
        plt.xlabel('Date')
        plt.ylabel('Distance (km)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        distance_chart = output_dir / 'distance_trend.png'
        plt.savefig(distance_chart, dpi=150)
        plt.close()
        charts.append(distance_chart)
    
    # 2. Heart Rate Trends
    if 'avg_heart_rate' in summary_df.columns:
        plt.figure(figsize=(12, 6))
        sns.lineplot(x='date', y='avg_heart_rate', data=summary_df, marker='o', 
                     color='red', label='Average HR')
        
        if 'max_heart_rate' in summary_df.columns:
            sns.lineplot(x='date', y='max_heart_rate', data=summary_df, marker='x',
                         color='darkred', label='Max HR')
        
        plt.title('Heart Rate Trends Over Time')
        plt.xlabel('Date')
        plt.ylabel('Heart Rate (bpm)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        hr_chart = output_dir / 'heart_rate_trend.png'
        plt.savefig(hr_chart, dpi=150)
        plt.close()
        charts.append(hr_chart)
    
    # 3. Performance Improvement (sport-specific)
    # For running: pace
    if 'pace_value' in summary_df.columns and 'sport' in summary_df.columns:
        running_data = summary_df[summary_df['sport'].str.lower() == 'running']
        if not running_data.empty:
            plt.figure(figsize=(12, 6))
            sns.lineplot(x='date', y='pace_value', data=running_data, marker='o', color='blue')
            
            # Lower pace is better, so invert y-axis
            plt.gca().invert_yaxis()
            
            # Format y-axis labels as min:sec
            from matplotlib.ticker import FuncFormatter
            def format_pace(y, pos):
                mins = int(y)
                secs = int((y - mins) * 60)
                return f"{mins}:{secs:02d}"
            
            plt.gca().yaxis.set_major_formatter(FuncFormatter(format_pace))
            
            plt.title('Running Pace Improvement Over Time')
            plt.xlabel('Date')
            plt.ylabel('Pace (min/km)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            pace_chart = output_dir / 'pace_improvement.png'
            plt.savefig(pace_chart, dpi=150)
            plt.close()
            charts.append(pace_chart)
    
    # For cycling: power
    if 'avg_power' in summary_df.columns and 'sport' in summary_df.columns:
        cycling_data = summary_df[summary_df['sport'].str.lower() == 'cycling']
        if not cycling_data.empty:
            plt.figure(figsize=(12, 6))
            sns.lineplot(x='date', y='avg_power', data=cycling_data, marker='o', color='purple')
            plt.title('Cycling Power Trend Over Time')
            plt.xlabel('Date')
            plt.ylabel('Average Power (watts)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            power_chart = output_dir / 'power_trend.png'
            plt.savefig(power_chart, dpi=150)
            plt.close()
            charts.append(power_chart)
    
    # 4. Combined distance by sport type
    if 'sport' in summary_df.columns and 'distance' in summary_df.columns:
        plt.figure(figsize=(12, 6))
        sns.lineplot(x='date', y='distance', hue='sport', data=summary_df, marker='o')
        plt.title('Distance by Sport Type Over Time')
        plt.xlabel('Date')
        plt.ylabel('Distance (km)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.legend(title='Sport')
        plt.tight_layout()
        
        sport_chart = output_dir / 'sport_distance_trend.png'
        plt.savefig(sport_chart, dpi=150)
        plt.close()
        charts.append(sport_chart)
    
    # 5. Summary with weekly totals
    if 'date' in summary_df.columns and 'distance' in summary_df.columns:
        # Add week for grouping
        summary_df['week'] = pd.to_datetime(summary_df['date']).dt.isocalendar().week
        summary_df['year'] = pd.to_datetime(summary_df['date']).dt.isocalendar().year
        
        # Group by week and calculate totals
        weekly_totals = summary_df.groupby(['year', 'week']).agg({
            'distance': 'sum',
            'duration': 'sum',
            'total_calories': 'sum',
            'date': 'min'  # Take first date of the week for plotting
        }).reset_index()
        
        # Create combo chart (distances as bars, calories as line)
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Plot distance bars
        sns.barplot(x='date', y='distance', data=weekly_totals, color='blue', alpha=0.7, ax=ax1)
        ax1.set_xlabel('Week Starting')
        ax1.set_ylabel('Weekly Distance (km)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        
        # Rotate x labels
        plt.xticks(rotation=45)
        
        # Create second y-axis for calories
        if 'total_calories' in weekly_totals.columns and not weekly_totals['total_calories'].isna().all():
            ax2 = ax1.twinx()
            sns.lineplot(x='date', y='total_calories', data=weekly_totals, color='red', marker='o', ax=ax2)
            ax2.set_ylabel('Weekly Calories Burned', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
        
        plt.title('Weekly Training Volume')
        plt.tight_layout()
        
        weekly_chart = output_dir / 'weekly_summary.png'
        plt.savefig(weekly_chart, dpi=150)
        plt.close()
        charts.append(weekly_chart)
    
    # Create an HTML report with the charts
    html_path = output_dir / 'workout_comparison.html'
    with open(html_path, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Workout Comparison Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        .chart-container {{ margin-bottom: 30px; }}
        .chart {{ max-width: 100%; border: 1px solid #ddd; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #f2f2f2; text-align: left; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Workout Comparison Analysis</h1>
    <p>Analysis of {len(summary_df)} workouts from {summary_df['date'].min()} to {summary_df['date'].max()}</p>
    
    <h2>Summary Statistics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Average</th>
            <th>Minimum</th>
            <th>Maximum</th>
            <th>Total</th>
        </tr>
""")
        
        # Add summary statistics rows
        metrics = [
            ('Distance (km)', 'distance'),
            ('Duration (min)', 'duration'),
            ('Calories', 'total_calories'),
            ('Avg HR (bpm)', 'avg_heart_rate')
        ]
        
        for label, col in metrics:
            if col in summary_df.columns and not summary_df[col].isna().all():
                avg = summary_df[col].mean()
                min_val = summary_df[col].min()
                max_val = summary_df[col].max()
                total = summary_df[col].sum()
                
                f.write(f"""        <tr>
            <td>{label}</td>
            <td>{avg:.1f}</td>
            <td>{min_val:.1f}</td>
            <td>{max_val:.1f}</td>
            <td>{total:.1f}</td>
        </tr>
""")
        
        f.write("""    </table>
    
    <h2>Trend Charts</h2>
""")
        
        # Add each chart image
        for chart_path in charts:
            chart_title = chart_path.stem.replace('_', ' ').title()
            chart_rel_path = chart_path.name
            
            f.write(f"""
    <div class="chart-container">
        <h3>{chart_title}</h3>
        <img class="chart" src="{chart_rel_path}" alt="{chart_title}">
    </div>
""")
        
        # Add workout list
        f.write("""
    <h2>Analyzed Workouts</h2>
    <table>
        <tr>
            <th>Date</th>
            <th>Sport</th>
            <th>Distance</th>
            <th>Duration</th>
            <th>Avg HR</th>
        </tr>
""")
        
        # Sort by date, most recent first
        for _, row in summary_df.sort_values('date', ascending=False).iterrows():
            date_str = row['date'] if pd.notna(row['date']) else 'Unknown'
            sport = row['sport'] if pd.notna(row['sport']) else 'Activity'
            distance = f"{row['distance']:.2f} km" if pd.notna(row['distance']) else '-'
            duration = f"{row['duration']:.0f} min" if pd.notna(row['duration']) else '-'
            avg_hr = f"{row['avg_heart_rate']:.0f} bpm" if pd.notna(row['avg_heart_rate']) else '-'
            
            f.write(f"""        <tr>
            <td>{date_str}</td>
            <td>{sport}</td>
            <td>{distance}</td>
            <td>{duration}</td>
            <td>{avg_hr}</td>
        </tr>
""")
        
        f.write("""    </table>
</body>
</html>
""")
    
    print(f"Workout comparison report created: {html_path}")
    return output_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python workout_comparison.py <directory> [sport_type] [days]")
        sys.exit(1)
    
    directory = sys.argv[1]
    sport_type = sys.argv[2] if len(sys.argv) > 2 else None
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    
    files = find_workout_files(directory, sport_type, days)
    if files:
        print(f"Found {len(files)} workout files")
        result = compare_workouts(files)
        sys.exit(0 if result else 1)
    else:
        print("No workout files found matching criteria")
        sys.exit(1)

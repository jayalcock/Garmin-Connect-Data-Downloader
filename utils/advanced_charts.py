#!/usr/bin/env python3
"""
Advanced visualization module for sport-specific Garmin activity data

This module provides specialized visualizations for different activity types:
- Running: Pace charts, stride length analysis
- Cycling: Power zone distribution, cadence efficiency
- Swimming: Stroke analysis, SWOLF score trends
- General: Heart rate zone distribution, training effect

Dependencies: matplotlib, seaborn, pandas, numpy
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to prevent GUI issues
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Set default style
plt.style.use('seaborn-v0_8-whitegrid')


def detect_activity_type(df):
    """Detect the activity type from a dataframe"""
    if 'session' in df['record_type'].values:
        session_df = df[df['record_type'] == 'session']
        if not session_df.empty and 'sport' in session_df.columns:
            return session_df.iloc[0]['sport']
    
    # Default fallback if we can't determine
    return 'activity'


def create_hr_zone_chart(record_df, session_df, output_path):
    """
    Create a heart rate zone distribution chart
    
    Args:
        record_df: DataFrame with record data points
        session_df: DataFrame with session data (for max HR)
        output_path: Path to save the chart
        
    Returns:
        Path to the generated chart
    """
    if 'heart_rate' not in record_df.columns:
        return None
        
    # Get heart rate data
    hr_data = record_df['heart_rate'].dropna()
    if hr_data.empty:
        return None
        
    # Define zones based on max HR or use default zones
    max_hr = 190  # Default value
    if not session_df.empty and 'max_heart_rate' in session_df.columns:
        max_hr = session_df['max_heart_rate'].max()
    
    # Define HR zones (percentages of max HR)
    zones = {
        'Zone 1 (Recovery)': (0.5, 0.6),
        'Zone 2 (Easy)': (0.6, 0.7),
        'Zone 3 (Aerobic)': (0.7, 0.8),
        'Zone 4 (Threshold)': (0.8, 0.9),
        'Zone 5 (Maximum)': (0.9, 1.0)
    }
    
    # Calculate zone counts
    zone_counts = {}
    for name, (lower_pct, upper_pct) in zones.items():
        lower_hr = max_hr * lower_pct
        upper_hr = max_hr * upper_pct
        zone_counts[name] = ((hr_data >= lower_hr) & (hr_data < upper_hr)).sum()
    
    # Add values above zone 5
    zone_counts['Above Max'] = (hr_data >= max_hr).sum()
    
    # Create a pie chart
    plt.figure(figsize=(10, 6))
    
    # Create both a pie chart and bar chart for HR zones
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Color map for zones
    colors = ['#1e88e5', '#43a047', '#fdd835', '#fb8c00', '#e53935', '#8e24aa']
    
    # Pie chart
    labels = list(zone_counts.keys())
    values = list(zone_counts.values())
    
    # Filter out zeros for better visualization
    non_zero_labels = []
    non_zero_values = []
    for i, val in enumerate(values):
        if val > 0:
            non_zero_labels.append(labels[i])
            non_zero_values.append(val)
    
    explode = [0.1] * len(non_zero_labels)  # Explode all slices
    
    ax1.pie(non_zero_values, labels=non_zero_labels, autopct='%1.1f%%',
           startangle=90, colors=colors[:len(non_zero_labels)],
           explode=explode, shadow=True)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax1.set_title('Time in Heart Rate Zones')
    
    # Bar chart
    sns.barplot(x=list(zone_counts.keys()), y=list(zone_counts.values()), 
                palette=colors, ax=ax2)
    ax2.set_title('Minutes in Each Zone')
    ax2.set_ylabel('Time (minutes)')
    ax2.set_xlabel('Heart Rate Zone')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def create_running_analysis(record_df, session_df, output_dir):
    """
    Create specialized running charts
    
    Args:
        record_df: DataFrame with record data points
        session_df: DataFrame with session data
        output_dir: Directory to save the charts
        
    Returns:
        List of generated chart paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_charts = []
    
    # 1. Pace chart (inverted speed)
    if 'speed' in record_df.columns and 'timestamp' in record_df.columns:
        try:
            # Convert timestamps to minutes from start
            record_df['timestamp'] = pd.to_datetime(record_df['timestamp'])
            record_df['minutes'] = (record_df['timestamp'] - record_df['timestamp'].min()).dt.total_seconds() / 60
            
            # Calculate pace (min/km)
            valid_speed = record_df['speed'] > 0.2  # Filter very slow/stopped points
            record_df.loc[valid_speed, 'pace'] = 60 / (record_df.loc[valid_speed, 'speed'] * 3.6)
            
            plt.figure(figsize=(10, 6))
            ax = sns.lineplot(x='minutes', y='pace', data=record_df[valid_speed], color='blue')
            
            # Invert y-axis (lower pace is better)
            ax.invert_yaxis()
            
            # Format y-axis labels as min:sec
            from matplotlib.ticker import FuncFormatter
            def format_pace(y, pos):
                mins = int(y)
                secs = int((y - mins) * 60)
                return f"{mins}:{secs:02d}"
            
            ax.yaxis.set_major_formatter(FuncFormatter(format_pace))
            
            # Get average pace for annotation
            avg_pace = record_df.loc[valid_speed, 'pace'].mean()
            avg_min = int(avg_pace)
            avg_sec = int((avg_pace - avg_min) * 60)
            
            # Add average pace line and annotation
            plt.axhline(y=avg_pace, color='red', linestyle='--', alpha=0.7)
            plt.text(record_df['minutes'].max() * 0.75, avg_pace * 0.98, 
                     f"Average: {avg_min}:{avg_sec:02d}/km", 
                     color='red', fontweight='bold')
            
            plt.title('Running Pace Throughout Workout')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Pace (min/km)')
            plt.tight_layout()
            
            # Save chart
            pace_chart = output_dir / 'running_pace.png'
            plt.savefig(pace_chart, dpi=150)
            plt.close()
            
            generated_charts.append(pace_chart)
            print(f"Created running pace chart: {pace_chart}")
        except Exception as e:
            print(f"Error creating pace chart: {e}")
    
    # 2. Stride Length Analysis (if available)
    if 'speed' in record_df.columns and 'cadence' in record_df.columns:
        try:
            # Calculate stride length (in meters)
            # Formula: speed (m/s) / (cadence (steps/min) / 60) * 2 (for both feet)
            # This assumes cadence is measured as steps/minute for one foot
            
            valid_data = (record_df['speed'] > 0.2) & (record_df['cadence'] > 0)
            record_df.loc[valid_data, 'stride_length'] = (
                record_df.loc[valid_data, 'speed'] / (record_df.loc[valid_data, 'cadence'] / 60) * 2
            )
            
            # Filter out extreme values (very short or long strides)
            stride_data = record_df[
                (record_df['stride_length'] > 0.5) & 
                (record_df['stride_length'] < 3.0)
            ]
            
            if not stride_data.empty:
                # Create stride length vs pace scatter plot
                plt.figure(figsize=(10, 6))
                
                # Calculate pace (min/km)
                stride_data['pace'] = 60 / (stride_data['speed'] * 3.6)
                
                # Create scatter plot with hex binning for density
                plt.hexbin(stride_data['pace'], stride_data['stride_length'], 
                          gridsize=20, cmap='viridis', mincnt=1)
                
                plt.colorbar(label='Count')
                
                # Overlay trend line
                sns.regplot(x='pace', y='stride_length', data=stride_data, 
                           scatter=False, color='red', line_kws={'linewidth': 2})
                
                plt.title('Stride Length vs. Pace Relationship')
                plt.xlabel('Pace (min/km)')
                plt.ylabel('Stride Length (meters)')
                plt.tight_layout()
                
                # Save chart
                stride_chart = output_dir / 'stride_analysis.png'
                plt.savefig(stride_chart, dpi=150)
                plt.close()
                
                generated_charts.append(stride_chart)
                print(f"Created stride length analysis chart: {stride_chart}")
        except Exception as e:
            print(f"Error creating stride analysis chart: {e}")
    
    # 3. HR vs Pace chart
    if 'heart_rate' in record_df.columns and 'speed' in record_df.columns:
        try:
            # Create filtered dataframe
            hr_pace_df = record_df[
                (record_df['speed'] > 0.2) & 
                (record_df['heart_rate'] > 0)
            ].copy()
            
            # Calculate pace (min/km)
            hr_pace_df['pace'] = 60 / (hr_pace_df['speed'] * 3.6)
            
            plt.figure(figsize=(10, 6))
            
            # Create scatter plot with hex binning
            plt.hexbin(hr_pace_df['heart_rate'], hr_pace_df['pace'], 
                      gridsize=20, cmap='plasma', mincnt=1)
            
            plt.colorbar(label='Count')
            
            plt.title('Heart Rate vs. Pace Relationship')
            plt.xlabel('Heart Rate (bpm)')
            plt.ylabel('Pace (min/km)')
            
            # Invert y-axis (lower pace is better)
            plt.gca().invert_yaxis()
            
            # Format y-axis labels as min:sec
            from matplotlib.ticker import FuncFormatter
            def format_pace(y, pos):
                mins = int(y)
                secs = int((y - mins) * 60)
                return f"{mins}:{secs:02d}"
            
            plt.gca().yaxis.set_major_formatter(FuncFormatter(format_pace))
            
            plt.tight_layout()
            
            # Save chart
            hr_pace_chart = output_dir / 'hr_vs_pace.png'
            plt.savefig(hr_pace_chart, dpi=150)
            plt.close()
            
            generated_charts.append(hr_pace_chart)
            print(f"Created HR vs pace chart: {hr_pace_chart}")
        except Exception as e:
            print(f"Error creating HR vs pace chart: {e}")
    
    return generated_charts


def create_cycling_analysis(record_df, session_df, output_dir):
    """
    Create specialized cycling charts
    
    Args:
        record_df: DataFrame with record data points
        session_df: DataFrame with session data
        output_dir: Directory to save the charts
        
    Returns:
        List of generated chart paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_charts = []
    
    # 1. Power Zone Distribution (if power data exists)
    if 'power' in record_df.columns:
        try:
            power_data = record_df['power'].dropna()
            if not power_data.empty:
                # Get FTP (Functional Threshold Power) if available, otherwise estimate
                ftp = 250  # Default estimated FTP
                
                # Try to get max power from session to estimate FTP
                if not session_df.empty and 'max_power' in session_df.columns:
                    max_power = session_df['max_power'].max()
                    # Rough estimate: FTP is ~76% of max power
                    ftp = int(max_power * 0.76)
                    
                # If average power is available, use it for better FTP estimate
                if not session_df.empty and 'avg_power' in session_df.columns:
                    avg_power = session_df['avg_power'].iloc[0]
                    # Rough estimate: FTP is ~105-110% of average power for a hard workout
                    ftp = max(ftp, int(avg_power * 1.07))
                
                # Define power zones based on FTP
                power_zones = {
                    'Zone 1 (Recovery)': (0, 0.55 * ftp),
                    'Zone 2 (Endurance)': (0.55 * ftp, 0.75 * ftp),
                    'Zone 3 (Tempo)': (0.75 * ftp, 0.90 * ftp),
                    'Zone 4 (Threshold)': (0.90 * ftp, 1.05 * ftp),
                    'Zone 5 (VO2 Max)': (1.05 * ftp, 1.20 * ftp),
                    'Zone 6 (Anaerobic)': (1.20 * ftp, 1.50 * ftp),
                    'Zone 7 (Sprint)': (1.50 * ftp, float('inf'))
                }
                
                # Calculate time in each zone
                zone_seconds = {}
                for zone_name, (lower, upper) in power_zones.items():
                    zone_seconds[zone_name] = ((power_data >= lower) & (power_data < upper)).sum()
                
                # Create both a pie chart and bar chart for power zones
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
                
                # Color map for zones
                colors = ['blue', 'green', 'yellow', 'orange', 'red', 'purple', 'black']
                
                # Pie chart
                labels = list(zone_seconds.keys())
                values = list(zone_seconds.values())
                
                # Filter out zeros for better visualization
                non_zero_labels = []
                non_zero_values = []
                non_zero_colors = []
                for i, val in enumerate(values):
                    if val > 0:
                        non_zero_labels.append(labels[i])
                        non_zero_values.append(val)
                        non_zero_colors.append(colors[i])
                
                explode = [0.1] * len(non_zero_labels)  # Explode all slices
                wedges, texts, autotexts = ax1.pie(non_zero_values, labels=non_zero_labels, autopct='%1.1f%%',
                       startangle=90, colors=non_zero_colors,
                       explode=explode, shadow=True)
                
                # Make the percentage labels more readable
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                ax1.set_title(f'Power Zone Distribution (FTP Estimate: {ftp} watts)')
                
                # Bar chart
                sns.barplot(x=list(zone_seconds.keys()), y=list(zone_seconds.values()), 
                            palette=colors, ax=ax2)
                ax2.set_title('Seconds in Each Power Zone')
                ax2.set_ylabel('Time (seconds)')
                ax2.set_xlabel('Power Zone')
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
                
                plt.tight_layout()
                
                # Save chart
                power_zone_chart = output_dir / 'power_zone_distribution.png'
                plt.savefig(power_zone_chart, dpi=150)
                plt.close()
                
                generated_charts.append(power_zone_chart)
                print(f"Created power zone distribution chart: {power_zone_chart}")
        except Exception as e:
            print(f"Error creating power zone chart: {e}")
    
    # 2. Cadence vs Power analysis
    if 'cadence' in record_df.columns and 'power' in record_df.columns:
        try:
            # Filter for valid cadence and power values
            cp_df = record_df[(record_df['cadence'] > 0) & (record_df['power'] > 0)].copy()
            
            if not cp_df.empty:
                plt.figure(figsize=(10, 8))
                
                # Create a scatter plot with hex binning
                plt.hexbin(cp_df['cadence'], cp_df['power'], gridsize=20, 
                          cmap='viridis', mincnt=1)
                
                plt.colorbar(label='Count')
                
                # Add a trend line
                sns.regplot(x='cadence', y='power', data=cp_df, 
                           scatter=False, color='red', line_kws={'linewidth': 2})
                
                plt.title('Cadence vs. Power Relationship')
                plt.xlabel('Cadence (rpm)')
                plt.ylabel('Power (watts)')
                
                # Add optimal cadence range
                plt.axvspan(85, 95, alpha=0.2, color='green', label='Optimal Cadence Range')
                plt.legend()
                
                plt.tight_layout()
                
                # Save chart
                cadence_power_chart = output_dir / 'cadence_vs_power.png'
                plt.savefig(cadence_power_chart, dpi=150)
                plt.close()
                
                generated_charts.append(cadence_power_chart)
                print(f"Created cadence vs power chart: {cadence_power_chart}")
        except Exception as e:
            print(f"Error creating cadence vs power chart: {e}")
    
    # 3. Combined Effort and Terrain Analysis
    if all(col in record_df.columns for col in ['altitude', 'power', 'heart_rate', 'speed']):
        try:
            # Create filtered dataframe for valid data points
            combined_df = record_df[(record_df['speed'] > 0) & 
                                   (record_df['power'] > 0) & 
                                   (record_df['heart_rate'] > 0)].copy()
            
            if not combined_df.empty and 'timestamp' in combined_df.columns:
                # Convert timestamps to minutes from start
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                combined_df['minutes'] = (combined_df['timestamp'] - combined_df['timestamp'].min()).dt.total_seconds() / 60
                
                # Smooth altitude to reduce noise
                combined_df['altitude_smooth'] = combined_df['altitude'].rolling(window=10, min_periods=1).mean()
                
                # Calculate gradient (slope)
                combined_df['distance_m'] = combined_df['speed'].cumsum() * 1.0  # Rough approximation of distance
                combined_df['gradient'] = combined_df['altitude_smooth'].diff() / combined_df['distance_m'].diff() * 100
                combined_df['gradient'] = combined_df['gradient'].clip(-15, 15)  # Clip extreme values
                
                # Create a figure with 4 subplots sharing x-axis
                fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True, gridspec_kw={'hspace': 0.3})
                
                # Plot 1: Altitude
                axes[0].plot(combined_df['minutes'], combined_df['altitude_smooth'], color='green', linewidth=2)
                axes[0].set_ylabel('Altitude (m)')
                axes[0].set_title('Terrain and Performance Analysis')
                
                # Plot 2: Gradient
                axes[1].plot(combined_df['minutes'], combined_df['gradient'], color='orange', linewidth=1.5)
                axes[1].axhline(y=0, color='gray', linestyle='--')
                axes[1].set_ylabel('Gradient (%)')
                
                # Plot 3: Power
                axes[2].plot(combined_df['minutes'], combined_df['power'], color='red', linewidth=1.5)
                # Add smoothed power line
                axes[2].plot(combined_df['minutes'], 
                            combined_df['power'].rolling(window=30, min_periods=1).mean(), 
                            color='darkred', linewidth=2, alpha=0.7)
                axes[2].set_ylabel('Power (watts)')
                
                # Plot 4: Heart Rate
                axes[3].plot(combined_df['minutes'], combined_df['heart_rate'], color='blue', linewidth=1.5)
                axes[3].set_ylabel('Heart Rate (bpm)')
                axes[3].set_xlabel('Time (minutes)')
                
                plt.tight_layout()
                
                # Save chart
                terrain_analysis_chart = output_dir / 'terrain_analysis.png'
                plt.savefig(terrain_analysis_chart, dpi=150)
                plt.close()
                
                generated_charts.append(terrain_analysis_chart)
                print(f"Created terrain and performance analysis chart: {terrain_analysis_chart}")
        except Exception as e:
            print(f"Error creating terrain analysis chart: {e}")
    
    return generated_charts


def create_swimming_analysis(record_df, session_df, output_dir):
    """
    Create specialized swimming charts
    
    Args:
        record_df: DataFrame with record data points
        session_df: DataFrame with session data
        output_dir: Directory to save the charts
        
    Returns:
        List of generated chart paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_charts = []
    
    # 1. Lap Analysis (Swimming laps are more important than other sports)
    lap_df = None
    try:
        # Find lap data in the main dataframes
        if 'record_type' in record_df.columns:
            lap_df = record_df[record_df['record_type'] == 'lap'].copy()
        
        if lap_df is None or lap_df.empty:
            # If no lap data found in record_df, try looking for a separate lap dataframe
            from pathlib import Path
            csv_path = Path(output_dir).parent
            possible_file = csv_path / f"{csv_path.stem.replace('_summary', '')}.csv"
            
            if possible_file.exists():
                import pandas as pd
                full_df = pd.read_csv(possible_file, low_memory=False)
                lap_df = full_df[full_df['record_type'] == 'lap'].copy()
        
        if lap_df is not None and not lap_df.empty and len(lap_df) > 1:
            plt.figure(figsize=(12, 6))
            
            # Extract lap times and distances
            lap_df['lap_time'] = lap_df.get('total_elapsed_time', lap_df.get('total_timer_time', 0))
            
            # Convert to minutes for display
            lap_df['lap_minutes'] = lap_df['lap_time'] / 60.0
            
            # Create bar chart of lap times
            plt.bar(range(1, len(lap_df) + 1), lap_df['lap_minutes'], color='skyblue')
            plt.axhline(y=lap_df['lap_minutes'].mean(), color='red', linestyle='--', 
                       label=f'Avg: {lap_df["lap_minutes"].mean():.2f} min')
            
            plt.title('Swimming Lap Times')
            plt.xlabel('Lap Number')
            plt.ylabel('Time (minutes)')
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(range(1, len(lap_df) + 1))
            
            # Save chart
            lap_chart = output_dir / 'swim_lap_times.png'
            plt.savefig(lap_chart, dpi=150)
            plt.close()
            
            generated_charts.append(lap_chart)
            print(f"Created swimming lap times chart: {lap_chart}")
            
            # 2. SWOLF Score Chart (Swimming efficiency)
            if 'swolf' in lap_df.columns or 'swim_stroke' in lap_df.columns:
                plt.figure(figsize=(12, 6))
                
                # Use SWOLF if available, otherwise calculate from stroke count and time
                if 'swolf' in lap_df.columns:
                    swolf_data = lap_df['swolf']
                elif 'swim_stroke' in lap_df.columns and 'total_strokes' in lap_df.columns:
                    # Estimate SWOLF from strokes and time
                    swolf_data = lap_df['total_strokes'] + lap_df['lap_minutes'] * 60
                else:
                    swolf_data = None
                
                if swolf_data is not None:
                    plt.plot(range(1, len(lap_df) + 1), swolf_data, 'o-', color='teal', linewidth=2)
                    plt.axhline(y=swolf_data.mean(), color='red', linestyle='--', 
                               label=f'Avg: {swolf_data.mean():.1f}')
                    
                    plt.title('SWOLF Score by Lap (Lower is Better)')
                    plt.xlabel('Lap Number')
                    plt.ylabel('SWOLF Score')
                    plt.legend()
                    plt.grid(True, alpha=0.3)
                    plt.xticks(range(1, len(lap_df) + 1))
                    
                    # Save chart
                    swolf_chart = output_dir / 'swim_swolf.png'
                    plt.savefig(swolf_chart, dpi=150)
                    plt.close()
                    
                    generated_charts.append(swolf_chart)
                    print(f"Created SWOLF efficiency chart: {swolf_chart}")
            
            # 3. Stroke Rate Analysis
            if 'total_strokes' in lap_df.columns:
                plt.figure(figsize=(12, 6))
                
                # Calculate strokes per minute
                lap_df['strokes_per_minute'] = lap_df['total_strokes'] / lap_df['lap_minutes']
                
                # Create line chart
                plt.plot(range(1, len(lap_df) + 1), lap_df['strokes_per_minute'], 
                       'o-', color='purple', linewidth=2)
                
                plt.title('Stroke Rate by Lap')
                plt.xlabel('Lap Number')
                plt.ylabel('Strokes per Minute')
                plt.grid(True, alpha=0.3)
                plt.xticks(range(1, len(lap_df) + 1))
                
                # Save chart
                stroke_chart = output_dir / 'swim_stroke_rate.png'
                plt.savefig(stroke_chart, dpi=150)
                plt.close()
                
                generated_charts.append(stroke_chart)
                print(f"Created stroke rate chart: {stroke_chart}")
    
    except Exception as e:
        print(f"Error creating swimming charts: {e}")
    
    return generated_charts


def generate_advanced_charts(csv_file, output_dir=None):
    """
    Generate advanced sport-specific charts for a workout
    
    Args:
        csv_file: Path to the CSV file with workout data
        output_dir: Directory to save the charts (defaults to 'advanced_charts' subdirectory)
        
    Returns:
        Path to the charts directory if successful, None otherwise
    """
    try:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return None
            
        # Set output directory
        if output_dir:
            charts_dir = Path(output_dir)
        else:
            charts_dir = csv_path.parent / 'advanced_charts'
            
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Read CSV data
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Extract different record types
        record_df = df[df['record_type'] == 'record'].copy()
        session_df = df[df['record_type'] == 'session'].copy()
        lap_df = df[df['record_type'] == 'lap'].copy()
        
        if record_df.empty:
            print("No record data found in CSV")
            return None
            
        # Detect activity type
        activity_type = detect_activity_type(df).lower()
        print(f"Detected activity type: {activity_type}")
        
        # Generate charts based on activity type
        generated_charts = []
        
        # HR Zone chart (works for all activity types)
        hr_zone_chart = charts_dir / f"{csv_path.stem}_hr_zones.png"
        if create_hr_zone_chart(record_df, session_df, hr_zone_chart):
            generated_charts.append(hr_zone_chart)
            print(f"Created HR zone chart: {hr_zone_chart}")
        
        # Activity-specific visualizations
        if activity_type == 'running':
            running_charts = create_running_analysis(record_df, session_df, charts_dir)
            generated_charts.extend(running_charts)
            
        elif activity_type == 'cycling' or activity_type == 'biking':
            cycling_charts = create_cycling_analysis(record_df, session_df, charts_dir)
            generated_charts.extend(cycling_charts)
            
        elif activity_type == 'swimming':
            swimming_charts = create_swimming_analysis(record_df, session_df, charts_dir)
            generated_charts.extend(swimming_charts)
        
        # Create a dashboard HTML file linking all charts
        if generated_charts:
            html_path = charts_dir / f"{csv_path.stem}_dashboard.html"
            
            with open(html_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{activity_type.title()} Workout Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .chart-container {{ margin-bottom: 30px; }}
        .chart {{ max-width: 100%; border: 1px solid #ddd; border-radius: 5px; }}
        h2 {{ color: #3498db; }}
    </style>
</head>
<body>
    <h1>{activity_type.title()} Workout Analysis Dashboard</h1>
    <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
""")
                
                # Add each chart
                for chart_path in generated_charts:
                    chart_title = chart_path.stem.replace('_', ' ').title()
                    chart_rel_path = chart_path.name
                    
                    f.write(f"""
    <div class="chart-container">
        <h2>{chart_title}</h2>
        <img class="chart" src="{chart_rel_path}" alt="{chart_title}">
    </div>
""")
                
                f.write("""
</body>
</html>
""")
            
            print(f"Created dashboard HTML: {html_path}")
            
        return charts_dir if generated_charts else None
        
    except Exception as e:
        print(f"Error generating advanced charts: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python advanced_charts.py <csv_file> [output_dir]")
        sys.exit(1)
        
    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = generate_advanced_charts(csv_file, output_dir)
    sys.exit(0 if result else 1)

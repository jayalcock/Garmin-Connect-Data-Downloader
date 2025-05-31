#!/usr/bin/env python3
"""
Garmin Workout Visualization

This module creates visualizations and charts for Garmin workout data.
It is designed to work with CSV files generated from FIT files.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

def generate_workout_charts(csv_file, output_dir=None):
    """
    Generate a set of charts for a workout based on CSV data
    
    Args:
        csv_file: Path to the CSV file containing workout data
        output_dir: Directory to save the charts (defaults to a 'charts' subdirectory)
        
    Returns:
        Path to the charts directory if successful, None otherwise
    """
    try:
        # Import visualization libraries and set non-interactive backend
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend to prevent GUI issues
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required modules with: pip install matplotlib seaborn")
        return None
        
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return None
        
    # Set up output directory
    if output_dir:
        charts_dir = Path(output_dir)
    else:
        charts_dir = csv_path.parent / 'charts'
    
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load the CSV data
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Extract different record types
        record_df = df[df['record_type'] == 'record'].copy()
        session_df = df[df['record_type'] == 'session'].copy()
        lap_df = df[df['record_type'] == 'lap'].copy()
        
        # Skip if no record data available
        if record_df.empty:
            print("No record data found for visualization")
            return None
            
        # Get sport type for chart titles
        sport_type = "Activity"
        if not session_df.empty:
            sport = session_df.iloc[0].get('sport', 'activity')
            sport_type = sport.title()
            
        # Process timestamps for x-axis
        if 'timestamp' in record_df.columns:
            record_df['timestamp'] = pd.to_datetime(record_df['timestamp'])
            
            # Create relative time axis (minutes from start)
            if not record_df['timestamp'].isna().all():
                start_time = record_df['timestamp'].min()
                record_df['minutes'] = (record_df['timestamp'] - start_time).dt.total_seconds() / 60
            else:
                record_df['minutes'] = range(len(record_df))
        else:
            # No timestamp available, use simple index
            record_df['minutes'] = range(len(record_df))
            
        # Set seaborn style
        sns.set_style("whitegrid")
        
        # Track generated charts for reporting
        charts_created = []
        
        # 1. Heart Rate Chart
        if 'heart_rate' in record_df.columns:
            plt.figure(figsize=(10, 5))
            ax = sns.lineplot(x='minutes', y='heart_rate', data=record_df, color='red')
            
            # Add HR zones if we can estimate max HR
            if not session_df.empty and 'max_heart_rate' in session_df.columns:
                max_hr = session_df['max_heart_rate'].max()
                
                # Add zone guidelines
                zone_colors = ['lightblue', 'lightgreen', 'yellow', 'orange', 'red']
                zone_labels = ['Very Light', 'Light', 'Moderate', 'Hard', 'Max']
                zone_pcts = [0.6, 0.7, 0.8, 0.9, 1.0]
                
                for i, (pct, color, label) in enumerate(zip(zone_pcts, zone_colors, zone_labels)):
                    hr_value = max_hr * pct
                    plt.axhline(y=hr_value, color=color, linestyle='--', alpha=0.5)
                    plt.text(record_df['minutes'].max() * 0.02, hr_value + 2, f"Zone {i+1}: {label}", 
                             fontsize=8, color='gray')
                    
            plt.title(f'Heart Rate During {sport_type}')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Heart Rate (bpm)')
            plt.tight_layout()
            
            # Save the chart
            hr_chart = charts_dir / f"{csv_path.stem}_heart_rate.png"
            plt.savefig(hr_chart, dpi=150)
            plt.close()
            
            charts_created.append(('Heart Rate', hr_chart))
            print(f"Created heart rate chart: {hr_chart}")
            
        # 2. Speed Chart
        if 'speed' in record_df.columns:
            plt.figure(figsize=(10, 5))
            
            # Convert m/s to km/h for display
            record_df['speed_kmh'] = record_df['speed'] * 3.6
            
            # Get sport type for appropriate units
            pace_chart = False
            if not session_df.empty:
                sport = session_df.iloc[0].get('sport', 'activity')
                if sport.lower() == 'running':
                    # For running, calculate pace (min/km) instead of speed
                    pace_chart = True
                    valid_speed = record_df['speed'] > 0.3  # Filter out very slow speeds
                    record_df.loc[valid_speed, 'pace_min_km'] = 60 / (record_df.loc[valid_speed, 'speed_kmh'])
                    
                    # Plot pace
                    ax = sns.lineplot(x='minutes', y='pace_min_km', data=record_df[valid_speed], color='blue')
                    plt.gca().invert_yaxis()  # Invert y-axis for pace (lower is better)
                    plt.title(f'Running Pace During {sport_type}')
                    plt.xlabel('Time (minutes)')
                    plt.ylabel('Pace (min/km)')
                    
                    # Format y-axis as time
                    from matplotlib.ticker import FuncFormatter
                    def format_pace(y, pos):
                        minutes = int(y)
                        seconds = int((y - minutes) * 60)
                        return f"{minutes}:{seconds:02d}"
                    
                    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_pace))
                    
                else:
                    # Regular speed chart
                    ax = sns.lineplot(x='minutes', y='speed_kmh', data=record_df, color='blue')
                    plt.title(f'Speed During {sport_type}')
                    plt.xlabel('Time (minutes)')
                    plt.ylabel('Speed (km/h)')
            else:
                # No session data, just plot speed
                ax = sns.lineplot(x='minutes', y='speed_kmh', data=record_df, color='blue')
                plt.title('Speed During Workout')
                plt.xlabel('Time (minutes)')
                plt.ylabel('Speed (km/h)')
                
            plt.tight_layout()
            
            # Save chart
            if pace_chart:
                speed_chart = charts_dir / f"{csv_path.stem}_pace.png"
                charts_created.append(('Pace', speed_chart))
                print(f"Created pace chart: {speed_chart}")
            else:
                speed_chart = charts_dir / f"{csv_path.stem}_speed.png"
                charts_created.append(('Speed', speed_chart))
                print(f"Created speed chart: {speed_chart}")
                
            plt.savefig(speed_chart, dpi=150)
            plt.close()
            
        # 3. Elevation Profile
        if 'altitude' in record_df.columns:
            plt.figure(figsize=(10, 4))
            
            # Create a smooth elevation profile
            record_df['altitude_smooth'] = record_df['altitude'].rolling(window=10, min_periods=1).mean()
            
            # Plot elevation
            sns.lineplot(x='minutes', y='altitude_smooth', data=record_df, color='green')
            
            # Fill area under the curve
            plt.fill_between(record_df['minutes'], record_df['altitude_smooth'].min(), record_df['altitude_smooth'], 
                             alpha=0.2, color='green')
            
            # Add total elevation gain if available
            if not session_df.empty and 'total_ascent' in session_df.columns:
                total_ascent = session_df['total_ascent'].iloc[0]
                plt.text(0.02, 0.95, f"Total Gain: {int(total_ascent)}m", 
                         transform=plt.gca().transAxes, fontsize=12,
                         bbox=dict(facecolor='white', alpha=0.5))
                
            plt.title(f'Elevation Profile for {sport_type}')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Altitude (m)')
            plt.tight_layout()
            
            # Save chart
            elev_chart = charts_dir / f"{csv_path.stem}_elevation.png"
            plt.savefig(elev_chart, dpi=150)
            plt.close()
            
            charts_created.append(('Elevation', elev_chart))
            print(f"Created elevation chart: {elev_chart}")
            
        # 4. Cadence Chart
        if 'cadence' in record_df.columns:
            plt.figure(figsize=(10, 4))
            
            # Determine if we need to multiply cadence (for running)
            cadence_multiplier = 1
            cadence_unit = "rpm"
            if not session_df.empty:
                sport = session_df.iloc[0].get('sport', 'activity')
                if sport.lower() == 'running':
                    cadence_multiplier = 2  # Double for running (convert to steps/min)
                    cadence_unit = "spm"
                    
            # Plot cadence
            record_df['cadence_display'] = record_df['cadence'] * cadence_multiplier
            sns.lineplot(x='minutes', y='cadence_display', data=record_df, color='purple')
            
            plt.title(f'Cadence During {sport_type}')
            plt.xlabel('Time (minutes)')
            plt.ylabel(f'Cadence ({cadence_unit})')
            plt.tight_layout()
            
            # Save chart
            cadence_chart = charts_dir / f"{csv_path.stem}_cadence.png"
            plt.savefig(cadence_chart, dpi=150)
            plt.close()
            
            charts_created.append(('Cadence', cadence_chart))
            print(f"Created cadence chart: {cadence_chart}")
            
        # 5. Power Chart (mainly for cycling)
        if 'power' in record_df.columns:
            plt.figure(figsize=(10, 4))
            
            # Plot power
            sns.lineplot(x='minutes', y='power', data=record_df, color='orange')
            
            # Add smoothed power line
            record_df['power_smooth'] = record_df['power'].rolling(window=30, min_periods=1).mean()
            sns.lineplot(x='minutes', y='power_smooth', data=record_df, color='red', label='30s avg')
            
            plt.title(f'Power Output During {sport_type}')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Power (watts)')
            plt.legend()
            plt.tight_layout()
            
            # Save chart
            power_chart = charts_dir / f"{csv_path.stem}_power.png"
            plt.savefig(power_chart, dpi=150)
            plt.close()
            
            charts_created.append(('Power', power_chart))
            print(f"Created power chart: {power_chart}")
            
        # 6. Combined chart (HR and Speed)
        if 'heart_rate' in record_df.columns and 'speed' in record_df.columns:
            fig, ax1 = plt.subplots(figsize=(12, 5))
            
            # Primary y-axis: Heart Rate
            color = 'tab:red'
            ax1.set_xlabel('Time (minutes)')
            ax1.set_ylabel('Heart Rate (bpm)', color=color)
            ax1.plot(record_df['minutes'], record_df['heart_rate'], color=color, alpha=0.8)
            ax1.tick_params(axis='y', labelcolor=color)
            
            # Secondary y-axis: Speed
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('Speed (km/h)', color=color)
            ax2.plot(record_df['minutes'], record_df['speed'] * 3.6, color=color, alpha=0.8)
            ax2.tick_params(axis='y', labelcolor=color)
            
            fig.suptitle(f'Heart Rate and Speed During {sport_type}')
            fig.tight_layout()
            
            # Save chart
            combined_chart = charts_dir / f"{csv_path.stem}_hr_speed.png"
            plt.savefig(combined_chart, dpi=150)
            plt.close()
            
            charts_created.append(('Combined HR/Speed', combined_chart))
            print(f"Created combined HR/Speed chart: {combined_chart}")
            
        # 7. Lap Analysis Chart (if multiple laps)
        if len(lap_df) > 1:
            # Create lap comparison chart
            metrics = []
            
            if 'avg_heart_rate' in lap_df.columns:
                metrics.append(('avg_heart_rate', 'Heart Rate (bpm)'))
            
            if 'avg_speed' in lap_df.columns:
                # Get sport type for appropriate units
                if not session_df.empty:
                    sport = session_df.iloc[0].get('sport', 'activity')
                    if sport.lower() == 'running':
                        # For running, show pace (min/km) instead of speed
                        valid_speed = lap_df['avg_speed'] > 0
                        lap_df.loc[valid_speed, 'avg_pace'] = 60 / (lap_df.loc[valid_speed, 'avg_speed'] * 3.6)
                        metrics.append(('avg_pace', 'Avg Pace (min/km)'))
                    else:
                        # For other activities, show speed in km/h
                        lap_df['avg_speed_kmh'] = lap_df['avg_speed'] * 3.6
                        metrics.append(('avg_speed_kmh', 'Avg Speed (km/h)'))
                else:
                    # Default to speed if no session data
                    lap_df['avg_speed_kmh'] = lap_df['avg_speed'] * 3.6
                    metrics.append(('avg_speed_kmh', 'Avg Speed (km/h)'))
                
            if 'total_distance' in lap_df.columns:
                # Convert to km
                lap_df['distance_km'] = lap_df['total_distance'] / 1000
                metrics.append(('distance_km', 'Distance (km)'))
                
            if 'total_elapsed_time' in lap_df.columns:
                # Convert to minutes
                lap_df['time_min'] = lap_df['total_elapsed_time'] / 60
                metrics.append(('time_min', 'Time (minutes)'))
                
            if metrics:
                lap_df['lap_number'] = range(1, len(lap_df) + 1)
                
                # Create a lap comparison chart
                fig, axs = plt.subplots(len(metrics), 1, figsize=(10, 3*len(metrics)), sharex=True)
                
                for i, (metric, label) in enumerate(metrics):
                    if len(metrics) > 1:
                        ax = axs[i]
                    else:
                        ax = axs
                        
                    sns.barplot(x='lap_number', y=metric, data=lap_df, ax=ax)
                    ax.set_ylabel(label)
                    ax.set_title(f'Lap {label}')
                    
                    # Special formatting for pace charts
                    if metric == 'avg_pace':
                        # Format y-axis as min:sec for pace
                        from matplotlib.ticker import FuncFormatter
                        def format_pace(y, pos):
                            minutes = int(y)
                            seconds = int((y - minutes) * 60)
                            return f"{minutes}:{seconds:02d}"
                        
                        ax.yaxis.set_major_formatter(FuncFormatter(format_pace))
                    
                fig.suptitle(f'Lap Analysis for {sport_type}')
                plt.xlabel('Lap Number')
                plt.tight_layout()
                
                # Save chart
                lap_chart = charts_dir / f"{csv_path.stem}_lap_analysis.png"
                plt.savefig(lap_chart, dpi=150)
                plt.close()
                
                charts_created.append(('Lap Analysis', lap_chart))
                print(f"Created lap analysis chart: {lap_chart}")
                
        return charts_dir if charts_created else None
    
    except Exception as e:
        print(f"Error generating charts: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_summary_with_charts(summary_file, charts_dir):
    """Add links to generated charts in the summary markdown file"""
    summary_path = Path(summary_file)
    charts_dir = Path(charts_dir)
    
    if not summary_path.exists():
        print(f"Summary file not found: {summary_path}")
        return False
        
    # Get list of chart files
    chart_files = list(charts_dir.glob('*.png'))
    if not chart_files:
        print("No charts found in directory")
        return False
        
    try:
        # Read existing summary
        with open(summary_path, 'r') as f:
            content = f.read()
            
        # Add charts section
        charts_section = "\n\n## Workout Visualizations\n\n"
        charts_section += "The following charts show your workout data:\n\n"
        
        # List all charts
        for chart in chart_files:
            chart_name = chart.stem.split('_')[-1].replace('_', ' ').title()
            # Use relative path to chart from summary file
            rel_path = chart.relative_to(summary_path.parent.parent)
            charts_section += f"- {chart_name}: `{rel_path}`\n"
            
        # Add note about viewing
        charts_section += "\nView these charts for a visual representation of your workout metrics.\n"
        
        # Write updated summary
        with open(summary_path, 'w') as f:
            f.write(content + charts_section)
            
        print(f"Updated summary file with chart links: {summary_path}")
        return True
    
    except Exception as e:
        print(f"Error updating summary with charts: {e}")
        return False


def main():
    """Main function when run as a script"""
    if len(sys.argv) < 2:
        print("Usage: python workout_charts.py <csv_file> [output_dir]")
        return 1
        
    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    charts_dir = generate_workout_charts(csv_file, output_dir)
    
    if charts_dir:
        # Try to update summary file if it exists
        csv_path = Path(csv_file)
        summary_file = csv_path.parent / f"{csv_path.stem}_summary.md"
        if summary_file.exists():
            update_summary_with_charts(summary_file, charts_dir)
        
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

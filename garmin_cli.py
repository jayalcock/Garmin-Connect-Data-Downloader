#!/usr/bin/env python3
"""
Garmin Workout Analyzer - Unified CLI Tool

A command-line tool that brings together all Garmin data workflow functionality:
- Download activities from Garmin Connect
- Process FIT files to CSV format
- Generate visualizations and charts
- Create ChatGPT-friendly summaries
- Compare multiple workouts over time
- Download daily health statistics from Garmin Connect

Usage:
  garmin_cli.py download [--days=<days>] [--id=<id>] [--format=<format>]
  garmin_cli.py process <file> [--charts] [--summary-only]
  garmin_cli.py batch <directory> [--recursive]
  garmin_cli.py analyze <file>
  garmin_cli.py latest [--charts]
  garmin_cli.py compare [--sport=<sport>] [--days=<days>] [--directory=<directory>]
  garmin_cli.py health_stats [--date=<date>] [--days=<days>]
  
Options:
  -h --help               Show this help message
  --days=<days>           Number of days to download or analyze [default: 1]
  --id=<id>               Specific activity ID to download
  --format=<format>       Format type (ORIGINAL, TCX, GPX) [default: ORIGINAL]
  --charts                Generate visualization charts
  --summary-only          Create summary only (no CSV)
  --recursive             Search directory recursively
  --sport=<sport>         Filter by sport type (e.g., running, cycling, swimming)
  --directory=<directory> Directory to search for workout files [default: exports]
  --date=<date>           Specific date in YYYY-MM-DD format for health stats
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess
import datetime as dt


def ensure_dependency(module_name, package_name=None):
    """Check if a dependency is installed, if not suggest how to install it"""
    try:
        __import__(module_name)
    except ImportError:
        pkg_name = package_name or module_name
        print(f"Missing dependency: {module_name}")
        print(f"Please install it with: pip install {pkg_name}")
        return False
    return True


def download_command(args):
    """Download activities from Garmin Connect"""
    # Import dependencies
    try:
        # Add paths to search for modules - for Docker and local dev
        current_dir = os.path.dirname(os.path.realpath(__file__))
        # Make sure current directory is in path
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        # Add parent dir for good measure
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        
        # Print debugging info about paths
        print(f"Python path in garmin_cli: {sys.path}")
        print(f"Current directory in garmin_cli: {current_dir}")
        print(f"Files in current directory: {os.listdir(current_dir)}")
        
        # Try direct import first
        from garmin_sync import connect_to_garmin, download_activity_file, download_activities, download_today_activities
        print("Successfully imported garmin_sync with direct import")
    except ImportError as e:
        print(f"Error importing garmin_sync directly: {e}")
        try:
            # Try with absolute path
            import garmin_sync
            connect_to_garmin = garmin_sync.connect_to_garmin
            download_activity_file = garmin_sync.download_activity_file
            download_activities = garmin_sync.download_activities
            download_today_activities = garmin_sync.download_today_activities
            print("Successfully imported garmin_sync with absolute import")
        except ImportError as e:
            print(f"Could not import garmin_sync.py. Make sure it's in the same directory. Error: {e}")
            
            # Last resort - try loading the module directly from a file
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("garmin_sync", os.path.join(current_dir, "garmin_sync.py"))
                if spec and spec.loader:
                    garmin_sync = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(garmin_sync)
                    connect_to_garmin = garmin_sync.connect_to_garmin
                    download_activity_file = garmin_sync.download_activity_file
                    download_activities = garmin_sync.download_activities
                    download_today_activities = garmin_sync.download_today_activities
                    print("Successfully imported garmin_sync using direct file loading")
                else:
                    print("Failed to create module spec for garmin_sync.py")
                    return False
            except Exception as e:
                print(f"All import methods failed. Error: {e}")
                return False

    # Connect to Garmin
    client = connect_to_garmin(non_interactive=True, allow_mfa=False)
    if not client:
        print("Failed to connect to Garmin Connect")
        return False

    # Download activities based on arguments
    if args.id:
        print(f"Downloading activity {args.id} in {args.format} format...")
        return download_activity_file(client, args.id, args.format, create_chatgpt_summary=True)
    elif args.days == 1:
        print("Downloading today's activities...")
        download_today_activities(client, format_type=args.format)
        return True
    else:
        print(f"Downloading activities from the past {args.days} days...")
        days_ago = dt.datetime.now() - dt.timedelta(days=int(args.days))
        download_activities(client, start_date=days_ago, format_type=args.format)
        return True


def process_command(args):
    """Process a FIT file to CSV and optionally create summary or charts"""
    # Ensure file exists
    fit_file = Path(args.file)
    if not fit_file.exists() or not fit_file.is_file():
        print(f"Error: File not found: {fit_file}")
        return False

    if not fit_file.suffix.lower() == '.fit':
        print(f"Error: File is not a .fit file: {fit_file}")
        return False

    # Import dependencies
    if not ensure_dependency('fitparse'):
        return False
    if not ensure_dependency('pandas'):
        return False

    # Choose the appropriate converter based on arguments
    if args.summary_only:
        try:
            from utils.fit_converter import convert_and_analyze
            print(f"Processing {fit_file} (summary only)...")
            result = convert_and_analyze(fit_file, verbose=True)
            return result is not None
        except ImportError:
            print("Could not import fit_converter.py. Falling back to fit_to_csv.py...")
            try:
                from utils.fit_to_csv import fit_to_csv
                print(f"Processing {fit_file}...")
                result = fit_to_csv(fit_file, summary_only=True)
                return result is not None
            except ImportError:
                print("Could not import fit_to_csv.py.")
                return False
    else:
        try:
            from utils.fit_to_csv import fit_to_csv
            print(f"Converting {fit_file} to CSV...")
            csv_file = fit_to_csv(fit_file)
            if not csv_file:
                return False

            if args.charts or args.advanced:
                generate_charts(csv_file, advanced=args.advanced)

            return True
        except ImportError:
            print("Could not import fit_to_csv.py.")
            return False


def batch_command(args):
    """Process multiple FIT files in a directory"""
    # Ensure directory exists
    dir_path = Path(args.directory)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: Directory not found: {dir_path}")
        return False

    # Find FIT files
    pattern = '**/*.fit' if args.recursive else '*.fit'
    fit_files = list(dir_path.glob(pattern))

    if not fit_files:
        print(f"No FIT files found in {dir_path}")
        return False

    print(f"Found {len(fit_files)} FIT files to process")

    # Process each file
    success_count = 0
    for fit_file in fit_files:
        print(f"Processing {fit_file}...")
        try:
            from utils.fit_to_csv import fit_to_csv
            csv_file = fit_to_csv(fit_file)
            if csv_file:
                success_count += 1
        except ImportError:
            print("Could not import fit_to_csv.py. Skipping file.")
            continue

    print(f"Successfully processed {success_count} of {len(fit_files)} files")
    return success_count > 0


def analyze_command(args):
    """Create a detailed analysis of a FIT or CSV file"""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return False

    # Determine file type and create appropriate analysis
    if file_path.suffix.lower() == '.fit':
        print("Converting FIT file to CSV first...")
        try:
            from utils.fit_to_csv import fit_to_csv
            csv_file = fit_to_csv(file_path)
            if not csv_file:
                return False
            file_path = csv_file
        except ImportError:
            print("Could not import fit_to_csv.py.")
            return False

    if file_path.suffix.lower() == '.csv':
        try:
            from utils.create_garmin_analysis import create_chatgpt_analysis
            output_file = file_path.parent / f"{file_path.stem}_analysis.md"
            print(f"Creating detailed analysis from {file_path}...")
            analysis_file = create_chatgpt_analysis(file_path, output_file)
            if analysis_file:
                print(f"Analysis created: {analysis_file}")
                
                # Generate charts if requested
                if args.charts or args.advanced:
                    generate_charts(file_path, advanced=args.advanced)
                    
                # Try to open the file with the default application
                try:
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', analysis_file])
                    elif sys.platform == 'win32':  # Windows
                        os.startfile(analysis_file)
                    elif sys.platform == 'linux':  # Linux
                        subprocess.run(['xdg-open', analysis_file])
                except Exception as e:
                    print(f"Could not open the file: {e}")
                return True
        except ImportError:
            print("Could not import create_garmin_analysis.py.")

    return False


def generate_charts(csv_file, advanced=False):
    """Generate charts for a workout based on CSV data
    
    Args:
        csv_file: Path to the CSV file with workout data
        advanced: Whether to generate advanced sport-specific charts
        
    Returns:
        True if charts were generated successfully, False otherwise
    """
    try:
        # Dynamically import visualization dependencies
        import matplotlib
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
    except ImportError as e:
        print(f"Missing dependency for chart generation: {e}")
        print("Please install with: pip install matplotlib seaborn pandas")
        return False

    print(f"Generating charts for {csv_file}...")
    csv_path = Path(csv_file)
    
    # Create charts directory
    charts_dir = csv_path.parent / 'charts'
    charts_dir.mkdir(exist_ok=True)
    
    # Generate advanced charts if requested
    if advanced:
        try:
            from utils.advanced_charts import generate_advanced_charts
            advanced_charts_dir = generate_advanced_charts(csv_file)
            if advanced_charts_dir:
                print(f"Generated advanced charts in {advanced_charts_dir}")
        except ImportError as e:
            print(f"Could not import advanced_charts module: {e}")
            print("Falling back to basic chart generation")
    
    try:
        # Load CSV data
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Extract record data (time series data points)
        record_df = df[df['record_type'] == 'record'].copy()
        
        # Skip if no record data
        if record_df.empty:
            print("No detailed record data found for visualization")
            return False
        
        # Ensure timestamp is properly formatted
        if 'timestamp' in record_df.columns:
            record_df['timestamp'] = pd.to_datetime(record_df['timestamp'])
            
            # Create time axis in minutes from start
            if not record_df['timestamp'].isna().all():
                start_time = record_df['timestamp'].min()
                record_df['minutes'] = (record_df['timestamp'] - start_time).dt.total_seconds() / 60
            else:
                # If timestamps are not available, use simple indices
                record_df['minutes'] = range(len(record_df))
        
        # Generate charts based on available data
        metrics_generated = []
        
        # 1. Heart Rate Chart
        if 'heart_rate' in record_df.columns:
            plt.figure(figsize=(10, 4))
            sns.lineplot(x='minutes', y='heart_rate', data=record_df)
            plt.title('Heart Rate During Workout')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Heart Rate (bpm)')
            plt.tight_layout()
            hr_chart = charts_dir / f"{csv_path.stem}_heart_rate.png"
            plt.savefig(hr_chart)
            plt.close()
            metrics_generated.append("heart rate")
            print(f"Created heart rate chart: {hr_chart}")
        
        # 2. Speed Chart
        if 'speed' in record_df.columns:
            plt.figure(figsize=(10, 4))
            # Convert m/s to km/h
            record_df['speed_kmh'] = record_df['speed'] * 3.6
            sns.lineplot(x='minutes', y='speed_kmh', data=record_df)
            plt.title('Speed During Workout')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Speed (km/h)')
            plt.tight_layout()
            speed_chart = charts_dir / f"{csv_path.stem}_speed.png"
            plt.savefig(speed_chart)
            plt.close()
            metrics_generated.append("speed")
            print(f"Created speed chart: {speed_chart}")
            
        # 3. Elevation Chart
        if 'altitude' in record_df.columns:
            plt.figure(figsize=(10, 4))
            sns.lineplot(x='minutes', y='altitude', data=record_df)
            plt.title('Elevation Profile')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Altitude (m)')
            plt.tight_layout()
            elevation_chart = charts_dir / f"{csv_path.stem}_elevation.png"
            plt.savefig(elevation_chart)
            plt.close()
            metrics_generated.append("elevation")
            print(f"Created elevation chart: {elevation_chart}")
            
        # 4. Cadence Chart
        if 'cadence' in record_df.columns:
            plt.figure(figsize=(10, 4))
            sns.lineplot(x='minutes', y='cadence', data=record_df)
            plt.title('Cadence During Workout')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Cadence (rpm/spm)')
            plt.tight_layout()
            cadence_chart = charts_dir / f"{csv_path.stem}_cadence.png"
            plt.savefig(cadence_chart)
            plt.close()
            metrics_generated.append("cadence")
            print(f"Created cadence chart: {cadence_chart}")
            
        # 5. Power Chart (for cycling)
        if 'power' in record_df.columns:
            plt.figure(figsize=(10, 4))
            sns.lineplot(x='minutes', y='power', data=record_df)
            plt.title('Power Output')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Power (watts)')
            plt.tight_layout()
            power_chart = charts_dir / f"{csv_path.stem}_power.png"
            plt.savefig(power_chart)
            plt.close()
            metrics_generated.append("power")
            print(f"Created power chart: {power_chart}")
            
        # 6. Combined Chart (HR + Speed)
        if 'heart_rate' in record_df.columns and 'speed' in record_df.columns:
            fig, ax1 = plt.subplots(figsize=(10, 5))
            
            # Heart rate on primary y-axis
            ax1.set_xlabel('Time (minutes)')
            ax1.set_ylabel('Heart Rate (bpm)', color='tab:red')
            ax1.plot(record_df['minutes'], record_df['heart_rate'], color='tab:red')
            ax1.tick_params(axis='y', labelcolor='tab:red')
            
            # Speed on secondary y-axis
            ax2 = ax1.twinx()
            ax2.set_ylabel('Speed (km/h)', color='tab:blue')
            ax2.plot(record_df['minutes'], record_df['speed'] * 3.6, color='tab:blue')
            ax2.tick_params(axis='y', labelcolor='tab:blue')
            
            plt.title('Heart Rate and Speed')
            plt.tight_layout()
            combined_chart = charts_dir / f"{csv_path.stem}_hr_speed.png"
            plt.savefig(combined_chart)
            plt.close()
            print(f"Created combined heart rate and speed chart: {combined_chart}")
        
        # Add chart links to the workout summary file
        summary_file = csv_path.parent / f"{csv_path.stem}_summary.md"
        if summary_file.exists():
            print(f"Adding chart links to summary file: {summary_file}")
            
            # Read the existing summary
            with open(summary_file, 'r') as f:
                content = f.read()
            
            # Add image links section if we generated any charts
            if metrics_generated:
                charts_section = "\n## Workout Visualizations\n\n"
                charts_section += "The following charts are available in the 'charts' folder:\n\n"
                
                for metric in metrics_generated:
                    charts_section += f"- {metric.title()} chart\n"
                
                # Write the updated content
                with open(summary_file, 'w') as f:
                    f.write(content + charts_section)
        
        return True
    
    except Exception as e:
        print(f"Error generating charts: {e}")
        import traceback
        traceback.print_exc()
        return False


def latest_command(args):
    """Process the most recent FIT file"""
    # Get the script directory
    script_dir = Path(__file__).parent
    export_dir = script_dir / "exports" / "activities"
    
    if not export_dir.exists():
        print(f"Error: Export directory not found: {export_dir}")
        return False
    
    # Find the most recent FIT file
    fit_files = list(export_dir.glob("*.fit"))
    if not fit_files:
        print("No FIT files found in exports/activities")
        return False
    
    # Sort by modification time (most recent first)
    latest_fit = max(fit_files, key=os.path.getmtime)
    print(f"Found most recent FIT file: {latest_fit}")
    
    # Process it
    args.file = latest_fit
    result = process_command(args)
    
    # Generate charts if requested
    if result and (args.charts or args.advanced):
        csv_file = export_dir.parent / "chatgpt_ready" / f"{latest_fit.stem}.csv"
        if csv_file.exists():
            generate_charts(csv_file, advanced=args.advanced)
    
    return result


def compare_command(args):
    """Compare multiple workouts and analyze trends"""
    try:
        from utils.workout_comparison import find_workout_files, compare_workouts
    except ImportError:
        print("Could not import workout_comparison module")
        return False

    # Default directory if not specified
    directory = args.directory
    if not directory:
        # Try to find the exports directory
        script_dir = Path(__file__).parent
        directory = script_dir / "exports"
        
        if not directory.exists():
            print(f"Default directory not found: {directory}")
            print("Please specify directory with --directory=<path>")
            return False
    
    print(f"Looking for workout files in {directory}...")
    files = find_workout_files(directory, args.sport, args.days)
    
    if not files:
        print(f"No workout files found matching criteria.")
        if args.sport:
            print(f"Try using a different sport type or increasing the days.")
        return False
    
    print(f"Found {len(files)} workout files to analyze")
    
    # Create comparison directory
    output_dir = Path(directory) / "workout_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate comparison charts
    result = compare_workouts(files, output_dir)
    
    if not result:
        print("Failed to generate workout comparison")
        return False
    
    # Open the HTML report if generated
    html_report = output_dir / "workout_comparison.html"
    if html_report.exists():
        print(f"Opening workout comparison report: {html_report}")
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', html_report])
            elif sys.platform == 'win32':  # Windows
                os.startfile(html_report)
            elif sys.platform == 'linux':  # Linux
                subprocess.run(['xdg-open', html_report])
        except Exception as e:
            print(f"Could not open the report file: {e}")
            print(f"Report available at: {html_report}")
    
    return True


def health_stats_command(args):
    """Download daily health statistics from Garmin Connect
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from garmin_sync import connect_to_garmin, get_stats
    except ImportError as e:
        print(f"Error importing garmin_sync: {e}")
        print("Make sure you have the correct dependencies installed.")
        return False
    
    print("\n===== Downloading Health Statistics from Garmin Connect =====\n")
    
    # Connect to Garmin
    interactive = not args.non_interactive
    client = connect_to_garmin(non_interactive=args.non_interactive, allow_mfa=True)
    
    if not client:
        print("Failed to connect to Garmin Connect. Aborting.")
        return False
        
    # Determine the date range
    if args.date:
        try:
            from datetime import datetime, timedelta
            start_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Please use YYYY-MM-DD format.")
            return False
    else:
        # Default to yesterday if no date provided
        from datetime import date, timedelta
        start_date = date.today() - timedelta(days=1)
    
    days = max(1, args.days)
    
    print(f"Downloading health statistics for {days} day(s) starting from {start_date.isoformat()}")
    
    success = True
    for day_offset in range(days):
        # Calculate the date for this iteration
        current_date = start_date - timedelta(days=day_offset)
        date_str = current_date.isoformat()
        
        print(f"\nProcessing date: {date_str}")
        
        # Get stats for the current date
        stats = get_stats(client, date_str=date_str, export=True, interactive=interactive)
        if not stats:
            print(f"Failed to download data for {date_str}")
            success = False
            
    if success:
        print("\nHealth statistics download completed successfully.")
        print("Data has been saved to exports/garmin_stats.csv")
    else:
        print("\nHealth statistics download completed with some errors.")
    
    return success


def main():
    parser = argparse.ArgumentParser(description='Garmin Workout Analyzer - Unified CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download activities from Garmin Connect')
    download_parser.add_argument('--days', type=int, default=1, help='Number of days to download')
    download_parser.add_argument('--id', help='Specific activity ID to download')
    download_parser.add_argument('--format', default='ORIGINAL', help='Format type (ORIGINAL, TCX, GPX)')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a FIT file to CSV')
    process_parser.add_argument('file', help='FIT file to process')
    process_parser.add_argument('--charts', action='store_true', help='Generate visualization charts')
    process_parser.add_argument('--advanced', action='store_true', help='Generate advanced sport-specific charts')
    process_parser.add_argument('--summary-only', action='store_true', help='Create summary only (no CSV)')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process multiple FIT files')
    batch_parser.add_argument('directory', help='Directory containing FIT files')
    batch_parser.add_argument('--recursive', action='store_true', help='Search directory recursively')
    batch_parser.add_argument('--charts', action='store_true', help='Generate visualization charts')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Create detailed analysis of a FIT/CSV file')
    analyze_parser.add_argument('file', help='FIT or CSV file to analyze')
    analyze_parser.add_argument('--charts', action='store_true', help='Include visualization charts')
    analyze_parser.add_argument('--advanced', action='store_true', help='Generate advanced sport-specific charts')
    
    # Latest command
    latest_parser = subparsers.add_parser('latest', help='Process the most recent FIT file')
    latest_parser.add_argument('--charts', action='store_true', help='Generate visualization charts')
    latest_parser.add_argument('--advanced', action='store_true', help='Generate advanced sport-specific charts')
    
    # Compare command (new)
    compare_parser = subparsers.add_parser('compare', help='Compare multiple workouts over time')
    compare_parser.add_argument('--sport', help='Filter by sport type (running, cycling, swimming, etc.)')
    compare_parser.add_argument('--days', type=int, default=90, help='Number of past days to include [default: 90]')
    compare_parser.add_argument('--directory', help='Directory to search for workout files')
    
    # Health Stats command
    health_stats_parser = subparsers.add_parser('health_stats', help='Download daily health statistics from Garmin Connect')
    health_stats_parser.add_argument('--date', help='Specific date in YYYY-MM-DD format (defaults to yesterday)')
    health_stats_parser.add_argument('--days', type=int, default=1, help='Number of days to download (starting from date) [default: 1]')
    health_stats_parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode (no prompts)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'download':
        success = download_command(args)
    elif args.command == 'process':
        success = process_command(args)
    elif args.command == 'batch':
        success = batch_command(args)
    elif args.command == 'analyze':
        success = analyze_command(args)
    elif args.command == 'latest':
        success = latest_command(args)
    elif args.command == 'compare':
        success = compare_command(args)
    elif args.command == 'health_stats':
        success = health_stats_command(args)
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

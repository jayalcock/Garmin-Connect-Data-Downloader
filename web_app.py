#!/usr/bin/env python3
"""
Garmin Workout Analyzer - Web Interface

A web-based interface for the Garmin workout analysis tools.
This provides browser access to the functionality in garmin_cli.py.

Features:
- Download activities from Garmin Connect
- Process FIT files to CSV format
- Generate visualizations and charts
- Create ChatGPT-friendly summaries
- Compare multiple workouts over time
"""

import os
import sys
import json
import time
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, redirect, url_for, 
                   send_from_directory, send_file, flash, jsonify, abort)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import NumberRange, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'garmin-workout-analyzer-secret-key')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure export directories exist
os.makedirs('exports/activities', exist_ok=True)
os.makedirs('exports/chatgpt_ready', exist_ok=True)

# Create a directory for storing results
RESULTS_DIR = Path('web_results')
RESULTS_DIR.mkdir(exist_ok=True)

# Import garmin_cli functionality
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
    print(f"Python path: {sys.path}")
    print(f"Current directory: {current_dir}")
    print(f"Files in current directory: {os.listdir(current_dir)}")
    
    # First try direct import
    from garmin_cli import (
        download_command, process_command, analyze_command
    )
    print("Successfully imported garmin_cli with direct import")
except ImportError as e:
    print(f"Error importing garmin_cli directly: {e}")
    try:
        # Try with absolute import
        import garmin_cli
        download_command = garmin_cli.download_command
        process_command = garmin_cli.process_command
        analyze_command = garmin_cli.analyze_command
        latest_command = garmin_cli.latest_command
        compare_command = garmin_cli.compare_command
        print("Successfully imported garmin_cli with absolute import")
    except ImportError as e2:
        print(f"Error with absolute import: {e2}")
        sys.exit(1)

# Forms
class DownloadForm(FlaskForm):
    days = IntegerField('Number of days to download', validators=[NumberRange(min=1, max=365)], default=1)
    activity_id = StringField('Activity ID (optional)', validators=[Optional()])
    format_type = SelectField('Format Type', 
                              choices=[('ORIGINAL', 'ORIGINAL (FIT)'), 
                                       ('TCX', 'TCX'), 
                                       ('GPX', 'GPX'),
                                       ('CSV', 'CSV (Converted from FIT)')],
                              default='ORIGINAL')
    submit = SubmitField('Download Activities')

class ProcessForm(FlaskForm):
    fit_file = FileField('FIT File', validators=[
        FileRequired(),
        FileAllowed(['fit'], 'FIT files only!')
    ])
    generate_charts = BooleanField('Generate Charts', default=True)
    advanced_charts = BooleanField('Generate Advanced Charts', default=False)
    summary_only = BooleanField('Summary Only (No CSV)', default=False)
    submit = SubmitField('Process File')

class AnalyzeForm(FlaskForm):
    fit_file = FileField('FIT/CSV File', validators=[
        FileRequired(),
        FileAllowed(['fit', 'csv'], 'FIT or CSV files only!')
    ])
    generate_charts = BooleanField('Generate Charts', default=True)
    advanced_charts = BooleanField('Generate Advanced Charts', default=False)
    submit = SubmitField('Analyze File')

class CompareForm(FlaskForm):
    sport_type = SelectField('Sport Type', 
                           choices=[('', 'All Sports'),
                                    ('running', 'Running'),
                                    ('cycling', 'Cycling'), 
                                    ('swimming', 'Swimming')],
                           default='')
    days = IntegerField('Days to Include', validators=[NumberRange(min=1, max=365)], default=90)
    submit = SubmitField('Compare Workouts')

class HealthStatsForm(FlaskForm):
    days = IntegerField('Number of days to download', validators=[NumberRange(min=1, max=90)], default=1)
    start_date = StringField('Start Date (YYYY-MM-DD)', 
                             validators=[Optional()],
                             description="Leave blank to use today's date")
    submit = SubmitField('Download Health Stats')

class CommandArgs:
    """Simple class to mimic argparse namespace for CLI functions"""
    def __init__(self):
        self.days = None
        self.id = None
        self.format = None
        self.file = None
        self.charts = None
        self.advanced = None
        self.summary_only = None
        self.sport = None
        self.directory = None
        self.date = None
        self.non_interactive = None

@app.route('/')
def home():
    """Home page with links to all functionality"""
    return render_template('index.html')

@app.route('/download', methods=['GET', 'POST'])
def download():
    """Download activities from Garmin Connect"""
    form = DownloadForm()
    
    if form.validate_on_submit():
        # Convert form data to CLI arguments
        args = CommandArgs()
        args.days = form.days.data
        args.id = form.activity_id.data if form.activity_id.data else None
        args.format = form.format_type.data
        
        # Create a unique results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = RESULTS_DIR / f"download_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Redirect stdout/stderr to capture output
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
        
        try:
            success = download_command(args)
            
            # Reset stdout/stderr
            sys.stdout.flush()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Read captured output
            output.seek(0)
            command_output = output.read()
            output.close()
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w", encoding="utf-8") as f:
                f.write(command_output)
            
            # Copy downloaded files to result directory if successful
            if success:
                activities_dir = Path("exports/activities")
                if activities_dir.exists():
                    # Copy only the newly downloaded files (most recent based on timestamp)
                    dest_activities = result_dir / "activities"
                    dest_activities.mkdir(exist_ok=True)
                    
                    # Find the most recent files (created in the past days+1)
                    now = time.time()
                    for file in activities_dir.glob("*"):
                        # If file was created in the past days+1 days
                        if os.path.getmtime(file) > now - ((form.days.data + 1) * 86400):
                            shutil.copy2(file, dest_activities)
            
            return render_template(
                'download_result.html',
                success=success,
                output=command_output,
                result_dir=str(result_dir.relative_to(RESULTS_DIR)),
                timestamp=timestamp
            )
        except (OSError, RuntimeError) as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('download.html', form=form)

@app.route('/process', methods=['GET', 'POST'])
def process():
    """Process a FIT file to CSV with optional charts"""
    form = ProcessForm()
    
    if form.validate_on_submit():
        # Save the uploaded file
        fit_file = form.fit_file.data
        filename = secure_filename(fit_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        fit_file.save(file_path)
        
        # Convert form data to CLI arguments
        args = CommandArgs()
        args.file = file_path
        args.charts = form.generate_charts.data
        args.advanced = form.advanced_charts.data
        args.summary_only = form.summary_only.data
        
        # Create a unique results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = RESULTS_DIR / f"process_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Redirect stdout/stderr to capture output
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
        
        try:
            success = process_command(args)
            
            # Reset stdout/stderr
            sys.stdout.flush()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Read captured output
            output.seek(0)
            command_output = output.read()
            output.close()
            
            # Initialize content variables
            summary_content = None
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w", encoding="utf-8") as f:
                f.write(command_output)
            
            # Copy processed files to result directory
            if success:
                basename = os.path.splitext(filename)[0]
                chatgpt_dir = Path("exports/chatgpt_ready")
                
                # Copy CSV file if it exists
                csv_file = chatgpt_dir / f"{basename}.csv"
                if csv_file.exists():
                    shutil.copy2(csv_file, result_dir)
                
                # Copy summary file if it exists
                summary_file = chatgpt_dir / f"{basename}_summary.md"
                if summary_file.exists():
                    shutil.copy2(summary_file, result_dir)
                    # Read summary content for display
                    with open(summary_file, "r", encoding="utf-8") as f:
                        summary_content = f.read()
                
                # Copy charts if they exist
                charts_dir = chatgpt_dir / "charts"
                if charts_dir.exists():
                    dest_charts = result_dir / "charts"
                    dest_charts.mkdir(exist_ok=True)
                    
                    for chart_file in charts_dir.glob(f"{basename}*.png"):
                        shutil.copy2(chart_file, dest_charts)
                
                advanced_charts_dir = chatgpt_dir / "advanced_charts"
                if advanced_charts_dir.exists():
                    dest_advanced = result_dir / "advanced_charts"
                    dest_advanced.mkdir(exist_ok=True)
                    
                    for chart_file in advanced_charts_dir.glob("*.png"):
                        shutil.copy2(chart_file, dest_advanced)
                    
                    # Copy HTML dashboard if it exists
                    dashboard_file = advanced_charts_dir / f"{basename}_dashboard.html"
                    if dashboard_file.exists():
                        shutil.copy2(dashboard_file, dest_advanced)
            
            return render_template(
                'process_result.html',
                success=success,
                output=command_output,
                result_dir=str(result_dir.relative_to(RESULTS_DIR)),
                summary_content=summary_content,
                timestamp=timestamp
            )
        except (OSError, RuntimeError) as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('process.html', form=form)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Analyze a FIT/CSV file with detailed metrics"""
    form = AnalyzeForm()
    analysis_content = None  # Always initialize
    
    if form.validate_on_submit():
        # Save the uploaded file
        uploaded_file = form.fit_file.data
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)
        
        # Convert form data to CLI arguments
        args = CommandArgs()
        args.file = file_path
        args.charts = form.generate_charts.data
        args.advanced = form.advanced_charts.data
        
        # Create a unique results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = RESULTS_DIR / f"analyze_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Redirect stdout/stderr to capture output
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
        
        try:
            success = analyze_command(args)
            
            # Reset stdout/stderr
            sys.stdout.flush()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Read captured output
            output.seek(0)
            command_output = output.read()
            output.close()
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w", encoding="utf-8") as f:
                f.write(command_output)
            
            # Copy processed files to result directory
            if success:
                basename = os.path.splitext(filename)[0]
                chatgpt_dir = Path("exports/chatgpt_ready")
                
                # Copy analysis file if it exists
                analysis_file = chatgpt_dir / f"{basename}_analysis.md"
                if analysis_file.exists():
                    shutil.copy2(analysis_file, result_dir)
                    
                    # Read analysis content for display
                    with open(analysis_file, "r", encoding="utf-8") as f:
                        analysis_content = f.read()
                
                # Copy charts if they exist
                charts_dir = chatgpt_dir / "charts"
                if charts_dir.exists():
                    dest_charts = result_dir / "charts"
                    dest_charts.mkdir(exist_ok=True)
                    
                    for chart_file in charts_dir.glob(f"{basename}*.png"):
                        shutil.copy2(chart_file, dest_charts)
                
                # Copy advanced charts if they exist
                advanced_charts_dir = chatgpt_dir / "advanced_charts"
                if advanced_charts_dir.exists():
                    dest_advanced = result_dir / "advanced_charts"
                    dest_advanced.mkdir(exist_ok=True)
                    
                    for chart_file in advanced_charts_dir.glob("*.png"):
                        shutil.copy2(chart_file, dest_advanced)
            
            return render_template(
                'analyze_result.html',
                success=success,
                output=command_output,
                result_dir=str(result_dir.relative_to(RESULTS_DIR)),
                analysis_content=analysis_content,
                timestamp=timestamp
            )
        except (OSError, RuntimeError) as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('analyze.html', form=form)

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """Stub page for compare functionality."""
    return render_template('compare.html')

# Comment out incomplete routes to avoid syntax errors
# @app.route('/compare', methods=['GET', 'POST'])
# def compare():
#     pass
#
# @app.route('/compare_result/<result_id>')
# def compare_result(result_id):
#     pass
#
# @app.route('/latest', methods=['GET'])
# def latest():
#     pass

@app.route('/latest', methods=['GET'])
def latest():
    """Stub page for latest functionality."""
    return render_template('latest.html')

@app.route('/health_stats', methods=['GET', 'POST'])
def health_stats():
    """Download daily health statistics from Garmin Connect"""
    form = HealthStatsForm()
    
    if form.validate_on_submit():
        # Convert form data to CLI arguments
        args = CommandArgs()
        args.days = form.days.data
        args.date = form.start_date.data if form.start_date.data else None
        args.non_interactive = True
        
        # Create a unique results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = RESULTS_DIR / f"health_stats_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Redirect stdout/stderr to capture output
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
        
        try:
            # Import health_stats_command from garmin_cli.py
            try:
                from garmin_cli import health_stats_command
                success = health_stats_command(args)
            except ImportError:
                from garmin_sync import connect_to_garmin, get_stats
                
                # Connect to Garmin
                client = connect_to_garmin(non_interactive=True, allow_mfa=False)
                
                if not client:
                    success = False
                else:
                    # Determine the date range
                    if args.date:
                        try:
                            start_date = datetime.strptime(args.date, '%Y-%m-%d').date()
                        except ValueError:
                            start_date = datetime.now().date() - timedelta(days=1)
                    else:
                        # Default to today if no date provided
                        start_date = datetime.now().date()
                    
                    days = max(1, args.days)
                    success = True
                    
                    for day_offset in range(days):
                        # Calculate the date for this iteration
                        current_date = start_date - timedelta(days=day_offset)
                        date_str = current_date.isoformat()
                        
                        # Get stats for the current date
                        stats = get_stats(client, date_str=date_str, export=True, interactive=False)
                        if not stats:
                            success = False
            
            # Reset stdout/stderr
            sys.stdout.flush()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Read captured output
            output.seek(0)
            command_output = output.read()
            output.close()
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w", encoding="utf-8") as f:
                f.write(command_output)
            
            # Copy csv files to result directory if successful
            if success:
                csv_file = Path("exports/garmin_stats.csv")
                if csv_file.exists():
                    # Copy the main stats file
                    shutil.copy2(csv_file, result_dir / "garmin_stats.csv")
                    
                    # Also copy any archive files created
                    archive_dir = Path("exports/archive")
                    if archive_dir.exists():
                        result_archive_dir = result_dir / "archive"
                        result_archive_dir.mkdir(exist_ok=True)
                        
                        # Find only the recently created files based on timestamp
                        # We'll assume files created in the last hour are from this operation
                        current_time = time.time()
                        one_hour_ago = current_time - 3600
                        
                        for archive_file in archive_dir.glob("garmin_stats_*.csv"):
                            if os.path.getmtime(archive_file) > one_hour_ago:
                                shutil.copy2(archive_file, result_archive_dir / archive_file.name)
                
                # Copy JSON files (raw health data) to result directory
                exports_dir = Path("exports")
                if exports_dir.exists():
                    # Copy recently created JSON files
                    current_time = time.time()
                    one_hour_ago = current_time - 3600
                    
                    for json_file in exports_dir.glob("garmin_stats_*_raw.json"):
                        if os.path.getmtime(json_file) > one_hour_ago:
                            shutil.copy2(json_file, result_dir / json_file.name)
                
                # Read the most recent rows of the CSV for display
                csv_preview = None
                if (result_dir / "garmin_stats.csv").exists():
                    try:
                        import pandas as pd
                        # Read the entire CSV file
                        df = pd.read_csv(result_dir / "garmin_stats.csv")
                        
                        # Sort by date to ensure proper chronological order
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.sort_values('date', ascending=False)  # Most recent first
                        
                        # Take the most recent 10 rows
                        df_preview = df.head(10)
                        
                        preview_html = df_preview.to_html(classes="table table-striped table-bordered table-sm", index=False)
                        csv_preview = {
                            'html': preview_html,
                            'rows': len(df_preview),
                            'columns': len(df_preview.columns),
                            'total_rows': len(df)
                        }
                    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
                        pass
                
                return render_template(
                    'health_stats_result.html',
                    result_id=timestamp,
                    success=success,
                    output=command_output,
                    days=args.days,
                    start_date=args.date if args.date else datetime.now().date().isoformat(),
                    csv_preview=csv_preview
                )
            
            flash("Failed to download health statistics. See output for details.", "danger")
            return render_template(
                'health_stats_result.html',
                result_id=timestamp,
                success=False,
                output=command_output,
                error="Failed to download health statistics."
            )
            
        except Exception as e:
            # Reset stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            flash(f"Error: {str(e)}", "danger")
            return render_template(
                'health_stats_result.html',
                result_id=timestamp,
                success=False,
                output=str(e),
                error="An error occurred while downloading health statistics."
            )
    
    return render_template('health_stats.html', form=form)


@app.route('/results')
def results():
    """View all result directories"""
    result_list = []
    for result_dir in sorted(RESULTS_DIR.glob('*'), key=os.path.getctime, reverse=True):
        if result_dir.is_dir():
            # Get command type and timestamp
            dir_name = result_dir.name
            parts = dir_name.split('_')
            
            if len(parts) >= 2:
                command = parts[0]
                timestamp = '_'.join(parts[1:])
                
                # Create result object that matches template expectations
                result_list.append({
                    'id': dir_name,  # Use full directory name as ID
                    'dir': str(result_dir.name),
                    'command': command,
                    'timestamp': timestamp,
                    'mtime': os.path.getmtime(result_dir),
                    'created_at': datetime.fromtimestamp(os.path.getmtime(result_dir)).strftime("%Y-%m-%d %H:%M:%S"),
                    'title': f"{command.title()} - {timestamp}",
                    'type': command,
                    'type_color': 'primary' if command == 'health_stats' else 'success' if command == 'download' else 'info',
                    'result_type': 'Health Stats' if command == 'health_stats' else command.title()
                })
    
    return render_template('results.html', results=result_list)

@app.route('/results/<path:result_dir>')
def view_result(result_dir):
    """View a specific result directory"""
    full_path = RESULTS_DIR / result_dir
    
    if not full_path.exists() or not full_path.is_dir():
        abort(404)
    
    # Get list of files in the directory
    files = []
    charts = []
    summary_file = None
    analysis_file = None
    output_file = None
    html_report = None
    
    # Track if we have CSV and FIT files (including in subdirectories)
    has_csv_files = False
    has_fit_files = False
    
    for file in full_path.glob('*'):
        if file.is_file():
            if file.suffix == '.md':
                if 'summary' in file.name:
                    summary_file = file.name
                elif 'analysis' in file.name:
                    analysis_file = file.name
            elif file.name == 'output.txt':
                output_file = file.name
            elif file.suffix == '.html':
                html_report = file.name
            elif file.suffix == '.png':
                charts.append(file.name)
            elif file.suffix == '.csv':
                has_csv_files = True
                files.append(file.name)
            elif file.suffix == '.fit':
                has_fit_files = True
                files.append(file.name)
            else:
                files.append(file.name)
    
    # Check for subdirectories with charts and data files
    chart_dirs = {}
    for subdir in full_path.glob('*'):
        if subdir.is_dir():
            subdir_charts = [f.name for f in subdir.glob('*.png')]
            if subdir_charts:
                chart_dirs[subdir.name] = subdir_charts
            
            # Check for CSV and FIT files in subdirectories
            if not has_csv_files:
                has_csv_files = any(subdir.glob('*.csv'))
            if not has_fit_files:
                has_fit_files = any(subdir.glob('*.fit'))
    
    # Read content of markdown files if they exist
    summary_content = None
    if summary_file:
        with open(full_path / summary_file, 'r', encoding="utf-8") as f:
            summary_content = f.read()
    
    analysis_content = None
    if analysis_file:
        with open(full_path / analysis_file, 'r', encoding="utf-8") as f:
            analysis_content = f.read()
    
    output_content = None
    if output_file:
        with open(full_path / output_file, 'r', encoding="utf-8") as f:
            output_content = f.read()
    
    # Create a result object that matches the template expectations
    result = {
        'id': result_dir,
        'title': f"Result: {result_dir}",
        'created_at': datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S"),
        'type': result_dir.split('_')[0] if '_' in result_dir else 'unknown',
        'type_color': 'primary',
        'result_type': 'Analysis' if analysis_file else ('Processing' if files else 'Data'),
        'metadata': None,
        'files': {
            'csv': has_csv_files,
            'fit': has_fit_files,
            'summary': summary_file is not None,
            'analysis': analysis_file is not None,
            'chatgpt': any('chatgpt' in f for f in files)
        }
    }
    
    return render_template(
        'view_result.html',
        result=result,
        result_dir=result_dir,
        files=files,
        charts=charts,
        chart_dirs=chart_dirs,
        summary_file=summary_file,
        summary_content=summary_content,
        analysis_file=analysis_file,
        analysis_content=analysis_content,
        output_file=output_file,
        output_content=output_content,
        html_report=html_report
    )

@app.route('/results/<path:result_dir>/<path:filename>')
def result_file(result_dir, filename):
    """Serve files from result directories"""
    return send_from_directory(RESULTS_DIR / result_dir, filename)

@app.route('/results/<path:result_dir>/<path:subdir>/<path:filename>')
def result_subdir_file(result_dir, subdir, filename):
    """Serve files from result subdirectories"""
    return send_from_directory(RESULTS_DIR / result_dir / subdir, filename)

@app.route('/download_result/<result_id>/<file_type>')
def download_result(result_id, file_type):
    """Download specific file types from result directories"""
    # Find the result directory that matches the result_id
    # The result_id is typically a timestamp like "20250530_123456"
    # and the directory name is like "health_stats_20250530_123456"
    
    result_dir = None
    for potential_dir in RESULTS_DIR.glob(f"*{result_id}"):
        if potential_dir.is_dir():
            result_dir = potential_dir
            break
    
    if not result_dir:
        # Try exact match
        result_dir = RESULTS_DIR / result_id
        if not result_dir.exists():
            abort(404)
    
    # Map file_type to actual filename
    if file_type == 'csv':
        # Look for CSV files in the result directory
        csv_files = list(result_dir.glob("*.csv"))
        if csv_files:
            # Filter out summary files and prefer full CSV files
            full_csv_files = [f for f in csv_files if '_summary.csv' not in f.name]
            if full_csv_files:
                # Return the most recently modified full CSV file
                most_recent_csv = max(full_csv_files, key=lambda f: f.stat().st_mtime)
                return send_from_directory(result_dir, most_recent_csv.name)
            else:
                # Fallback to any CSV file if no full CSV found
                most_recent_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
                return send_from_directory(result_dir, most_recent_csv.name)
        # Also check for garmin_stats.csv specifically
        if (result_dir / "garmin_stats.csv").exists():
            return send_from_directory(result_dir, "garmin_stats.csv")
        # Check subdirectories for CSV files
        for subdir in result_dir.glob("*"):
            if subdir.is_dir():
                csv_files = list(subdir.glob("*.csv"))
                if csv_files:
                    # Filter out summary files and prefer full CSV files
                    full_csv_files = [f for f in csv_files if '_summary.csv' not in f.name]
                    if full_csv_files:
                        # Return the most recently modified full CSV file from subdirectory
                        most_recent_csv = max(full_csv_files, key=lambda f: f.stat().st_mtime)
                        return send_from_directory(subdir, most_recent_csv.name)
                    else:
                        # Fallback to any CSV file if no full CSV found
                        most_recent_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
                        return send_from_directory(subdir, most_recent_csv.name)
    
    elif file_type == 'fit':
        # Look for FIT files
        fit_files = list(result_dir.glob("*.fit"))
        if fit_files:
            return send_from_directory(result_dir, fit_files[0].name)
        # Check subdirectories for FIT files
        for subdir in result_dir.glob("*"):
            if subdir.is_dir():
                fit_files = list(subdir.glob("*.fit"))
                if fit_files:
                    return send_from_directory(subdir, fit_files[0].name)
    
    elif file_type == 'summary':
        # Look for summary markdown files
        summary_files = list(result_dir.glob("*_summary.md"))
        if summary_files:
            return send_from_directory(result_dir, summary_files[0].name)
    
    elif file_type == 'analysis':
        # Look for analysis markdown files
        analysis_files = list(result_dir.glob("*_analysis.md"))
        if analysis_files:
            return send_from_directory(result_dir, analysis_files[0].name)
    
    elif file_type == 'chatgpt':
        # Look for ChatGPT-formatted files
        chatgpt_files = list(result_dir.glob("*_chatgpt.md"))
        if chatgpt_files:
            return send_from_directory(result_dir, chatgpt_files[0].name)
    
    elif file_type == 'archive':
        # Look for archive directory or zip files
        archive_dir = result_dir / "archive"
        if archive_dir.exists():
            # Create a zip file of the archive directory on-the-fly
            import zipfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    for file_path in archive_dir.rglob('*'):
                        if file_path.is_file():
                            zip_file.write(file_path, file_path.relative_to(archive_dir))
                
                return send_from_directory(
                    os.path.dirname(tmp_file.name), 
                    os.path.basename(tmp_file.name),
                    as_attachment=True,
                    download_name=f"garmin_archive_{result_id}.zip"
                )
    
    # If no matching file found
    abort(404)

@app.route('/delete_result/<result_id>')
def delete_result(result_id):
    """Delete a result directory"""
    # Find the result directory that matches the result_id
    result_dir = None
    for potential_dir in RESULTS_DIR.glob(f"*{result_id}"):
        if potential_dir.is_dir():
            result_dir = potential_dir
            break
    
    if not result_dir:
        # Try exact match
        result_dir = RESULTS_DIR / result_id
        if not result_dir.exists():
            abort(404)
    
    try:
        # Remove the entire result directory
        shutil.rmtree(result_dir)
        flash(f"Result {result_id} has been deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting result: {str(e)}", "danger")
    
    return redirect(url_for('results'))

@app.route('/garmin-login', methods=['POST'])
def garmin_login():
    """Handle Garmin login via AJAX"""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Missing username or password'})
    
    username = data['username']
    password = data['password']
    
    # Save credentials to temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        json.dump({'username': username, 'password': password}, f)
    
    # TODO: Implement proper Garmin login logic
    # (Not implemented yet. Remove this warning when implemented.)
    
    return jsonify({'success': True, 'message': 'Login successful'})

@app.route('/download_json/<result_id>')
def download_json(result_id):
    """Download JSON files for a health stats result"""
    result_dir = RESULTS_DIR / f"health_stats_{result_id}"
    
    if not result_dir.exists():
        flash("Result not found", "error")
        return redirect(url_for('health_stats'))
    
    # Check if there are any JSON files to download
    json_files = list(result_dir.glob("*.json"))
    archive_json_files = []
    
    # Also check archive directory
    archive_dir = result_dir / "archive"
    if archive_dir.exists():
        archive_json_files = list(archive_dir.glob("*.json"))
    
    all_json_files = json_files + archive_json_files
    
    if not all_json_files:
        flash("No JSON files found for this result", "error")
        return redirect(url_for('health_stats_result', result_id=result_id))
    
    if len(all_json_files) == 1:
        # Single file, download directly
        json_file = all_json_files[0]
        return send_file(
            json_file,
            as_attachment=True,
            download_name=json_file.name,
            mimetype='application/json'
        )
    else:
        # Multiple files, create a zip
        import zipfile
        
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zipf:
                for json_file in all_json_files:
                    # Add file to zip with a clean name
                    arcname = json_file.name
                    if json_file.parent.name == "archive":
                        arcname = f"archive/{json_file.name}"
                    zipf.write(json_file, arcname)
            
            # Send the zip file
            return send_file(
                tmp_zip.name,
                as_attachment=True,
                download_name=f"health_stats_{result_id}_json.zip",
                mimetype='application/zip'
            )


@app.route('/download_single_json/<result_id>/<filename>')
def download_single_json(result_id, filename):
    """Download a specific JSON file from a health stats result"""
    result_dir = RESULTS_DIR / f"health_stats_{result_id}"
    
    if not result_dir.exists():
        flash("Result not found", "error")
        return redirect(url_for('health_stats'))
    
    # Look for the file in the main directory and archive
    json_file = result_dir / filename
    if not json_file.exists():
        json_file = result_dir / "archive" / filename
    
    if not json_file.exists():
        flash("JSON file not found", "error")
        return redirect(url_for('health_stats_result', result_id=result_id))
    
    return send_file(
        json_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

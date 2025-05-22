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
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import (Flask, render_template, request, redirect, url_for, 
                   send_from_directory, flash, jsonify, abort)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

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
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from garmin_cli import (
        download_command, process_command, analyze_command, latest_command, compare_command
    )
except ImportError as e:
    print(f"Error importing garmin_cli: {e}")
    sys.exit(1)

# Forms
class DownloadForm(FlaskForm):
    days = IntegerField('Number of days to download', validators=[NumberRange(min=1, max=365)], default=1)
    activity_id = StringField('Activity ID (optional)', validators=[Optional()])
    format_type = SelectField('Format Type', 
                              choices=[('ORIGINAL', 'ORIGINAL (FIT)'), 
                                       ('TCX', 'TCX'), 
                                       ('GPX', 'GPX')],
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

class CommandArgs:
    """Simple class to mimic argparse namespace for CLI functions"""
    pass

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
            with open(result_dir / "output.txt", "w") as f:
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
        except Exception as e:
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
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w") as f:
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
                    with open(summary_file, "r") as f:
                        summary_content = f.read()
                else:
                    summary_content = None
                
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
                summary_content=summary_content if success and 'summary_content' in locals() else None,
                timestamp=timestamp
            )
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('process.html', form=form)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Analyze a FIT/CSV file with detailed metrics"""
    form = AnalyzeForm()
    
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
            with open(result_dir / "output.txt", "w") as f:
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
                    with open(analysis_file, "r") as f:
                        analysis_content = f.read()
                else:
                    analysis_content = None
                
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
                analysis_content=analysis_content if success and 'analysis_content' in locals() else None,
                timestamp=timestamp
            )
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('analyze.html', form=form)

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """Compare multiple workouts over time"""
    form = CompareForm()
    
    if form.validate_on_submit():
        # Convert form data to CLI arguments
        args = CommandArgs()
        args.sport = form.sport_type.data if form.sport_type.data else None
        args.days = form.days.data
        args.directory = "exports"
        
        # Create a unique results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = RESULTS_DIR / f"compare_{timestamp}"
        result_dir.mkdir(exist_ok=True)
        
        # Redirect stdout/stderr to capture output
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
        
        try:
            success = compare_command(args)
            
            # Reset stdout/stderr
            sys.stdout.flush()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Read captured output
            output.seek(0)
            command_output = output.read()
            output.close()
            
            # Save output to result directory
            with open(result_dir / "output.txt", "w") as f:
                f.write(command_output)
            
            # Copy comparison files to result directory
            if success:
                comparison_dir = Path("exports/workout_comparison")
                if comparison_dir.exists():
                    # Copy HTML report
                    html_report = comparison_dir / "workout_comparison.html"
                    if html_report.exists():
                        shutil.copy2(html_report, result_dir)
                    
                    # Copy all chart images
                    for chart_file in comparison_dir.glob("*.png"):
                        shutil.copy2(chart_file, result_dir)
            
            return render_template(
                'compare_result.html',
                success=success,
                output=command_output,
                result_dir=str(result_dir.relative_to(RESULTS_DIR)),
                timestamp=timestamp
            )
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output.close()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template('compare.html', form=form)

@app.route('/latest', methods=['GET'])
def latest():
    """Process the most recent FIT file"""
    # Get query parameters
    charts = request.args.get('charts', 'true').lower() == 'true'
    advanced = request.args.get('advanced', 'false').lower() == 'true'
    
    # Convert to CLI arguments
    args = CommandArgs()
    args.charts = charts
    args.advanced = advanced
    
    # Create a unique results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = RESULTS_DIR / f"latest_{timestamp}"
    result_dir.mkdir(exist_ok=True)
    
    # Redirect stdout/stderr to capture output
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = output = tempfile.NamedTemporaryFile(mode='w+')
    
    try:
        success = latest_command(args)
        
        # Reset stdout/stderr
        sys.stdout.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Read captured output
        output.seek(0)
        command_output = output.read()
        output.close()
        
        # Save output to result directory
        with open(result_dir / "output.txt", "w") as f:
            f.write(command_output)
        
        # Copy processed files to result directory
        if success:
            chatgpt_dir = Path("exports/chatgpt_ready")
            
            # Find the latest CSV file
            csv_files = list(chatgpt_dir.glob("*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=os.path.getmtime)
                basename = latest_csv.stem
                
                # Copy CSV file
                shutil.copy2(latest_csv, result_dir)
                
                # Copy summary file if it exists
                summary_file = chatgpt_dir / f"{basename}_summary.md"
                if summary_file.exists():
                    shutil.copy2(summary_file, result_dir)
                    
                    # Read summary content for display
                    with open(summary_file, "r") as f:
                        summary_content = f.read()
                else:
                    summary_content = None
                
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
            'latest_result.html',
            success=success,
            output=command_output,
            result_dir=str(result_dir.relative_to(RESULTS_DIR)),
            summary_content=summary_content if success and 'summary_content' in locals() else None,
            timestamp=timestamp
        )
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        output.close()
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('home'))

@app.route('/results')
def results():
    """View all result directories"""
    results = []
    for result_dir in sorted(RESULTS_DIR.glob('*'), key=os.path.getctime, reverse=True):
        if result_dir.is_dir():
            # Get command type and timestamp
            dir_name = result_dir.name
            parts = dir_name.split('_')
            
            if len(parts) >= 2:
                command = parts[0]
                timestamp = '_'.join(parts[1:])
                
                results.append({
                    'dir': str(result_dir.name),
                    'command': command,
                    'timestamp': timestamp,
                    'mtime': os.path.getmtime(result_dir)
                })
    
    return render_template('results.html', results=results)

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
            else:
                files.append(file.name)
    
    # Check for subdirectories with charts
    chart_dirs = {}
    for subdir in full_path.glob('*'):
        if subdir.is_dir():
            subdir_charts = [f.name for f in subdir.glob('*.png')]
            if subdir_charts:
                chart_dirs[subdir.name] = subdir_charts
    
    # Read content of markdown files if they exist
    summary_content = None
    if summary_file:
        with open(full_path / summary_file, 'r') as f:
            summary_content = f.read()
    
    analysis_content = None
    if analysis_file:
        with open(full_path / analysis_file, 'r') as f:
            analysis_content = f.read()
    
    output_content = None
    if output_file:
        with open(full_path / output_file, 'r') as f:
            output_content = f.read()
    
    return render_template(
        'view_result.html',
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
    
    return jsonify({'success': True, 'message': 'Login successful'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

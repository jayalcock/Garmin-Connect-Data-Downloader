# Garmin Connect Data Downloader & Workout Analyzer

This project allows you to automatically download your health and fitness data from Garmin Connect, save it as CSV files, and analyze your workouts. It includes comprehensive visualization tools and ChatGPT integration for detailed workout analysis.

## Features

- **Download** activities from Garmin Connect
- **Process** FIT files to CSV format with detailed metrics
- **Visualize** workout data with charts and graphs
- **Analyze** workouts with detailed metrics and insights
- **Compare** multiple workouts over time
- **Web Interface** for easy access to all functionality
- **Docker Support** for simplified deployment

## Project Structure

```
Data download/
├── __init__.py             # Root init file for Python package
├── garmin_sync.py          # Main implementation file (core functionality)
├── daily_export.py         # Symlink to src/daily_export.py script for automated export
├── manual_export.py        # Symlink to src/manual_export.py script with MFA support
├── download_today.sh       # Shell script to download today's activities
├── analyze_workout.py      # CLI tool for analyzing workout data with ChatGPT
├── setup.py                # Python package setup file
├── garmin_cli.py           # Unified CLI tool for all functionality
├── web_app.py              # Web interface using Flask
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration for easy deployment
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates for web interface
├── static/                 # Static files (CSS, JS, images)
├── docs/                   # Documentation directory
│   ├── APP_PASSWORD_GUIDE.md    # Instructions for setting up app passwords
│   ├── BACKUP_LOCATION_CHANGES.md # Information on backup location changes
│   ├── CHANGELOG.md       # Project changelog
│   ├── OPENAI_INTEGRATION.md # Guide for using the OpenAI integration
│   └── README.md          # Additional documentation

## Web Interface

This project now includes a web interface that makes it easy to use all the functionality without needing to use the command line.

### Features

- Download activities from Garmin Connect
- Process FIT files with visualization options
- Analyze workouts for detailed metrics
- Compare multiple workouts over time
- View your latest workout
- Browse previous analysis results

## Docker Installation

### Prerequisites

- Docker and Docker Compose installed on your system

### Quick Start with Docker

1. Clone this repository:
```bash
git clone <repository-url>
cd "Garmin Apps/Data download"
```

2. Build and start the Docker container:
```bash
docker-compose up -d
```

3. Access the web interface at:
```
http://localhost:8080
```

### Configuration

Edit the `docker-compose.yml` file to change:
- Port mapping (default: 8080)
- Volume mounts for data persistence
- Environment variables

## Manual Installation

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd "Garmin Apps/Data download"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the web application:
```bash
python web_app.py
```

4. Access the web interface at:
```
http://localhost:5000
```

## Using the Web Interface

### Download Activities
1. Navigate to the Download page
2. Enter your Garmin Connect credentials (these are not stored)
3. Select the number of days to download
4. Click "Download Activities"

### Process FIT Files
1. Navigate to the Process page
2. Upload a FIT file
3. Select options for charts and summary
4. Click "Process File" 

### Analyze Workouts
1. Navigate to the Analyze page
2. Upload a FIT or CSV file
3. Select visualization options
4. Click "Analyze File"

### Compare Workouts
1. Navigate to the Compare page
2. Select sport type and date range
3. Click "Compare Workouts"

### Latest Workout
1. Navigate to the Latest page
2. Select options
3. Click "Get Latest Workout"

## CLI Usage

You can still use the command-line interface:

```bash
python garmin_cli.py download --days=7
python garmin_cli.py process my_activity.fit --charts
python garmin_cli.py analyze my_activity.fit
python garmin_cli.py compare --sport=running --days=30
python garmin_cli.py latest --charts
```

See `python garmin_cli.py --help` for more options.
├── src/                     # Source code directory
│   ├── __init__.py          # Package init file
│   ├── daily_export.py      # Daily automated export script
│   └── manual_export.py     # Manual export script with MFA support
├── utils/                   # Utility scripts and helper functions
│   ├── check_json.py        # JSON validation utility
│   ├── check_empty.py       # Check for empty data in exports
│   ├── merge_csv_files.py   # Utility to merge CSV files
│   ├── check_hrv.py         # HRV data validation utility
│   ├── dump_sleep_data.py   # Sleep data extraction utility
│   └── openai_integration.py # OpenAI integration for workout analysis
├── tests/                   # Test directory 
│   ├── __init__.py          # Test package init file
│   ├── run_tests.py         # Script to run all tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_daily_export.py # Daily export tests
│   ├── test_downloader.py   # Core downloader tests
│   ├── test_weight_data.py  # Weight data mapping tests
│   ├── test_mfa.py          # MFA testing script
│   └── test_data_retrieval.py # Data retrieval tests
├── utils/                   # Utility scripts 
│   ├── check_empty.py       # Check for empty fields in CSV exports
│   ├── check_hrv.py         # Check HRV data from Garmin Connect
│   ├── check_json.py        # Examine raw JSON data from Garmin API
│   ├── dump_sleep_data.py   # Extract detailed sleep data
│   └── merge_csv_files.py   # Merge multiple CSV exports
├── data/                    # Sample data directory
│   ├── hrv_data.json        # Sample HRV data for testing
│   └── sleep_data_2025-05-11.json # Sample sleep data for testing
├── exports/                 # Output directory for CSV and JSON exports
│   ├── archive/             # Archive of dated exports
│   └── activities/          # Directory for exported activity files
└── archive/                 # Old code archive for reference
    └── backups/             # Backup of old script versions
│       └── test_today_activities.py # Today's activities test script
├── exports/                 # Directory for exported CSV files
│   ├── garmin_stats.csv     # Main CSV file with all data (each row is a date)
│   ├── archive/             # Archive of date-specific CSV files
│   └── garmin_stats_backup_*.csv # Daily backups in Nextcloud
└── logs/                    # Directory for log files
    └── auth_status.json     # Authentication status log
├── CHANGELOG.md            # Comprehensive history of changes
```

## Usage

1. **Daily Export (Automated)**: 
   ```
   python run_daily_export.py
   ```
   This script is designed for automated runs (e.g., via cron job) and will not prompt for MFA codes.

2. **Manual Export (with MFA support)**:
   ```
   python run_manual_export.py
   ```
   Use this when you're available to enter an MFA code if required.

3. **Running Tests**:
   ```
   cd tests
   python run_tests.py
   ```
   
   To run specific tests:
   ```
   python run_tests.py downloader
   ```
   
   To run tests with real MFA:
   ```
   python run_tests.py --use-mfa
   ```

## MFA Support

The system supports Multi-Factor Authentication (MFA) but needs to be explicitly enabled for interactive sessions. For automated runs, you should use an app password as described in the APP_PASSWORD_GUIDE.md file.

## Data Storage

The application stores all your Garmin Connect health data in a single CSV file:

- The main data file is `exports/garmin_stats.csv`
- Each row represents data for a specific date
- The file is automatically backed up to Nextcloud 
- Daily backups are created in Nextcloud as `garmin_stats_backup_YYYY-MM-DD.csv` 

### Legacy Data Migration

If you have existing date-specific CSV files from previous versions, you can merge them using:

```
python merge_csv_files.py
```

This will:
1. Merge all `garmin_stats_YYYY-MM-DD.csv` files into a single `garmin_stats.csv` file
2. Archive the original date-specific files in `exports/archive/`

## Features

* Download daily health statistics (steps, heart rate, sleep, etc.)
* Export data to CSV files for analysis
* Automatically back up to Nextcloud
* Download activity files (workouts, runs, etc.) in FIT format
* Automatic download of today's activities without manual confirmation
* Set up scheduled daily exports via crontab

## File Formats

### FIT Format

All activities are now downloaded in the native FIT (Flexible and Interoperable Data Transfer) format. This is Garmin's proprietary format that contains the raw, complete data for your activities. Benefits include:

- Complete and accurate activity data with no loss of fidelity
- Direct compatibility with Garmin's ecosystem and many third-party tools
- Efficient binary format that preserves all sensor data
- Better support for advanced metrics like running dynamics, power data, etc.

### CSV Format

Daily statistics (steps, heart rate, sleep, etc.) continue to be exported in CSV format which allows for:
- Easy analysis in spreadsheets and data analysis tools
- Human-readable format for quick inspection
- Simple integration with other systems

## New Features

### Automatic Download of Today's Activities

The latest version allows you to automatically download all of today's activities with a single command:

1. Choose option 7 from the menu: "Download today's activities automatically (ORIGINAL format)"
2. All activities recorded today will be downloaded in ORIGINAL format (Garmin's native format which is a ZIP archive containing a .fit file), and the .fit file will be automatically extracted and saved for you.

This makes it easy to quickly back up your daily workout data with maximum data fidelity and compatibility with other fitness analysis tools.

### Unified CLI Tool for Workout Management

The new unified command-line interface brings together all Garmin data workflow functionality in one tool:

```bash
./garmin-cli.sh <command> [options]
```

Available commands:

1. **Download activities from Garmin Connect**
   ```bash
   ./garmin-cli.sh download [--days=<days>] [--id=<id>] [--format=<format>]
   ```

2. **Process a FIT file to CSV with visualizations**
   ```bash
   ./garmin-cli.sh process <file> [--charts] [--advanced] [--summary-only]
   ```

3. **Batch process multiple FIT files**
   ```bash
   ./garmin-cli.sh batch <directory> [--recursive] [--charts]
   ```

4. **Create detailed analysis of a workout**
   ```bash
   ./garmin-cli.sh analyze <file> [--charts] [--advanced]
   ```

5. **Process the most recent FIT file**
   ```bash
   ./garmin-cli.sh latest [--charts] [--advanced]
   ```

6. **Compare multiple workouts and visualize trends**
   ```bash
   ./garmin-cli.sh compare [--sport=<sport>] [--days=<days>] [--directory=<directory>]
   ```

The CLI tool automatically generates:
- CSV data files with all workout metrics
- ChatGPT-friendly markdown summaries
- Visualizations and charts (with `--charts` option)

All outputs are saved in the `exports/chatgpt_ready/` directory for easy access.

### Data Visualization

When using the `--charts` option with the CLI tool, the following visualizations are created:

- **Heart Rate Chart**: Shows your heart rate throughout the workout
- **Speed/Pace Chart**: Displays your speed (or pace for running)
- **Elevation Profile**: Shows elevation changes during the workout
- **Cadence Chart**: Displays your cadence (steps/minute or rpm)
- **Power Chart**: For cycling workouts with power data
- **Combined HR/Speed Chart**: Overlays heart rate and speed
- **Lap Analysis**: Compares metrics across laps

These charts are saved in a `charts/` subdirectory and linked from the workout summary.

#### Advanced Sport-Specific Visualizations

When using the `--advanced` option, specialized charts are generated based on the sport type:

**Running**:
- Pace charts with average pace overlay
- Stride length analysis and efficiency metrics
- Heart rate vs. pace relationship

**Cycling**:
- Power zone distribution charts
- Cadence vs. power efficiency analysis
- Combined terrain and performance analysis

**Swimming**:
- Lap time analysis
- SWOLF score charts (swimming efficiency)
- Stroke rate analysis

#### Workout Comparison and Trend Analysis

The comparison feature allows you to track your progress over time with visualizations of:

- Distance trends across multiple workouts
- Heart rate trends (average and maximum)
- Performance improvements (pace for running, power for cycling)
- Weekly training volume and calorie expenditure
- Sport-specific metric comparisons

To compare workouts:
```bash
./garmin-cli.sh compare --sport=running --days=90
```

This generates an HTML dashboard in the `exports/workout_comparison/` directory with interactive charts and tables showing your training progress.

### ChatGPT Integration for Workout Analysis

You can also directly analyze your workouts with ChatGPT:

```
python analyze_workout.py
```

Key capabilities:
- Configure your OpenAI API key with `--configure`
- List recent activities with `--list-activities`
- Analyze a specific activity using `--activity-id <ID>`
- Analyze activities from a specific date with `--date YYYY-MM-DD`

The analysis includes:
- Performance insights based on your metrics
- Recovery recommendations
- Training suggestions
- Comparisons to your previous workouts (when available)

All analyses are saved to `exports/analysis/` for future reference.

For detailed instructions, see [OpenAI Integration Guide](docs/OPENAI_INTEGRATION.md).

To run the automatic download directly from the command line:

```bash
cd "/Users/jay/Projects/Garmin Apps/Data download"
python3 test_today_activities.py
```

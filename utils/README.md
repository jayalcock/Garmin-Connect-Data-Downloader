# Garmin Connect Data Utilities

This directory contains utility scripts for managing and analyzing Garmin Connect data.

## Available Utilities

### Data Validation and Inspection

- **check_empty.py**: Identifies empty fields in the CSV export file
- **check_json.py**: Examines raw JSON data from Garmin Connect API
- **check_hrv.py**: Extracts and examines heart rate variability (HRV) data

### Data Processing

- **merge_csv_files.py**: Merges multiple Garmin Connect CSV export files into one
- **dump_sleep_data.py**: Extracts detailed sleep data from Garmin Connect

## Usage

All scripts should be run from the root directory of the project:

```bash
cd "/Users/jay/Projects/Garmin Apps/Data download"
python3 utils/script_name.py
```

Each script adds the parent directory to the Python path, so imports will work correctly.

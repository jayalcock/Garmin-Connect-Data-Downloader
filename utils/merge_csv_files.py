#!/usr/bin/env python3
# Script to merge existing date-specific CSV files into a single file

import os
import csv
import glob
from pathlib import Path

def merge_csv_files():
    """Merge all existing date-specific CSV files into a single file"""
    
    print("Merging existing CSV files into a single file...")
    print(f"Current directory: {os.getcwd()}")
    
    # Path to the exports directory
    exports_dir = Path(__file__).parent / "exports"
    print(f"Looking for CSV files in: {exports_dir}")
    
    # Find all existing CSV files
    csv_files = sorted(list(exports_dir.glob("garmin_stats_*.csv")))
    
    if not csv_files:
        print("No CSV files found to merge.")
        return
    
    print(f"Found {len(csv_files)} CSV files to merge.")
    
    # Create the new consolidated file
    new_file = exports_dir / "garmin_stats.csv"
    
    # First, check if any file exists and get all headers
    all_headers = set()
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    file_headers = next(reader)
                    all_headers.update(file_headers)
                except StopIteration:
                    # File is empty, skip it
                    print(f"Warning: {csv_file} is empty, skipping.")
                    continue
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue
    
    # Convert to list and ensure 'date' is the first column
    all_headers_list = list(all_headers)
    if 'date' in all_headers_list:
        all_headers_list.remove('date')
    all_headers_list = ['date'] + sorted(all_headers_list)
    
    # Create the new file and write all data
    print(f"Creating merged file: {new_file}")
    with open(new_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=all_headers_list)
        writer.writeheader()
        
        # Write data from each file
        rows_written = 0
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', newline='', encoding='utf-8') as infile:
                    reader = csv.DictReader(infile)
                    for row in reader:
                        # Create a row with all possible fields
                        clean_row = {header: row.get(header, '') for header in all_headers_list}
                        writer.writerow(clean_row)
                        rows_written += 1
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
    
    print(f"Merged {rows_written} rows of data into {new_file}")
    
    # Create backup copies of the original files
    backup_dir = exports_dir / "archive"
    backup_dir.mkdir(exist_ok=True)
    
    for csv_file in csv_files:
        try:
            backup_file = backup_dir / csv_file.name
            if not backup_file.exists():  # Don't overwrite existing backups
                import shutil
                shutil.copy2(csv_file, backup_file)
                print(f"Created backup: {backup_file}")
        except Exception as e:
            print(f"Error backing up {csv_file}: {e}")
    
    print("Merge completed successfully.")

if __name__ == "__main__":
    merge_csv_files()

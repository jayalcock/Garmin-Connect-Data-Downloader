#!/usr/bin/env python3
"""
FIT to CSV Converter

This script converts Garmin .fit files to CSV format for analysis or importing into other tools.
"""

import os
import sys
import csv
import argparse
import pandas as pd
from pathlib import Path
from fitparse import FitFile
from datetime import datetime

def fit_to_csv(fit_file_path, output_dir=None, summary_only=False):
    """
    Convert a FIT file to CSV format

    Args:
        fit_file_path: Path to the FIT file
        output_dir: Directory to save the CSV file (defaults to same directory as FIT file)
        summary_only: If True, only create a summary CSV with key metrics

    Returns:
        Path to the generated CSV file
    """
    fit_path = Path(fit_file_path)
    
    if not fit_path.exists():
        print(f"Error: File not found: {fit_path}")
        return None
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = fit_path.parent
    
    base_name = fit_path.stem
    csv_path = output_dir / f"{base_name}.csv"
    summary_path = output_dir / f"{base_name}_summary.csv"
    
    try:
        # Parse the FIT file
        print(f"Parsing FIT file: {fit_path}")
        fitfile = FitFile(str(fit_path))
        
        # Data structures to store records
        records = []
        record_types = {}
        
        # Process all messages in the FIT file
        for record in fitfile.get_messages():
            record_type = record.name
            
            # Store the record type to track what kinds of data we've seen
            if record_type not in record_types:
                record_types[record_type] = []
            
            # Convert the record to a dictionary
            data_dict = {}
            for field in record:
                field_name = field.name
                if field_name not in record_types[record_type]:
                    record_types[record_type].append(field_name)
                
                # Store the field value
                if field.value is not None:
                    data_dict[field_name] = field.value
                    
                # Also store units if available
                if field.units:
                    data_dict[f"{field_name}_units"] = field.units
            
            # Add the record type to the dictionary
            data_dict['record_type'] = record_type
            records.append(data_dict)
        
        print(f"Found {len(records)} records of {len(record_types)} types")
        
        # If there are no records, exit
        if not records:
            print("Error: No data found in FIT file")
            return None
            
        # Create a full DataFrame with all records
        if not summary_only:
            df = pd.DataFrame(records)
            df.to_csv(csv_path, index=False)
            print(f"Saved detailed CSV to: {csv_path}")

        # Create a summary of the workout
        summary = create_workout_summary(records, record_types)
        
        # Save the summary to CSV
        with open(summary_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in summary.items():
                writer.writerow([key, value])
        
        print(f"Saved summary CSV to: {summary_path}")
        
        return csv_path if not summary_only else summary_path
        
    except Exception as e:
        print(f"Error processing FIT file: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_workout_summary(records, record_types):
    """Create a summary of the workout data"""
    summary = {}
    
    # Extract session data (overall workout metrics)
    session_records = [r for r in records if r.get('record_type') == 'session']
    if session_records:
        session = session_records[0]  # Use the first session record
        
        # Add basic workout information
        for field in ['sport', 'sub_sport', 'total_elapsed_time', 'total_timer_time', 
                     'total_distance', 'total_calories', 'avg_speed', 'max_speed',
                     'avg_heart_rate', 'max_heart_rate', 'avg_cadence', 'max_cadence',
                     'avg_power', 'max_power', 'total_ascent', 'total_descent',
                     'start_time', 'timestamp']:
            if field in session:
                summary[field] = session[field]
                
                # Add units if available
                if f"{field}_units" in session:
                    summary[f"{field}_units"] = session[f"{field}_units"]
    
    # Calculate statistics from record data
    record_data = [r for r in records if r.get('record_type') == 'record']
    if record_data:
        # Convert list of dicts to DataFrame for easier analysis
        df = pd.DataFrame(record_data)
        
        # Calculate metrics that might not be in the session summary
        metrics = ['heart_rate', 'cadence', 'speed', 'power', 'altitude', 'temperature']
        for metric in metrics:
            if metric in df.columns:
                # Only add metrics not already in summary
                if f"avg_{metric}" not in summary:
                    summary[f"avg_{metric}"] = df[metric].mean()
                if f"max_{metric}" not in summary:
                    summary[f"max_{metric}"] = df[metric].max()
                if f"min_{metric}" not in summary and metric != 'cadence':  # Min cadence is usually 0
                    summary[f"min_{metric}"] = df[metric].min()
    
    # Extract lap information
    lap_records = [r for r in records if r.get('record_type') == 'lap']
    if lap_records:
        summary['number_of_laps'] = len(lap_records)
        
        # Calculate average lap metrics
        lap_df = pd.DataFrame(lap_records)
        if 'total_distance' in lap_df.columns:
            summary['avg_lap_distance'] = lap_df['total_distance'].mean()
        if 'total_elapsed_time' in lap_df.columns:
            summary['avg_lap_time'] = lap_df['total_elapsed_time'].mean()

    # Calculate time in heart rate zones if available
    hr_zone_records = [r for r in records if r.get('record_type') == 'hr_zone']
    if hr_zone_records:
        for record in hr_zone_records:
            if 'time_in_zone' in record and 'zone_number' in record:
                summary[f'time_in_hr_zone_{record["zone_number"]}'] = record['time_in_zone']
    
    # Format timestamps for better readability
    for key in ['start_time', 'timestamp']:
        if key in summary and isinstance(summary[key], datetime):
            summary[key] = summary[key].strftime('%Y-%m-%d %H:%M:%S')
    
    # Add what types of data are in the file
    summary['available_data_types'] = ', '.join(record_types.keys())
    
    return summary

def main():
    """Process command line arguments and run the converter"""
    parser = argparse.ArgumentParser(description='Convert FIT files to CSV format')
    parser.add_argument('input', help='FIT file or directory containing FIT files')
    parser.add_argument('-o', '--output', help='Output directory for CSV files')
    parser.add_argument('-s', '--summary', action='store_true', help='Generate only summary CSV')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process directories recursively')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Process a single file
        if input_path.suffix.lower() == '.fit':
            fit_to_csv(input_path, args.output, args.summary)
        else:
            print(f"Error: Input file must be a .fit file: {input_path}")
    elif input_path.is_dir():
        # Process all FIT files in the directory
        fit_files = []
        if args.recursive:
            fit_files = list(input_path.glob('**/*.fit'))
        else:
            fit_files = list(input_path.glob('*.fit'))
        
        if not fit_files:
            print(f"No FIT files found in {input_path}")
            return
        
        print(f"Found {len(fit_files)} FIT files to process")
        for fit_file in fit_files:
            fit_to_csv(fit_file, args.output, args.summary)
    else:
        print(f"Error: Input path does not exist: {input_path}")

if __name__ == '__main__':
    main()

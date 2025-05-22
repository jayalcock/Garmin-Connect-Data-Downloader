#!/usr/bin/env python3
"""
Simple FIT to CSV and analysis tool for Garmin activities
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

def convert_and_analyze(fit_file, output_dir=None, verbose=False):
    """
    Convert a FIT file to CSV and create an analysis summary
    
    Args:
        fit_file: Path to the FIT file
        output_dir: Directory to save output files (defaults to same as input file)
        verbose: Whether to print verbose output
    
    Returns:
        Tuple of (csv_path, analysis_path) if successful, None otherwise
    """
    # Import fitparse here to handle any import errors
    try:
        from fitparse import FitFile
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install fitparse with: pip install fitparse")
        return None
    
    fit_path = Path(fit_file)
    if not fit_path.exists():
        print(f"Error: FIT file not found: {fit_path}")
        return None
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = fit_path.parent
    
    # Output file paths
    csv_path = output_dir / f"{fit_path.stem}.csv"
    analysis_path = output_dir / f"{fit_path.stem}_analysis.md"
    
    try:
        if verbose:
            print(f"Processing FIT file: {fit_path}")
        
        # Convert FIT to CSV
        # Parse the FIT file
        fitfile = FitFile(str(fit_path))
        
        # Extract all records
        records = []
        for record in fitfile.get_messages():
            record_type = record.name
            
            data_dict = {'record_type': record_type}
            for field in record:
                field_name = field.name
                
                if field.value is not None:
                    data_dict[field_name] = field.value
                
                if field.units:
                    data_dict[f"{field_name}_units"] = field.units
            
            records.append(data_dict)
        
        if not records:
            print("No data found in FIT file")
            return None
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False)
        
        if verbose:
            print(f"Created CSV: {csv_path}")
        
        # Now create a simple analysis
        # Extract different record types
        record_df = df[df['record_type'] == 'record'].copy()
        session_df = df[df['record_type'] == 'session'].copy()
        lap_df = df[df['record_type'] == 'lap'].copy()
        
        # Check if we have the necessary data
        if session_df.empty:
            print("No session data found in activity")
            return csv_path, None
        
        # Create analysis file
        with open(analysis_path, 'w') as f:
            # Title
            f.write("# Garmin Activity Analysis\n\n")
            
            # Basic session info
            session = session_df.iloc[0]
            sport_type = session.get('sport', 'Activity')
            f.write(f"## {sport_type.title()} Summary\n\n")
            
            # Basic metrics
            metrics = []
            
            # Distance
            if 'total_distance' in session:
                distance = session['total_distance']
                metrics.append(f"**Distance:** {distance/1000:.2f} km")
            
            # Duration
            if 'total_elapsed_time' in session:
                time = session['total_elapsed_time']
                minutes = int(time // 60)
                seconds = int(time % 60)
                metrics.append(f"**Duration:** {minutes}:{seconds:02d}")
            
            # Calories
            if 'total_calories' in session:
                metrics.append(f"**Calories:** {int(session['total_calories'])}")
            
            # Heart rate
            if 'avg_heart_rate' in session:
                metrics.append(f"**Avg HR:** {int(session['avg_heart_rate'])} bpm")
            
            # Speed
            if 'avg_speed' in session:
                speed = session['avg_speed'] * 3.6  # Convert m/s to km/h
                metrics.append(f"**Avg Speed:** {speed:.1f} km/h")
            
            # Write all metrics
            for metric in metrics:
                f.write(f"{metric}\n")
            
            f.write("\n## Tips for ChatGPT Analysis\n\n")
            f.write("When analyzing this workout with ChatGPT, consider asking about:\n\n")
            f.write("1. Performance relative to your goals\n")
            f.write("2. Trends in your metrics over time\n")
            f.write("3. Suggestions for improving specific aspects\n")
            f.write("4. Recovery recommendations\n")
        
        if verbose:
            print(f"Created analysis: {analysis_path}")
        
        return csv_path, analysis_path
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fit_converter.py <fit_file> [output_dir]")
        sys.exit(1)
    
    fit_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = convert_and_analyze(fit_file, output_dir, verbose=True)
    
    if result:
        csv_path, analysis_path = result
        print("\nConversion complete!")
        print(f"CSV file: {csv_path}")
        print(f"Analysis file: {analysis_path}")
    else:
        print("\nConversion failed!")
        sys.exit(1)

#!/usr/bin/env python3
# Simple test script to check raw JSON weight data

import json
import os
from pathlib import Path

def main():
    """Simple test to check raw JSON weight data"""
    # Load a sample raw JSON file
    json_path = Path(__file__).parent / "exports" / "garmin_stats_2025-05-11_raw.json"
    
    print(f"Looking for file: {json_path}")
    print(f"File exists: {json_path.exists()}")
    
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print("\n===== Raw Data from JSON =====")
            print(f"Raw weight value: {raw_data.get('weight')}")
            print(f"Raw BMI value: {raw_data.get('bmi')}")
            print(f"Raw bodyFat value: {raw_data.get('bodyFat')}")
            
            if raw_data.get('weight'):
                print(f"\nWeight in kg: {raw_data.get('weight', 0) / 1000:.2f}")
        except Exception as e:
            print(f"Error processing JSON: {e}")
    else:
        print(f"File not found: {json_path}")

if __name__ == "__main__":
    main()
    print("Script completed.")

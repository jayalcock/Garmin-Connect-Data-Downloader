#!/usr/bin/env python3
# Test script to verify weight data mapping

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from garmin_sync import get_stats

def main():
    """Test weight data extraction from raw JSON"""
    # Load a sample raw JSON file
    json_path = Path(__file__).parent / "exports" / "garmin_stats_2025-05-11_raw.json"
    
    if not json_path.exists():
        print(f"Error: Cannot find {json_path}")
        sys.exit(1)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print("\n===== Raw Data from JSON =====")
    print(f"Raw weight value: {raw_data.get('weight')}")
    print(f"Raw weightInGrams value: {raw_data.get('weightInGrams')}")
    print(f"Raw bodyFat value: {raw_data.get('bodyFat')}")
    print(f"Raw bodyFatPercentage value: {raw_data.get('bodyFatPercentage')}")
    
    # Apply our field mapping
    field_mappings = {
        'weight': 'weightInGrams',
        'bodyFat': 'bodyFatPercentage',
    }
    
    # Apply field mappings to simulate what get_stats does
    for api_field, our_field in field_mappings.items():
        if api_field in raw_data and our_field not in raw_data:
            raw_data[our_field] = raw_data[api_field]
            print(f"\nMapped {api_field} to {our_field}: {raw_data[our_field]}")
    
    print("\n===== After Field Mapping =====")
    print(f"Weight in kg: {raw_data.get('weightInGrams', 0) / 1000:.2f}")
    print(f"BMI: {raw_data.get('bmi')}")
    print(f"Body Fat: {raw_data.get('bodyFatPercentage')}%")

if __name__ == "__main__":
    main()

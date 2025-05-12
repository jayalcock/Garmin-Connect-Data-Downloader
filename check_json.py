#!/usr/bin/env python3
import json
import sys

# Load the raw JSON data
try:
    with open("exports/garmin_stats_2025-05-11_raw.json", 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading JSON: {e}")
    sys.exit(1)

# Check for specific missing fields
missing_fields = ["visceralFat", "metabolicAge", "physiqueRating", "hrRestingLowHrvValue"]
print("Missing fields in the raw JSON data:")
for field in missing_fields:
    print(f"{field}: {data.get(field)}")

# Print some of the available fields for context
print("\nSome available fields in the raw JSON data:")
for field in sorted(data.keys())[:20]:
    print(f"{field}: {data.get(field)}")

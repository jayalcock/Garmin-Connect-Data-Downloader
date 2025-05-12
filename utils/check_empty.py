#!/usr/bin/env python3
import csv
import os
import sys

# Add the parent directory to the path to ensure we can find modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Path to the CSV file
csv_path = os.path.join(parent_dir, 'exports', 'garmin_stats.csv')

with open(csv_path, 'r') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = list(reader)

for i, row in enumerate(rows):
    empty_fields = []
    for j, (header, value) in enumerate(zip(headers, row)):
        if value == "":
            empty_fields.append(header)
    
    print(f"Row {i+1} ({row[0]}): {len(empty_fields)} empty fields")
    if empty_fields:
        print(f"  Empty fields: {empty_fields}")

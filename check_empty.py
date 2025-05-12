#!/usr/bin/env python3
import csv

with open('exports/garmin_stats.csv', 'r') as f:
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

#!/usr/bin/env python3
# Test the CSV export functionality

from pathlib import Path
import os
from fixed_downloader import export_to_csv

# Set up test directory and file
output_dir = Path('./test_export')
output_dir.mkdir(exist_ok=True)
csv_path = output_dir / 'garmin_stats.csv'

# Create initial test CSV with sample data
with open(csv_path, 'w') as f:
    f.write('date,steps,restingHeartRate\n2025-05-11,10000,60\n2025-05-10,8000,55\n')

print(f'\nInitial CSV content:')
with open(csv_path) as f:
    print(f.read())

# Now update a record using our export function
print("\nUpdating the 2025-05-11 entry...")
stats = {'date': '2025-05-11', 'steps': 12000, 'restingHeartRate': 58}
export_to_csv(stats, '2025-05-11', output_dir)

# Check the updated file
print(f'\nAfter update, CSV content:')
with open(output_dir / 'garmin_stats.csv') as f:
    print(f.read())

# Clean up
import shutil
print('\nCleaning up test files...')
shutil.rmtree(output_dir)
print('Done!')

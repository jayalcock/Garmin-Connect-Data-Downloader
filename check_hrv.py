#!/usr/bin/env python3
import os
import sys
import json
from garmin_sync import connect_to_garmin

# Set test mode
os.environ["GARMIN_TEST_MODE"] = "true"

# Connect to Garmin
client = connect_to_garmin()
if not client:
    print("Failed to connect to Garmin Connect")
    sys.exit(1)

# Get HRV data for today
date_str = "2025-05-11"
print(f"Getting HRV data for {date_str}")
hrv_data = client.get_hrv_data(date_str)

# Save HRV data to file for examination
with open("hrv_data.json", "w") as f:
    json.dump(hrv_data, f, indent=2)
print(f"HRV data saved to hrv_data.json")

# Print HRV top-level keys
if hrv_data:
    print("\nHRV data keys:")
    print(sorted(hrv_data.keys()))
    
    # Check for summary if available
    if 'hrvSummary' in hrv_data:
        print("\nHRV Summary:")
        print(json.dumps(hrv_data['hrvSummary'], indent=2))

#!/usr/bin/env python3
# Auto-generated script for daily Garmin data export

import os
import sys
import datetime

# Add the parent directory to find the garmin_sync module
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from garmin_sync import connect_to_garmin, get_stats

def main():
    """Run the daily export"""
    print(f"Running daily Garmin Connect export on {datetime.datetime.now().isoformat()}")
    
    # Connect to Garmin Connect using saved credentials (non-interactive)
    client = connect_to_garmin(non_interactive=True, allow_mfa=False)
    
    if client:
        # Get yesterday's data (more likely to be complete than today's)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        get_stats(client, yesterday, export=True, interactive=False)
        
        # Also get today's data
        today = datetime.date.today().isoformat()
        get_stats(client, today, export=True, interactive=False)
    else:
        print("Failed to connect to Garmin Connect")
        sys.exit(1)

if __name__ == "__main__":
    main()

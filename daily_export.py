#!/usr/bin/env python3
# Auto-generated script for daily Garmin data export

import os
import sys
import datetime

# Add the parent directory to the path to find the downloader module
sys.path.append("/Users/jay/Projects/Garmin Apps/Data download")

from downloader import connect_to_garmin, get_stats

def main():
    """Run the daily export"""
    print(f"Running daily Garmin Connect export on {datetime.datetime.now().isoformat()}")
    
    # Connect to Garmin Connect using saved credentials (non-interactive)
    client = connect_to_garmin()
    
    if client:
        # Get yesterday's data (more likely to be complete than today's)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        get_stats(client, yesterday, export=True)
        
        # Also get today's data
        today = datetime.date.today().isoformat()
        get_stats(client, today, export=True)
    else:
        print("Failed to connect to Garmin Connect")
        sys.exit(1)

if __name__ == "__main__":
    main()

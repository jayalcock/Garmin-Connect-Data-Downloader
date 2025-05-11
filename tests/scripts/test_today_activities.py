#!/usr/bin/env python3
"""
Test script for the today's activities download functionality
"""

import os
import sys
import importlib.util

parent_dir = os.path.abspath(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

garmin_sync_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'garmin_sync.py')
spec = importlib.util.spec_from_file_location('garmin_sync', garmin_sync_path)
garmin_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(garmin_sync)
connect_to_garmin = garmin_sync.connect_to_garmin
download_today_activities = garmin_sync.download_today_activities

def main():
    """Test the download today's activities functionality"""
    print("Testing automatic download of today's activities")
    
    # Connect to Garmin Connect
    garmin_client = connect_to_garmin(non_interactive=True)
    
    if garmin_client:
        # Download today's activities in TCX format
        download_today_activities(garmin_client, "TCX")
    else:
        print("Failed to connect to Garmin Connect")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test script for the today's activities download functionality
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from downloader import connect_to_garmin, download_today_activities

def main():
    """Test the download today's activities functionality"""
    print("Testing automatic download of today's activities")
    
    # Connect to Garmin Connect
    garmin_client = connect_to_garmin()
    
    if garmin_client:
        # Download today's activities in TCX format
        download_today_activities(garmin_client, "TCX")
    else:
        print("Failed to connect to Garmin Connect")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

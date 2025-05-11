#!/usr/bin/env python3
# Manual export script that you can run when you're available to provide MFA

import os
import sys
import datetime
from pathlib import Path

# Import handling for both direct execution and being imported
# First, try to use fixed_downloader.py from the parent directory
try:
    # Add the parent directory to the path to find the fixed_downloader module
    parent_dir = Path(__file__).parent.parent
    sys.path.append(str(parent_dir))
    import fixed_downloader
    from fixed_downloader import connect_to_garmin, get_stats
except ImportError:
    # Fall back to the original downloader if fixed_downloader is not available
    try:
        # When imported from run_manual_export.py
        from src import downloader
        from src.downloader import connect_to_garmin, get_stats
    except ImportError:
        try:
            # When run directly or as a module in the src package
            from . import downloader
            from .downloader import connect_to_garmin, get_stats
        except ImportError:
            # Fallback for direct script execution
            import downloader
            from downloader import connect_to_garmin, get_stats

def main():
    """Run manual Garmin data export"""
    print(f"Running Garmin Connect export on {datetime.datetime.now().isoformat()}")
    print("This script requires you to enter MFA code when prompted.")
    
    # Connect to Garmin Connect with MFA support explicitly enabled
    client = connect_to_garmin(non_interactive=False, allow_mfa=True)
    
    if client:
        # Get yesterday's data
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        get_stats(client, yesterday, export=True)
        
        # Get today's data
        today = datetime.date.today().isoformat()
        get_stats(client, today, export=True)
        
        print("\nData export complete! Files have been saved to:")
        export_dir = Path(__file__).parent / "exports"
        print(f"- Local directory: {export_dir}")
        print(f"- Nextcloud directory: /Users/jay/Nextcloud/Garmin Health Data/")
    else:
        print("Failed to connect to Garmin Connect")
        sys.exit(1)

if __name__ == "__main__":
    main()

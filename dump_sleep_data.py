#!/usr/bin/env python3

import sys
import json
import datetime as dt
from garmin_sync import connect_to_garmin

def main():
    # Connect to Garmin
    garmin_client = connect_to_garmin()
    if not garmin_client:
        print("Failed to connect to Garmin Connect")
        return
    
    # Get date from command line or use today
    date_str = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    print(f"Getting sleep data for {date_str}")
    
    # Get sleep data
    sleep_data = garmin_client.get_sleep_data(date_str)
    
    # Dump to JSON file
    output_file = f"sleep_data_{date_str}.json"
    with open(output_file, 'w') as f:
        json.dump(sleep_data, f, indent=2)
    
    print(f"Saved sleep data to {output_file}")
    
    # Print top-level keys
    print("\nTop-level keys in sleep data:")
    print(sorted(sleep_data.keys()))
    
    # Print sleepLevels if available
    if 'sleepLevels' in sleep_data:
        print("\nSleep Levels:")
        print(json.dumps(sleep_data['sleepLevels'], indent=2))

if __name__ == "__main__":
    main()

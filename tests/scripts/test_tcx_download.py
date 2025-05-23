#!/usr/bin/env python3
# Test TCX download functionality

import importlib.util
import os
garmin_sync_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'garmin_sync.py')
spec = importlib.util.spec_from_file_location('garmin_sync', garmin_sync_path)
garmin_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(garmin_sync)
connect_to_garmin = garmin_sync.connect_to_garmin
download_activity_file = garmin_sync.download_activity_file

def test_tcx_download():
    """Test downloading a TCX file with the fixed filename generation"""
    client = connect_to_garmin(non_interactive=True)
    if client:
        # Use a sample activity ID - this may not exist on your account
        # but it will test the filename generation code
        activity_id = '12345678'
        result = download_activity_file(client, activity_id, 'TCX')
        if result:
            print(f"Success! Downloaded to: {result}")
        else:
            print("Failed to download activity")

if __name__ == "__main__":
    test_tcx_download()

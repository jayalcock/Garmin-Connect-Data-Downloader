#!/usr/bin/env python3
# Test TCX download functionality

from src.downloader import connect_to_garmin, download_activity_file

def test_tcx_download():
    """Test downloading a TCX file with the fixed filename generation"""
    client = connect_to_garmin()
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

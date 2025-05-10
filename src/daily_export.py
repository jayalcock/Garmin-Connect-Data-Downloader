#!/usr/bin/env python3
# Auto-generated script for daily Garmin data export

import sys
import datetime
import time
import subprocess
import json
from pathlib import Path

# Import from the same package
from . import downloader
from .downloader import load_saved_credentials, decrypt_password, get_stats, connect_to_garmin

# Maximum number of attempts to connect
MAX_ATTEMPTS = 3

def send_notification(title, message):
    """Send a notification on macOS"""
    try:
        subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'])
        print(f"Notification: {title} - {message}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def main():
    """Run the daily export"""
    start_time = datetime.datetime.now().isoformat()
    print(f"Running daily Garmin Connect export on {start_time}")
    log_file = Path("/Users/jay/Projects/Garmin Apps/Data download/logs/auth_status.json")
    
    # Import the module here to avoid import errors if it's not installed
    try:
        from garminconnect import Garmin
    except ImportError:
        print("Error: garminconnect module not found. Please install it with 'pip install garminconnect'")
        send_notification("Garmin Export Failed", "Missing required package")
        sys.exit(1)
    
    # Load saved credentials
    username, encrypted_pw = load_saved_credentials()
    if not username or not encrypted_pw:
        print("Error: No saved credentials found")
        send_notification("Garmin Export Failed", "No saved credentials found")
        sys.exit(1)
    
    password = decrypt_password(encrypted_pw)
    if not password:
        print("Error: Failed to decrypt password")
        send_notification("Garmin Export Failed", "Failed to decrypt password")
        sys.exit(1)
    
    # Log auth status
    auth_status = {
        "last_attempt": start_time,
        "success": False,
        "message": "Not yet tried"
    }
    
    # Attempt to connect to Garmin Connect using non-interactive mode
    client = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Attempt {attempt+1}/{MAX_ATTEMPTS} to connect to Garmin Connect...")
            # Explicitly set allow_mfa=False for automated runs
            client = connect_to_garmin(non_interactive=True, allow_mfa=False)
            if client:
                print("Authentication successful!")
                
                auth_status["success"] = True
                auth_status["message"] = "Authentication successful"
                
                # Save auth status
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(auth_status, f)
                
                break
            else:
                print("Failed to authenticate - MFA likely required")
                auth_status["message"] = "Failed to authenticate - MFA likely required"
        except Exception as e:
            print(f"Authentication error: {e}")
            auth_status["message"] = f"Authentication error: {e}"
            
        # Wait before next attempt
        time.sleep(5)
    
    # If we couldn't connect, exit
    if not client or not auth_status["success"]:
        print("Failed to connect to Garmin Connect after multiple attempts")
        auth_status["message"] = "Failed after multiple attempts"
        
        # Save auth status
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(auth_status, f)
            
        send_notification("Garmin Export Failed", "Authentication failed - MFA likely required")
        sys.exit(1)
    
    try:
        # Get yesterday's data (more likely to be complete than today's)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        result_yesterday = get_stats(client, yesterday, export=True)
        
        # Also get today's data
        today = datetime.date.today().isoformat()
        result_today = get_stats(client, today, export=True)
        
        if result_yesterday or result_today:
            send_notification("Garmin Export Successful", f"Exported data for {yesterday} and {today}")
        else:
            send_notification("Garmin Export Warning", "Connected but no data exported")
    except Exception as e:
        print(f"Error during data export: {e}")
        send_notification("Garmin Export Error", "Error during data export")
        sys.exit(1)

if __name__ == "__main__":
    main()

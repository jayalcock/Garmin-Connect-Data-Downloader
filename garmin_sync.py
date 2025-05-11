#!/usr/bin/env python3

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garth.exc import GarthHTTPError
import datetime as dt
import os
import getpass
import sys
import json
import csv
import time
import shutil
import base64
import logging
import builtins
from pathlib import Path
import traceback
import requests
from typing import Tuple, Optional, Dict, Any, Union

def load_saved_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load saved credentials if they exist"""
    config_path = Path.home() / '.garmin_config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('username'), config.get('encrypted_password')
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading saved credentials: {e}")
            return None, None
    return None, None

def save_credentials(username: str, password: str) -> None:
    """Save credentials (with basic obfuscation - not truly secure)"""
    # This is just basic obfuscation, not true encryption
    # For true security, use a dedicated password manager
    encrypted = base64.b64encode(password.encode()).decode()
    
    config_path = Path.home() / '.garmin_config.json'
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'encrypted_password': encrypted
            }, f)
        os.chmod(config_path, 0o600)  # Set permissions to user-only read/write
    except IOError as e:
        print(f"Error saving credentials: {e}")

def decrypt_password(encrypted: str) -> Optional[str]:
    """Decrypt the saved password"""
    if not encrypted:
        return None
    try:
        return base64.b64decode(encrypted.encode()).decode()
    except (TypeError, ValueError) as e:
        print(f"Error decrypting password: {e}")
        return None

def get_mfa_code():
    """Prompt user for MFA code"""
    print("Multi-Factor Authentication required.")
    return input("MFA one-time code: ")

def connect_to_garmin(non_interactive: bool = False, allow_mfa: bool = True) -> Optional[Garmin]:
    """Connect to Garmin account with login
    
    Args:
        non_interactive: If True, will attempt to connect without user input
                        (for automated scripts). If False (default), will prompt
                        for credentials and MFA.
        allow_mfa: If True (default), will prompt for MFA code when needed.
                   If False, will not attempt MFA authentication.
    
    Returns:
        Garmin client object if successful, None otherwise
    """
    # Define token storage paths
    tokenstore = os.path.expanduser("~/.garminconnect")
    
    # Try to load saved credentials first
    saved_username, saved_encrypted_pw = load_saved_credentials()
    
    # For non-interactive mode, we must have saved credentials
    if non_interactive:
        if not saved_username or not saved_encrypted_pw:
            print("Error: Non-interactive mode requires saved credentials")
            return None
        
        email = saved_username
        password = decrypt_password(saved_encrypted_pw)
        if not password:
            print("Error: Failed to decrypt password")
            return None
    else:
        # Interactive mode - ask user for input
        if saved_username:
            print(f"Found saved credentials for {saved_username}")
            use_saved = input("Use saved credentials? (y/n): ").strip().lower() == 'y'
            email = saved_username if use_saved else input("Enter your Garmin Connect email: ")
            
            if use_saved:
                password = decrypt_password(saved_encrypted_pw)
            else:
                password = getpass.getpass("Enter your Garmin Connect password: ")
        else:
            email = input("Enter your Garmin Connect email: ") if len(sys.argv) < 2 else sys.argv[1]
            password = getpass.getpass("Enter your Garmin Connect password: ")
            
            # Ask if user wants to save credentials
            if input("Save credentials for future use? (y/n): ").strip().lower() == 'y':
                save_credentials(email, password)
    
    # Attempt to connect to Garmin
    try:
        print("Authenticating with Garmin Connect...")
        print(f"Username: {email}")
        
        # Try to login using stored tokens first
        try:
            print(f"Trying to login using token data from '{tokenstore}'...")
            garmin = Garmin()
            garmin.login(tokenstore)
            print("Successfully logged in using saved tokens!")
            return garmin
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError) as e:
            print(f"Login tokens not present or expired, will log in with credentials: {e}")
        
        # Initialize Garmin client with email/password
        garmin = Garmin(email=email, password=password, is_cn=False)
        
        # Check if we're running in test mode
        test_mode = os.environ.get('GARMIN_TEST_MODE', 'false').lower() == 'true'
        
        if test_mode:
            # In test mode, mock the login process
            print("Running in test mode. MFA is being mocked.")
            # Don't actually call login - just pretend it succeeded
        elif allow_mfa:
            # Handle MFA if needed
            print("Note: If MFA is required, you will be prompted to enter a code.")
            # Login first step - may need MFA
            try:
                result = garmin.login()
                # Check if a tuple was returned (indicating MFA is needed)
                if isinstance(result, tuple) and len(result) == 2 and result[0] == "needs_mfa":
                    mfa_code = get_mfa_code()
                    garmin.resume_login(result[1], mfa_code)
                    
                # Save tokens for future use
                garmin.garth.dump(tokenstore)
                print(f"Tokens saved to '{tokenstore}' for future use.")
            except Exception as e:
                print(f"Login error: {e}")
                traceback.print_exc()
                return None
        else:
            # Attempt login but don't handle MFA prompts
            # This will fail if MFA is required
            try:
                # For no MFA, just try basic login
                garmin.login()
                garmin.garth.dump(tokenstore)
            except Exception as e:
                if "factor" in str(e).lower() or "mfa" in str(e).lower() or "verification" in str(e).lower():
                    print("Multi-factor authentication required but disabled.")
                    print("Enable MFA support with allow_mfa=True or use an app password if available.")
                    return None
                raise  # Re-raise if it's not an MFA-related error
        
        print("Authentication successful!")
        return garmin
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error: {e}")
        print("Check your internet connection and try again.")
        return None
    except ValueError as e:
        print(f"Value error: {e}")
        return None
    except (GarminConnectConnectionError, GarminConnectAuthenticationError, 
            GarminConnectTooManyRequestsError, requests.exceptions.HTTPError, GarthHTTPError) as e:
        print(f"Error connecting to Garmin Connect: {e}")
        traceback.print_exc()
        print("\nPossible solutions:")
        print("1. Check that your email and password are correct")
        print("2. Garmin might be blocking automated logins for security")
        print("3. Your account might require 2FA (two-factor authentication)")
        print("4. If using MFA, you may need to generate an app password in your Garmin account")
        return None
    except Exception as e:
        print(f"Unknown error: {e}")
        traceback.print_exc()
        return None

def export_to_csv(stats: Dict[str, Any], date_str: str, export_dir: Path) -> Path:
    """Export Garmin stats to a CSV file
    
    Args:
        stats: The stats dictionary from Garmin Connect
        date_str: The date string in ISO format (YYYY-MM-DD)
        export_dir: Directory to export to
        
    Returns:
        Path to the exported CSV file
    """
    # Ensure the export directory exists
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Use a single CSV file for all dates
    csv_file = export_dir / "garmin_stats.csv"
    
    # Define the fields we want to export
    date_fields = [
        'date', 'year', 'month', 'day', 'day_of_week'
    ]
    
    base_fields = [
        'totalDistanceMeters', 'totalKilocalories', 
        'activeKilocalories', 'bmrKilocalories', 'restingHeartRate', 'maxHeartRate',
        'minHeartRate', 'lastSevenDaysAvgRestingHeartRate', 'totalSteps', 
        'dailyStepGoal', 'floorsAscended', 'floorsDescended'
    ]
    
    # Add activity fields
    activity_fields = [
        'activeSeconds', 'sedentarySeconds', 'highlyActiveSeconds',
        'moderateIntensityMinutes', 'vigorousIntensityMinutes'
    ]
    
    # Add sleep fields if available
    sleep_fields = [
        'sleepTimeSeconds', 'deepSleepSeconds', 'lightSleepSeconds', 
        'remSleepSeconds', 'awakeSleepSeconds', 'sleepingSeconds'
    ]
    
    # Add stress fields if available
    stress_fields = [
        'averageStressLevel', 'maxStressLevel', 'stressQualifier',
        'restStressDuration', 'lowStressDuration', 'mediumStressDuration',
        'highStressDuration', 'stressPercentage'
    ]
    
    # Add body measurement fields if available
    body_fields = [
        'weightInGrams', 'bmi', 'bodyFatPercentage', 'bodyWater', 'boneMass', 
        'muscleMass', 'visceralFat', 'metabolicAge', 'physiqueRating'
    ]
    
    # Add respiration fields if available
    respiration_fields = [
        'avgWakingRespirationValue', 'latestRespirationValue', 
        'highestRespirationValue', 'lowestRespirationValue'
    ]
    
    # Add HRV fields if available
    hrv_fields = [
        'averageHrvValue', 'maxHrvValue', 'minHrvValue', 'hrRestingLowHrvValue',
        'weeklyAvgHrv', 'lastNightAvgHrv', 'lastNight5MinHighHrv', 'hrvStatus'
    ]
    
    # Add Body Battery fields
    body_battery_fields = [
        'bodyBatteryChargedValue', 'bodyBatteryDrainedValue', 
        'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryMostRecentValue'
    ]
    
    # Add SpO2 data if available
    spo2_fields = [
        'averageSpo2', 'latestSpo2', 'lowestSpo2'
    ]
    
    # Group fields by category for better organization
    field_groups = {
        "Date": date_fields,
        "Base": base_fields,
        "Activity": activity_fields,
        "Sleep": sleep_fields,
        "Stress": stress_fields,
        "Body": body_fields,
        "Respiration": respiration_fields,
        "HRV": hrv_fields,
        "Body Battery": body_battery_fields,
        "SpO2": spo2_fields
    }
    
    # Instead of filtering, create a complete row with all possible fields
    all_fields = []  # Will be filled by the loop below
    for category, fields in field_groups.items():
        all_fields.extend(fields)
    
    # Convert stats to a row with all fields, using blank for missing data
    row_data = {}
    for field in all_fields:
        row_data[field] = stats.get(field, '')
    
    # Write to CSV
    file_exists = csv_file.exists() and os.path.getsize(csv_file) > 0
    
    # For consistency, we'll overwrite the file if it exists but has different columns
    # This ensures that changes to our data structure don't result in misaligned columns
    # If a date already exists in the file, we'll replace that entry with new data
    duplicate_entry = False
    existing_data = []
    
    if file_exists:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                existing_headers = next(reader)
                if set(existing_headers) != set(all_fields):
                    # Headers don't match, overwrite the file
                    file_exists = False
                else:
                    # Read all rows and check if our date exists
                    for row in reader:
                        if row and row[0] == date_str:  # First column should be date
                            duplicate_entry = True
                            # Skip this row (we'll add the updated version)
                            continue
                        # Keep all other rows
                        existing_data.append(row)
            except StopIteration:
                # File is empty
                file_exists = False
    
    # Write to the file with either all existing data + new row or just create new file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(all_fields)
        # Write all existing rows (except the one we're replacing)
        for row in existing_data:
            writer.writerow(row)
        # Write our new/updated row
        writer.writerow([row_data.get(field, '') for field in all_fields])
    
    # Also create a dated archive copy for backup
    archive_dir = export_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dated_csv_file = archive_dir / f"garmin_stats_{date_str}.csv"
    
    # Always create a fresh dated file
    with open(dated_csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        writer.writerow(row_data)
    
    print(f"Exported data to {csv_file}")
    print(f"Archived date-specific data to {dated_csv_file}")
    return csv_file

def backup_data_file(file_path: Path) -> bool:
    """Backup a file to Nextcloud
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        True if successful, False otherwise
    """
    # Define the Nextcloud path for your data
    nextcloud_dir = Path("/Users/jay/Nextcloud/Garmin Health Data")
    
    try:
        # Ensure the Nextcloud directory exists
        nextcloud_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the file to Nextcloud
        dest_path = nextcloud_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"Backed up file to Nextcloud: {dest_path}")
        
        # Also create a timestamped backup copy
        today = dt.date.today().isoformat()
        backup_path = nextcloud_dir / f"garmin_stats_backup_{today}.csv"
        shutil.copy2(file_path, backup_path)
        print(f"Created dated backup in Nextcloud: {backup_path}")
        
        return True
    except Exception as e:
        print(f"Error copying to Nextcloud: {e}")
        return False

def get_stats(garmin_client: Optional[Garmin], date_str: Optional[str] = None, export: bool = False, interactive: bool = True) -> Optional[Dict[str, Any]]:
    """Get activity statistics from Garmin Connect for a specific date
    
    Args:
        garmin_client: The Garmin Connect client
        date_str: The date in ISO format (YYYY-MM-DD), or None for today
        export: Whether to export the data to CSV
        interactive: Whether to allow interactive prompts during execution
        
    Returns:
        The stats dictionary if successful, None otherwise
    """
    if not garmin_client:
        return None
        
    try:
        # Use today's date if none provided
        if date_str is None:
            date_obj = dt.date.today()
            date_str = date_obj.isoformat()
        else:
            # Validate date format
            try:
                date_obj = dt.date.fromisoformat(date_str)
                date_str = date_obj.isoformat()  # Normalize the format
            except ValueError:
                print(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")
                return None
            
        print(f"Getting data for {date_str}...")
        
        # Get stats for the specified date
        stats = garmin_client.get_stats_and_body(date_str)
        
        # Try to get HRV data separately
        try:
            print("Trying to fetch HRV data...")
            hrv_data = garmin_client.get_hrv_data(date_str)
            if hrv_data:
                print("HRV data found!")
                # Update stats with HRV data
                stats.update(hrv_data)
                
                # Extract HRV summary values if available for easier CSV export
                if 'hrvSummary' in hrv_data:
                    hrv_summary = hrv_data['hrvSummary']
                    if hrv_summary:
                        # Map HRV summary fields to our flat structure
                        stats['weeklyAvgHrv'] = hrv_summary.get('weeklyAvg')
                        stats['lastNightAvgHrv'] = hrv_summary.get('lastNightAvg') 
                        stats['lastNight5MinHighHrv'] = hrv_summary.get('lastNight5MinHigh')
                        stats['hrvStatus'] = hrv_summary.get('status')
                        
                        # Calculate average, min, max HRV values from the readings if available
                        if 'hrvReadings' in hrv_data and hrv_data['hrvReadings']:
                            readings = hrv_data['hrvReadings']
                            hrv_values = [reading.get('hrvValue', 0) for reading in readings if 'hrvValue' in reading]
                            if hrv_values:
                                stats['averageHrvValue'] = sum(hrv_values) / len(hrv_values)
                                stats['maxHrvValue'] = max(hrv_values)
                                stats['minHrvValue'] = min(hrv_values)
            else:
                print("No HRV data available for this date.")
        except Exception as e:
            print(f"Error fetching HRV data: {e}")
        
        # Add date information to the stats dictionary
        stats['date'] = date_str
        
        # Also add year, month, day as separate fields for easier analysis
        year, month, day = date_str.split('-')
        stats['year'] = year
        stats['month'] = month
        stats['day'] = day
        
        # Add day of week (0=Monday, 6=Sunday)
        stats['day_of_week'] = date_obj.weekday()
        
        # Display summary stats
        print(f"\n===== Summary for {date_str} =====")
        print("Steps:", stats.get("totalSteps", "unknown"))
        print("Distance:", stats.get("totalDistanceMeters", "unknown"), "meters")
        print("Calories:", stats.get("totalKilocalories", "unknown"), "kcal")
        print("Active calories:", stats.get("activeKilocalories", "unknown"), "kcal")
        print("BMR calories:", stats.get("bmrKilocalories", "unknown"), "kcal")
        
        # Heart rate data
        print("\n===== Heart Rate =====")
        print("Resting HR:", stats.get("restingHeartRate", "unknown"), "bpm")
        print("Max HR:", stats.get("maxHeartRate", "unknown"), "bpm") 
        
        # HRV data if available
        hrv_found = False
        for hrv_key in ["averageHrvValue", "maxHrvValue", "minHrvValue", "hrRestingLowHrvValue"]:
            if hrv_key in stats:
                if not hrv_found:
                    print("\n===== Heart Rate Variability =====")
                    hrv_found = True
                print(f"{hrv_key}: {stats.get(hrv_key, 'unknown')}")
        
        # If HRV data is missing, print a note
        if not hrv_found:
            print("\n===== Heart Rate Variability =====")
            print("No HRV data available from Garmin Connect API for this date.")
            # Here you could add a call to a dedicated HRV function if you have one
        
        # Sleep data if available
        if "sleepTimeSeconds" in stats:
            sleep_hours = stats.get("sleepTimeSeconds", 0) / 3600
            print("\n===== Sleep =====")
            print(f"Sleep Duration: {sleep_hours:.2f} hours")
            print(f"Deep Sleep: {stats.get('deepSleepSeconds', 0) / 3600:.2f} hours")
            print(f"Light Sleep: {stats.get('lightSleepSeconds', 0) / 3600:.2f} hours")
            print(f"REM Sleep: {stats.get('remSleepSeconds', 0) / 3600:.2f} hours")
            print(f"Awake Time: {stats.get('awakeSleepSeconds', 0) / 3600:.2f} hours")
        
        # Body stats if available
        if "weightInGrams" in stats:
            print("\n===== Body Stats =====")
            print(f"Weight: {stats.get('weightInGrams', 0) / 1000:.2f} kg")
            print(f"BMI: {stats.get('bmi', 'unknown')}")
            print(f"Body Fat: {stats.get('bodyFatPercentage', 'unknown')}%")
        
        # Export data if requested
        if export:
            export_dir = Path(__file__).parent / "exports"
            # Log the full stats dictionary for debugging
            debug_json_path = export_dir / f"garmin_stats_{date_str}_raw.json"
            with open(debug_json_path, "w", encoding="utf-8") as debug_f:
                json.dump(stats, debug_f, indent=2, ensure_ascii=False)
            csv_path = export_to_csv(stats, date_str, export_dir)
            backup_data_file(csv_path)
        
        # Ask if user wants to see all data (only in interactive mode)
        if interactive and input("\nShow all available data? (y/n): ").strip().lower() == 'y':
            print("\n===== All Available Data =====")
            for key, value in sorted(stats.items()):
                print(f"{key}: {value}")
        
        return stats
    
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while getting stats: {e}")
        return None
    except ValueError as e:
        print(f"Value error while getting stats: {e}")
        return None
    except Exception as e:
        print(f"Error getting stats: {e}")
        traceback.print_exc()
        return None

def get_activities(garmin_client: Optional[Garmin], start_date: Optional[str] = None, limit: int = 5) -> None:
    """Get recent activities from Garmin Connect
    
    Args:
        garmin_client: The Garmin Connect client
        start_date: The start date in ISO format (YYYY-MM-DD), or None for recent activities.
                    If provided, will show only activities from this date.
        limit: Maximum number of activities to retrieve
    """
    if not garmin_client:
        return
        
    try:
        specific_date = None
        if start_date:
            try:
                specific_date = dt.date.fromisoformat(start_date)  # Validate date format
            except ValueError:
                print(f"Invalid date format: {start_date}. Please use YYYY-MM-DD format.")
                return
        
        # Always get activities from Garmin Connect
        print(f"Getting recent activities (max: {limit})...")
        activities = garmin_client.get_activities(0, limit)
        
        if not activities:
            print("No activities found for the specified period.")
            return
        
        # Filter activities by date if a specific date was provided
        filtered_activities = activities
        if specific_date:
            filtered_activities = []
            for activity in activities:
                start_time = activity.get("startTimeLocal", "")
                if start_time and "T" in start_time:
                    activity_date_str = start_time.split("T")[0]
                    try:
                        if activity_date_str == specific_date.isoformat():
                            filtered_activities.append(activity)
                    except:
                        # If date parsing fails, include activity by default
                        pass
            
            if not filtered_activities:
                print(f"No activities found for date {specific_date.isoformat()}.")
                return
            print(f"Found {len(filtered_activities)} activities for date {specific_date.isoformat()}")
            
        print(f"\n===== Recent Activities =====")
        for i, activity in enumerate(filtered_activities, 1):
            start_time = activity.get("startTimeLocal", "Unknown")
            name = activity.get("activityName", "Unknown")
            distance = activity.get("distance", 0)
            duration = activity.get("duration", 0) / 60  # Convert seconds to minutes
            
            print(f"\nActivity {i}:")
            print(f"Date: {start_time}")
            print(f"Type: {name}")
            print(f"Distance: {distance:.2f} meters")
            print(f"Duration: {duration:.2f} minutes")
            
            # Additional stats if available
            if "averageHR" in activity:
                print(f"Average HR: {activity.get('averageHR')} bpm")
            if "calories" in activity:
                print(f"Calories: {activity.get('calories')} kcal")
            
            activity_id = activity.get("activityId")
            if activity_id:
                print(f"Activity ID: {activity_id}")
                
                # Check if the activity is from today
                is_from_today = False
                if start_time:
                    # Parse the date part from startTimeLocal (format: YYYY-MM-DDThh:mm:ss.000)
                    if "T" in start_time:
                        activity_date = start_time.split("T")[0]
                        today_date = dt.date.today().isoformat()
                        is_from_today = (activity_date == today_date)
                
                # Automatically download today's activities
                if is_from_today:
                    print(f"Automatically downloading today's activity {i} in TCX format...")
                    download_activity_file(garmin_client, activity_id, 'TCX')
                else:
                    # For older activities, still ask for confirmation
                    download = input(f"Download activity {i} from {start_time} in TCX format? (y/n): ").strip().lower()
                    if download == 'y':
                        download_activity_file(garmin_client, activity_id, 'TCX')
                
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while getting activities: {e}")
    except ValueError as e:
        print(f"Value error while getting activities: {e}")
    except Exception as e:
        print(f"Error getting activities: {e}")
        traceback.print_exc()

def setup_daily_export(garmin_client: Optional[Garmin]) -> None:
    """Create a scheduled task to run the export daily"""
    if not garmin_client:
        print("Not connected to Garmin Connect.")
        return
    
    print("\n===== Setup Daily Export =====")
    print("This will set up a daily automatic export of your Garmin data to Nextcloud.")
    
    # Create the export directory
    export_dir = Path(__file__).parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Export today's data as a test
    print("Testing export functionality...")
    today = dt.date.today().isoformat()
    get_stats(garmin_client, today, export=True)
    
    # Create a script for the crontab
    script_path = Path(__file__).parent / "daily_export.py"
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(f'''#!/usr/bin/env python3
# Auto-generated script for daily Garmin data export

import os
import sys
import datetime

# Add the parent directory to the path to find the downloader module
sys.path.append("{Path(__file__).parent}")

from garmin_sync import connect_to_garmin, get_stats

def main():
    """Run the daily export"""
    print(f"Running daily Garmin Connect export on {{datetime.datetime.now().isoformat()}}")
    
    # Connect to Garmin Connect using saved credentials
    client = connect_to_garmin(allow_mfa=True)
    
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
''')
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    # Create a unique log file path
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "garmin_export.log"
    
    # Create the crontab entry
    cron_time = "0 9 * * *"  # Run at 9 AM every day
    cron_entry = f'{cron_time} {script_path} >> {log_path} 2>&1'
    
    print("\nTo set up the daily export crontab, you need to run the following command:")
    print(f"\n(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -")
    
    # Ask if user wants to set up crontab now
    if input("\nSet up crontab now? (y/n): ").strip().lower() == 'y':
        try:
            os.system(f"(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -")
            print("\nCrontab set up successfully! Your data will be exported daily at 9 AM.")
            print(f"Logs will be written to: {log_path}")
        except Exception as e:
            print(f"\nError setting up crontab: {e}")
            print("You may need to manually add the crontab entry using 'crontab -e'")
    
    print("\nYou can manually run the export script anytime with:")
    print(f"python3 {script_path}")

def download_activity_file(garmin_client: Optional[Garmin], activity_id: str, 
                        format_type: str = 'TCX', output_dir: Optional[Path] = None) -> Optional[Path]:
    """Download an activity file in the specified format
    
    Args:
        garmin_client: The Garmin Connect client
        activity_id: The activity ID to download
        format_type: Format type ('TCX', 'GPX', 'KML', 'CSV', 'ORIGINAL')
        output_dir: Output directory (defaults to exports/activities if None)
        
    Returns:
        Path to the downloaded file if successful, None otherwise
    """
    if not garmin_client:
        print("Not connected to Garmin Connect")
        return None
        
    try:
        # Get valid format type
        format_enum = None
        try:
            format_enum = getattr(Garmin.ActivityDownloadFormat, format_type.upper())
        except AttributeError:
            print(f"Invalid format: {format_type}")
            print("Valid formats: TCX, GPX, KML, CSV, ORIGINAL")
            return None
        
        # Get activity details for filename
        activity = garmin_client.get_activity_details(activity_id)
        if not activity:
            print(f"Activity ID {activity_id} not found")
            return None
        
        # Extract activity information for filename
        # For summary, check both activitySummary and summaryDTO paths
        summary = activity.get("activitySummary", activity.get("summaryDTO", {}))
        
        # Get start time for the filename
        start_time_local = None
        # Try different paths where start time might be found
        if "startTimeLocal" in summary:
            start_time_local = summary.get("startTimeLocal", "")
        elif "startTimeLocal" in activity:
            start_time_local = activity.get("startTimeLocal", "")
            
        if start_time_local:
            # Convert YYYY-MM-DDThh:mm:ss.000 to YYYY-MM-DD_hhmmss
            start_time_local = start_time_local.replace("T", "_").replace(":", "").split(".")[0]
        else:
            # Use current timestamp as fallback
            start_time_local = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Get activity name
        activity_name = None
        if "activityName" in activity:
            activity_name = activity.get("activityName", "").replace(" ", "_")
            
        # Get activity type
        activity_type = "activity"  # Default value
        if "activityType" in activity and isinstance(activity["activityType"], dict):
            activity_type = activity["activityType"].get("typeKey", "activity")
        
        # Create sanitized filename
        filename_parts = []
        
        # Always include timestamp
        if start_time_local:
            filename_parts.append(start_time_local)
            
        # Add activity type if available
        if activity_type and activity_type != "activity":
            filename_parts.append(activity_type)
            
        # Add activity name if available
        if activity_name:
            filename_parts.append(activity_name)
            
        # Add activity ID for uniqueness
        filename_parts.append(str(activity_id))
            
        # Join parts with underscores and add extension
        filename = "_".join(filename_parts) + f".{format_type.lower()}"
        
        # Replace any invalid characters
        filename = filename.replace("/", "_").replace("\\", "_")
        
        # Set up output directory
        if output_dir is None:
            output_dir = Path(__file__).parent / "exports" / "activities"
        
        # Ensure the directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Full path for the file
        output_path = output_dir / filename
        
        # Download the activity
        print(f"Downloading activity {activity_id} in {format_type} format...")
        activity_data = garmin_client.download_activity(activity_id, format_enum)
        
        # Write activity data to file
        with open(output_path, "wb") as f:
            f.write(activity_data)
            
        print(f"Activity downloaded to {output_path}")
        return output_path
        
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while downloading activity: {e}")
        print("Check your internet connection and try again.")
        return None
    except ValueError as e:
        print(f"Value error while downloading activity: {e}")
        return None
    except IOError as e:
        print(f"I/O error while saving activity file: {e}")
        print(f"Check if you have write permissions for {output_dir}")
        return None
    except Exception as e:
        print(f"Error downloading activity: {e}")
        traceback.print_exc()
        return None

def download_today_activities(garmin_client: Optional[Garmin], format_type: str = 'TCX') -> None:
    """Download all of today's activities
    
    This is a convenience function that gets today's activities and downloads them automatically.
    
    Args:
        garmin_client: The Garmin Connect client
        format_type: Format type ('TCX', 'GPX', 'KML', 'CSV', 'ORIGINAL')
    """
    if not garmin_client:
        print("Not connected to Garmin Connect")
        return
    
    today_date = dt.date.today().isoformat()
    print(f"Searching for activities from today ({today_date})...")
    
    # Get a larger number of recent activities to ensure we catch all of today's
    try:
        activities = garmin_client.get_activities(0, 10)
        
        if not activities:
            print("No recent activities found.")
            return
        
        # Filter for today's activities
        todays_activities = []
        for activity in activities:
            # Prefer local time; fallback to GMT timestamp
            start_time = activity.get("startTimeLocal") or activity.get("startTimeGMT")
            if not start_time:
                continue
            # Handle both 'T' and space-separated datetime formats
            if 'T' in start_time:
                date_token = start_time.split('T')[0]
            else:
                date_token = start_time.split()[0]
            if date_token == today_date:
                todays_activities.append(activity)
        if not todays_activities:
            # Debug: list all activity timestamps to see why none match today
            print("Debug: Activity timestamps:")
            for idx, activity in enumerate(activities, start=1):
                ts = activity.get("startTimeLocal") or activity.get("startTimeGMT")
                print(f"  {idx}. {ts}")
            print(f"No activities found for today ({today_date}).")
            return
        
        print(f"Found {len(todays_activities)} activities from today.")
        
        # Download each activity
        for i, activity in enumerate(todays_activities, 1):
            activity_id = activity.get("activityId")
            name = activity.get("activityName", "Unknown")
            
            if activity_id:
                print(f"\nDownloading activity {i}/{len(todays_activities)}: {name}")
                download_activity_file(garmin_client, activity_id, format_type)
            
        print(f"\nFinished downloading all {len(todays_activities)} activities from today.")
        
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while getting activities: {e}")
    except ValueError as e:
        print(f"Value error while getting activities: {e}")
    except Exception as e:
        print(f"Error getting activities: {e}")
        traceback.print_exc()

def get_hrv_data(garmin_client: Optional[Garmin], date_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get HRV data from Garmin Connect for a specific date
    
    Args:
        garmin_client: The Garmin Connect client
        date_str: The date in ISO format (YYYY-MM-DD), or None for today
        
    Returns:
        The HRV data dictionary if successful, None otherwise
    """
    if not garmin_client:
        return None
    
    try:
        # Use today's date if none provided
        if date_str is None:
            date_obj = dt.date.today()
            date_str = date_obj.isoformat()
        else:
            # Validate date format
            try:
                date_obj = dt.date.fromisoformat(date_str)
                date_str = date_obj.isoformat()  # Normalize the format
            except ValueError:
                print(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")
                return None
            
        print(f"Getting HRV data for {date_str}...")
        
        # Get HRV data for the specified date
        hrv_data = garmin_client.get_hrv_data(date_str)
        
        if hrv_data:
            print("\n===== Heart Rate Variability (HRV) =====")
            for key, value in sorted(hrv_data.items()):
                print(f"{key}: {value}")
            return hrv_data
        else:
            print("No HRV data available for this date.")
            return None
            
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while getting HRV data: {e}")
        return None
    except ValueError as e:
        print(f"Value error while getting HRV data: {e}")
        return None
    except Exception as e:
        print(f"Error getting HRV data: {e}")
        traceback.print_exc()
        return None

def show_menu(garmin_client: Optional[Garmin]) -> None:
    """Show menu of options for Garmin Connect data retrieval"""
    if not garmin_client:
        print("Not connected to Garmin Connect.")
        return
    
    while True:
        print("\n===== Garmin Connect Data Menu =====")
        print("1. Get today's stats")
        print("2. Get stats for a specific date")
        print("3. Get recent activities")
        print("4. Export today's data to CSV and Nextcloud")
        print("5. Setup daily automatic export to Nextcloud")
        print("6. Download an activity file")
        print("7. Download today's activities automatically")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            get_stats(garmin_client)
        elif choice == "2":
            date_str = input("Enter date (YYYY-MM-DD): ").strip()
            get_stats(garmin_client, date_str)
        elif choice == "3":
            limit = input("Enter number of activities to retrieve (default: 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            get_activities(garmin_client, limit=limit)
        elif choice == "4":
            today = dt.date.today().isoformat()
            get_stats(garmin_client, today, export=True)
        elif choice == "5":
            setup_daily_export(garmin_client)
        elif choice == "6":
            activity_id = input("Enter activity ID: ").strip()
            format_type = input("Enter format type (default: TCX, others: GPX, KML, CSV, ORIGINAL): ").strip().upper()
            if not format_type:
                format_type = "TCX"  # Set default format to TCX
            download_activity_file(garmin_client, activity_id, format_type)
        elif choice == "7":
            # Automatically download today's activities 
            format_type = input("Enter format type (default: TCX, others: GPX, KML, CSV, ORIGINAL): ").strip().upper()
            if not format_type:
                format_type = "TCX"  # Set default format to TCX
            download_today_activities(garmin_client, format_type)
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-8.")

if __name__ == "__main__":
    client = connect_to_garmin()
    if client:
        show_menu(client)

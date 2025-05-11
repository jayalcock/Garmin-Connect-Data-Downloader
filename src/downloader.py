from garminconnect import (armin
    Garmin,time as dt
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)mport json
from garth.exc import GarthHTTPError
import datetime as dt
import osutil
import getpassmport Path
import sysceback
import json import Tuple, Optional, Dict, Any, Union
import csv
import timeved_credentials() -> Tuple[Optional[str], Optional[str]]:
import shutilaved credentials if they exist"""
import base64th = Path.home() / '.garmin_config.json'
import loggingpath.exists():
import builtins
from pathlib import Pathnfig_path, 'r', encoding='utf-8') as f:
import tracebackconfig = json.load(f)
import requests return config.get('username'), config.get('encrypted_password')
from typing import Tuple, Optional, Dict, Any, Union
            print(f"Error loading saved credentials: {e}")
def load_saved_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load saved credentials if they exist"""
    config_path = Path.home() / '.garmin_config.json'
    if config_path.exists():e: str, password: str) -> None:
        try:credentials (with basic obfuscation - not truly secure)"""
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)ted password manager
                return config.get('username'), config.get('encrypted_password')
        except (IOError, json.JSONDecodeError) as e:decode()
            print(f"Error loading saved credentials: {e}")
            return None, None / '.garmin_config.json'
    return None, None
        with open(config_path, 'w', encoding='utf-8') as f:
def save_credentials(username: str, password: str) -> None:
    """Save credentials (with basic obfuscation - not truly secure)"""
    # This is just basic obfuscation, not true encryption
    # For true security, use a dedicated password manager
    import base64config_path, 0o600)  # Set permissions to user-only read/write
    encrypted = base64.b64encode(password.encode()).decode()
        print(f"Error saving credentials: {e}")
    config_path = Path.home() / '.garmin_config.json'
    try:ypt_password(encrypted: str) -> Optional[str]:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'encrypted_password': encrypted
            }, f)
        os.chmod(config_path, 0o600)  # Set permissions to user-only read/write
    except IOError as e:alueError) as e:
        print(f"Error saving credentials: {e}"))
        return None
def decrypt_password(encrypted: str) -> Optional[str]:
    """Decrypt the saved password"""e: bool = False, allow_mfa: bool = True) -> Optional[Garmin]:
    if not encrypted:min account with login
        return None
    import base64
    try:non_interactive: If True, will attempt to connect without user input
        return base64.b64decode(encrypted.encode()).decode()efault), will prompt
    except (TypeError, ValueError) as e:and MFA.
        print(f"Error decrypting password: {e}")t for MFA code when needed.
        return NoneIf False, will not attempt MFA authentication.
    
def connect_to_garmin(non_interactive: bool = False, allow_mfa: bool = True) -> Optional[Garmin]:
    """Connect to Garmin account with login None otherwise
    """
    Args: to load saved credentials first
        non_interactive: If True, will attempt to connect without user input
                        (for automated scripts). If False (default), will prompt
                        for credentials and MFA.ed credentials
        allow_mfa: If True (default), will prompt for MFA code when needed.
                   If False, will not attempt MFA authentication.
            print("Error: Non-interactive mode requires saved credentials")
    Returns:return None
        Garmin client object if successful, None otherwise
    """ username = saved_username
    # Try to load saved credentials first_encrypted_pw)
    saved_username, saved_encrypted_pw = load_saved_credentials()
            print("Error: Failed to decrypt password")
    # For non-interactive mode, we must have saved credentials
    if non_interactive:
        if not saved_username or not saved_encrypted_pw:
            print("Error: Non-interactive mode requires saved credentials")
            return Nonend saved credentials for {saved_username}")
            use_saved = input("Use saved credentials? (y/n): ").strip().lower() == 'y'
        username = saved_usernamename if use_saved else input("Enter your Garmin Connect email: ")
        password = decrypt_password(saved_encrypted_pw)
        if not password::
            print("Error: Failed to decrypt password")ypted_pw)
            return None
    else:       password = getpass.getpass("Enter your Garmin Connect password: ")
        # Interactive mode - ask user for input
        if saved_username:ut("Enter your Garmin Connect email: ") if len(sys.argv) < 2 else sys.argv[1]
            print(f"Found saved credentials for {saved_username}")password: ")
            use_saved = input("Use saved credentials? (y/n): ").strip().lower() == 'y'
            username = saved_username if use_saved else input("Enter your Garmin Connect email: ")
            if input("Save credentials for future use? (y/n): ").strip().lower() == 'y':
            if use_saved:entials(username, password)
                password = decrypt_password(saved_encrypted_pw)
            else:connect to Garmin
                password = getpass.getpass("Enter your Garmin Connect password: ")
        else:("Authenticating with Garmin Connect...")
            username = input("Enter your Garmin Connect email: ") if len(sys.argv) < 2 else sys.argv[1]
            password = getpass.getpass("Enter your Garmin Connect password: ")
            itialize Garmin client
            # Ask if user wants to save credentials
            if input("Save credentials for future use? (y/n): ").strip().lower() == 'y':
                save_credentials(username, password)
        test_mode = os.environ.get('GARMIN_TEST_MODE', 'false').lower() == 'true'
    # Define token store locationget('GARMIN_USE_MFA', 'false').lower() == 'true'
    tokenstore = os.getenv("GARMINTOKENS") or os.path.expanduser("~/.garminconnect")
    
    # Attempt to connect to Garminogin process unless real MFA is specifically requested
    try:    print("Running in test mode. MFA is being mocked.")
        print("Authenticating with Garmin Connect...")login - just pretend it succeeded
        print(f"Username: {username}")d in test mode
        elif allow_mfa:
        try:you will be prompted to enter a code.")
            # Try to login using existing tokens first
            print(f"Trying to login using token data from '{tokenstore}'...")
            garmin = Garmin()    import importlib.util
            garmin.login(tokenstore)om the same directory as this file
            print("Authentication successful using saved tokens!")
            return garminom_email
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
            print("Tokens not found or expired. Logging in with credentials...")path and import
        sys as sys_mod
        # Initialize Garmin client
        if allow_mfa:s_mod.path.dirname(os_mod.path.abspath(__file__))
            garmin = Garmin(email=username, password=password, is_cn=False, return_on_mfa=True)_dir not in sys_mod.path:
            insert(0, src_dir)
            # Check if we're running in test mode
            test_mode = os.environ.get('GARMIN_TEST_MODE', 'false').lower() == 'true'inal_input = builtins.input
            if test_mode:
                print("Running in test mode. MFA is being mocked.")
                return garmin
                _mfa_code_from_email()
            # Try to import email_utils from the same directory as this file
            try:
                from .email_utils import get_latest_mfa_code_from_email
            except (ImportError, SystemError):
                # Fallback: add src directory to sys.path and importease enter manually.")
                src_dir = os.path.dirname(os.path.abspath(__file__))t)
                if src_dir not in sys.path:t
                    sys.path.insert(0, src_dir)
                try:
                    from email_utils import get_latest_mfa_code_from_email
                except ImportError:ut = original_input
                    # If email_utils is still not found, we'll handle MFA manually
                    pass't handle MFA prompts
            ail if MFA is required
            # Try login with possible MFA
            try:
                result1, result2 = garmin.login()
                if result1 == "needs_mfa":  # MFA is requiredif "factor" in str(e).lower() or "mfa" in str(e).lower() or "verification" in str(e).lower():
                    print("MFA code required. Checking email...")"Multi-factor authentication required but disabled.")
                    mfa_code = Noneprint("Enable MFA support with allow_mfa=True or use an app password if available.")
                    
                    # Try to get MFA code from email first   raise  # Re-raise if it's not an MFA-related error
                    try:
                        mfa_code = get_latest_mfa_code_from_email()
                        if mfa_code:c
                            print(f"Auto-filled MFA code: {mfa_code}")r, TimeoutError) as e:
                    except (NameError, ImportError):{e}")
                        pass
                        
                    # If we couldn't get it from email, ask user
                    if not mfa_code:}")
                        mfa_code = input("Enter MFA code from email: ")
                    pt Exception as e:
                    garmin.resume_login(result2, mfa_code)Connect: {e}")
                .print_exc()
                # Save tokens for future use
                garmin.garth.dump(tokenstore) and password are correct")
                print(f"Saved authentication tokens to {tokenstore}")r security")
            except Exception as e:our account might require 2FA (two-factor authentication)")
                print(f"Error during authentication: {e}")MFA, you may need to generate an app password in your Garmin account")
                return None
        else:
            # No MFA allowed, simpler login (will fail if MFA is required)ict[str, Any], date_str: str, export_dir: Path) -> Path:
            try:
                garmin = Garmin(email=username, password=password)
                garmin.login()
            except Exception as e:
                if "factor" in str(e).lower() or "mfa" in str(e).lower() or "verification" in str(e).lower():
                    print("Multi-factor authentication required but disabled.")
                    print("Enable MFA support with allow_mfa=True or use an app password if available.")
                    return None
                raise  # Re-raise if it's not an MFA-related error        Path to the exported CSV file
        
        print("Authentication successful!")
        return garminexport_dir.mkdir(parents=True, exist_ok=True)
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error: {e}")
        print("Check your internet connection and try again.")
        return None
    except ValueError as e:fine the fields we want to export
        print(f"Value error: {e}")lds = [
        return None', 'day_of_week'
    except Exception as e:
        print(f"Error connecting to Garmin Connect: {e}")
        traceback.print_exc()
        print("\nPossible solutions:")    'steps', 'totalDistanceMeters', 'totalKilocalories', 
        print("1. Check that your email and password are correct")ories', 'restingHeartRate', 'maxHeartRate',
        print("2. Garmin might be blocking automated logins for security")ngHeartRate', 'totalSteps', 
        print("3. Your account might require 2FA (two-factor authentication)")    'dailyStepGoal', 'floorsAscended', 'floorsDescended'
        print("4. If using MFA, you may need to generate an app password in your Garmin account")
        return None

def export_to_csv(stats: Dict[str, Any], date_str: str, export_dir: Path) -> Path:ctivity_fields = [
    """Export Garmin stats to a CSV file    'activeSeconds', 'sedentarySeconds', 'highlyActiveSeconds',
    tensityMinutes', 'vigorousIntensityMinutes'
    Args:
        stats: The stats dictionary from Garmin Connect
        date_str: The date string in ISO format (YYYY-MM-DD)
        export_dir: Directory to export to
           'sleepTimeSeconds', 'deepSleepSeconds', 'lightSleepSeconds', 
    Returns:    'remSleepSeconds', 'awakeSleepSeconds', 'sleepingSeconds'
        Path to the exported CSV file
    """
    # Ensure the export directory exists
    export_dir.mkdir(parents=True, exist_ok=True)
       'averageStressLevel', 'maxStressLevel', 'stressQualifier',
    # Use a single CSV file for all dates    'restStressDuration', 'lowStressDuration', 'mediumStressDuration',
    csv_file = export_dir / "garmin_stats.csv"ssPercentage'
    
    # Define the fields we want to export
    date_fields = [
        'date', 'year', 'month', 'day', 'day_of_week'ody_fields = [
    ]    'weightInGrams', 'bmi', 'bodyFatPercentage', 'bodyWater', 'boneMass', 
     'metabolicAge', 'physiqueRating'
    base_fields = [
        'steps', 'totalDistanceMeters', 'totalKilocalories', 
        'activeKilocalories', 'bmrKilocalories', 'restingHeartRate', 'maxHeartRate',
        'minHeartRate', 'lastSevenDaysAvgRestingHeartRate', 'totalSteps', 
        'dailyStepGoal', 'floorsAscended', 'floorsDescended'   'avgWakingRespirationValue', 'latestRespirationValue', 
    ]    'highestRespirationValue', 'lowestRespirationValue'
    
    # Add activity fields
    activity_fields = [
        'activeSeconds', 'sedentarySeconds', 'highlyActiveSeconds',
        'moderateIntensityMinutes', 'vigorousIntensityMinutes'   'averageHrvValue', 'maxHrvValue', 'minHrvValue', 'hrRestingLowHrvValue'
    ]]
    
    # Add sleep fields if availablelds
    sleep_fields = [
        'sleepTimeSeconds', 'deepSleepSeconds', 'lightSleepSeconds', ', 
        'remSleepSeconds', 'awakeSleepSeconds', 'sleepingSeconds'   'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryMostRecentValue'
    ]]
    
    # Add stress fields if availablea if available
    stress_fields = [
        'averageStressLevel', 'maxStressLevel', 'stressQualifier',   'averageSpo2', 'latestSpo2', 'lowestSpo2'
        'restStressDuration', 'lowStressDuration', 'mediumStressDuration',]
        'highStressDuration', 'stressPercentage'
    ]ory for better organization
    
    # Add body measurement fields if available
    body_fields = [   "Base": base_fields,
        'weightInGrams', 'bmi', 'bodyFatPercentage', 'bodyWater', 'boneMass',     "Activity": activity_fields,
        'muscleMass', 'visceralFat', 'metabolicAge', 'physiqueRating'
    ]tress_fields,
    
    # Add respiration fields if available   "Respiration": respiration_fields,
    respiration_fields = [    "HRV": hrv_fields,
        'avgWakingRespirationValue', 'latestRespirationValue', 
        'highestRespirationValue', 'lowestRespirationValue'_fields
    ]
    
    # Add HRV fields if available complete row with all possible fields
    hrv_fields = [ filled by the loop below
        'averageHrvValue', 'maxHrvValue', 'minHrvValue', 'hrRestingLowHrvValue'd_groups.items():
    ]elds)
    
    # Add Body Battery fieldsow with all fields, using blank for missing data
    body_battery_fields = [
        'bodyBatteryChargedValue', 'bodyBatteryDrainedValue', :
        'bodyBatteryHighestValue', 'bodyBatteryLowestValue', 'bodyBatteryMostRecentValue'   row_data[field] = stats.get(field, '')
    ]
    
    # Add SpO2 data if available(csv_file) > 0
    spo2_fields = [
        'averageSpo2', 'latestSpo2', 'lowestSpo2'write the file if it exists but has different columns
    ]# This ensures that changes to our data structure don't result in misaligned columns
     date twice
    # Group fields by category for better organizationry = False
    field_groups = {
        "Date": date_fields,ncoding='utf-8') as f:
        "Base": base_fields,        reader = csv.reader(f)
        "Activity": activity_fields,
        "Sleep": sleep_fields,
        "Stress": stress_fields,            if set(existing_headers) != set(all_fields):
        "Body": body_fields,
        "Respiration": respiration_fields,
        "HRV": hrv_fields,
        "Body Battery": body_battery_fields, if this date already exists in the file
        "SpO2": spo2_fields for row in reader:
    }mn should be date
    ate_entry = True
    # Instead of filtering, create a complete row with all possible fields            break
    all_fields = []  # Will be filled by the loop below
    for category, fields in field_groups.items():
        all_fields.extend(fields)
    
    # Convert stats to a row with all fields, using blank for missing datae_exists else 'w'
    row_data = {}
    for field in all_fields: or we're creating a new file
        row_data[field] = stats.get(field, '')
    ding='utf-8') as f:
    # Write to CSVer(f, fieldnames=all_fields)
    file_exists = csv_file.exists() and os.path.getsize(csv_file) > 0
    der()
    # For consistency, we'll overwrite the file if it exists but has different columnsa)
    # This ensures that changes to our data structure don't result in misaligned columns
    # We also check for duplicate entries by date to avoid adding the same date twice for backup
    duplicate_entry = Falsearchive_dir = export_dir / "archive"
    if file_exists:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:e_dir / f"garmin_stats_{date_str}.csv"
            reader = csv.reader(f)
            try:
                existing_headers = next(reader)w', newline='', encoding='utf-8') as f:
                if set(existing_headers) != set(all_fields):ieldnames=all_fields)
                    # Headers don't match, overwrite the file
                    file_exists = False    writer.writerow(row_data)
                else:
                    # Check if this date already exists in the file)
                    for row in reader:csv_file}")
                        if row and row[0] == date_str:  # First column should be date
                            duplicate_entry = True
                            break-> bool:
            except StopIteration:
                # File is empty
                file_exists = False
    le to backup
    mode = 'a' if file_exists else 'w'    
    
    # Only write if this is a new date or we're creating a new file
    if not duplicate_entry:
        with open(csv_file, mode, newline='', encoding='utf-8') as f:    # Define the Nextcloud path for your data
            writer = csv.DictWriter(f, fieldnames=all_fields)/Garmin Health Data")
            if not file_exists:
                writer.writeheader()try:
            writer.writerow(row_data) Ensure the Nextcloud directory exists
    st_ok=True)
    # Also create a dated archive copy for backup
    archive_dir = export_dir / "archive"py the file to Nextcloud
    archive_dir.mkdir(parents=True, exist_ok=True)th.name
    dated_csv_file = archive_dir / f"garmin_stats_{date_str}.csv" shutil.copy2(file_path, dest_path)
    {dest_path}")
    # Always create a fresh dated file
    with open(dated_csv_file, 'w', newline='', encoding='utf-8') as f:    # Also create a timestamped backup copy
        writer = csv.DictWriter(f, fieldnames=all_fields)today = dt.date.today().isoformat()
        writer.writeheader()stats_backup_{today}.csv"
        writer.writerow(row_data)
    print(f"Created dated backup in Nextcloud: {backup_path}")
    print(f"Exported data to {csv_file}")
    print(f"Archived date-specific data to {dated_csv_file}")
    return csv_file

def backup_data_file(file_path: Path) -> bool:return False
    """Backup a file to Nextcloud
    n], date_str: Optional[str] = None, export: bool = False) -> Optional[Dict[str, Any]]:
    Args:
        file_path: Path to the file to backup
        
    Returns:garmin_client: The Garmin Connect client
        True if successful, False otherwisehe date in ISO format (YYYY-MM-DD), or None for today
    """ export the data to CSV
    # Define the Nextcloud path for your data
    nextcloud_dir = Path("/Users/jay/Nextcloud/Garmin Health Data")
            The stats dictionary if successful, None otherwise
    try:
        # Ensure the Nextcloud directory exists
        nextcloud_dir.mkdir(parents=True, exist_ok=True)    return None
        
        # Copy the file to Nextcloud
        dest_path = nextcloud_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"Backed up file to Nextcloud: {dest_path}")    date_obj = dt.date.today()
        date_str = date_obj.isoformat()
        # Also create a timestamped backup copy
        today = dt.date.today().isoformat()     # Validate date format
        backup_path = nextcloud_dir / f"garmin_stats_backup_{today}.csv"
        shutil.copy2(file_path, backup_path)e_obj = dt.date.fromisoformat(date_str)
        print(f"Created dated backup in Nextcloud: {backup_path}")        date_str = date_obj.isoformat()  # Normalize the format
            except ValueError:
        return True: {date_str}. Please use YYYY-MM-DD format.")
    except Exception as e:
        print(f"Error copying to Nextcloud: {e}")
        return False...")

def get_stats(garmin_client: Optional[Garmin], date_str: Optional[str] = None, export: bool = False) -> Optional[Dict[str, Any]]:ied date
    """Get activity statistics from Garmin Connect for a specific dategarmin_client.get_stats_and_body(date_str)
    
    Args:
        garmin_client: The Garmin Connect clienttr
        date_str: The date in ISO format (YYYY-MM-DD), or None for today
        export: Whether to export the data to CSVnth, day as separate fields for easier analysis
        , month, day = date_str.split('-')
    Returns:
        The stats dictionary if successful, None otherwisestats['month'] = month
    """
    if not garmin_client:
        return None# Add day of week (0=Monday, 6=Sunday)
        
    try:
        # Use today's date if none provided# Display summary stats
        if date_str is None:
            date_obj = dt.date.today()known"))
            date_str = date_obj.isoformat()tats.get("totalDistanceMeters", "unknown"), "meters")
        else:ts.get("totalKilocalories", "unknown"), "kcal")
            # Validate date formatries:", stats.get("activeKilocalories", "unknown"), "kcal")
            try:print("BMR calories:", stats.get("bmrKilocalories", "unknown"), "kcal")
                date_obj = dt.date.fromisoformat(date_str)
                date_str = date_obj.isoformat()  # Normalize the format
            except ValueError:print("\n===== Heart Rate =====")
                print(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")ats.get("restingHeartRate", "unknown"), "bpm")
                return Noneknown"), "bpm") 
            
        print(f"Getting data for {date_str}...")
        
        # Get stats for the specified datewHrvValue"]:
        stats = garmin_client.get_stats_and_body(date_str)
                if not hrv_found:
        # Add date information to the stats dictionary("\n===== Heart Rate Variability =====")
        stats['date'] = date_str
        
        # Also add year, month, day as separate fields for easier analysis
        year, month, day = date_str.split('-')# Sleep data if available
        stats['year'] = yearn stats:
        stats['month'] = month stats.get("sleepTimeSeconds", 0) / 3600
        stats['day'] = day
        on: {sleep_hours:.2f} hours")
        # Add day of week (0=Monday, 6=Sunday)stats.get('deepSleepSeconds', 0) / 3600:.2f} hours")
        stats['day_of_week'] = date_obj.weekday()0) / 3600:.2f} hours")
        s.get('remSleepSeconds', 0) / 3600:.2f} hours")
        # Display summary stats 3600:.2f} hours")
        print(f"\n===== Summary for {date_str} =====")
        print("Steps:", stats.get("steps", "unknown"))
        print("Distance:", stats.get("totalDistanceMeters", "unknown"), "meters")
        print("Calories:", stats.get("totalKilocalories", "unknown"), "kcal")
        print("Active calories:", stats.get("activeKilocalories", "unknown"), "kcal")weightInGrams', 0) / 1000:.2f} kg")
        print("BMR calories:", stats.get("bmrKilocalories", "unknown"), "kcal")
        
        # Heart rate data
        print("\n===== Heart Rate =====")
        print("Resting HR:", stats.get("restingHeartRate", "unknown"), "bpm")
        print("Max HR:", stats.get("maxHeartRate", "unknown"), "bpm")     export_dir = Path(__file__).parent / "exports"
        dictionary for debugging
        # HRV data if available_dir / f"garmin_stats_{date_str}_raw.json"
        hrv_found = Falsencoding="utf-8") as debug_f:
        for hrv_key in ["averageHrvValue", "maxHrvValue", "minHrvValue", "hrRestingLowHrvValue"]:
            if hrv_key in stats:port_dir)
                if not hrv_found:
                    print("\n===== Heart Rate Variability =====")
                    hrv_found = True all data
                print(f"{hrv_key}: {stats.get(hrv_key, 'unknown')}")\nShow all available data? (y/n): ").strip().lower() == 'y':
        
        # Sleep data if available
        if "sleepTimeSeconds" in stats:
            sleep_hours = stats.get("sleepTimeSeconds", 0) / 3600
            print("\n===== Sleep =====")
            print(f"Sleep Duration: {sleep_hours:.2f} hours")
            print(f"Deep Sleep: {stats.get('deepSleepSeconds', 0) / 3600:.2f} hours")ror) as e:
            print(f"Light Sleep: {stats.get('lightSleepSeconds', 0) / 3600:.2f} hours")print(f"Connection error while getting stats: {e}")
            print(f"REM Sleep: {stats.get('remSleepSeconds', 0) / 3600:.2f} hours")
            print(f"Awake Time: {stats.get('awakeSleepSeconds', 0) / 3600:.2f} hours")
        )
        # Body stats if available
        if "weightInGrams" in stats:
            print("\n===== Body Stats =====")print(f"Error getting stats: {e}")
            print(f"Weight: {stats.get('weightInGrams', 0) / 1000:.2f} kg")int_exc()
            print(f"BMI: {stats.get('bmi', 'unknown')}")    return None
            print(f"Body Fat: {stats.get('bodyFatPercentage', 'unknown')}%")
        ate: Optional[str] = None, limit: int = 5) -> None:
        # Export data if requestedctivities from Garmin Connect
        if export:
            export_dir = Path(__file__).parent / "exports"
            # Log the full stats dictionary for debuggingnt: The Garmin Connect client
            debug_json_path = export_dir / f"garmin_stats_{date_str}_raw.json"art date in ISO format (YYYY-MM-DD), or None for recent activities.
            with open(debug_json_path, "w", encoding="utf-8") as debug_f: only activities from this date.
                json.dump(stats, debug_f, indent=2, ensure_ascii=False) of activities to retrieve
            csv_path = export_to_csv(stats, date_str, export_dir)
            backup_data_file(csv_path)    if not garmin_client:
        
        # Ask if user wants to see all data
        if input("\nShow all available data? (y/n): ").strip().lower() == 'y':try:
            print("\n===== All Available Data =====")pecific_date = None
            for key, value in sorted(stats.items()):
                print(f"{key}: {value}")
        ate date format
        return stats
             print(f"Invalid date format: {start_date}. Please use YYYY-MM-DD format.")
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while getting stats: {e}")
        return None# Always get activities from Garmin Connect
    except ValueError as e:print(f"Getting recent activities (max: {limit})...")
        print(f"Value error while getting stats: {e}")client.get_activities(0, limit)
        return None
    except Exception as e:ctivities:
        print(f"Error getting stats: {e}")
        traceback.print_exc()
        return None
ities by date if a specific date was provided
def get_activities(garmin_client: Optional[Garmin], start_date: Optional[str] = None, limit: int = 5) -> None:filtered_activities = activities
    """Get recent activities from Garmin Connect
    
    Args:
        garmin_client: The Garmin Connect client        start_time = activity.get("startTimeLocal", "")
        start_date: The start date in ISO format (YYYY-MM-DD), or None for recent activities.ime and "T" in start_time:
                    If provided, will show only activities from this date.
        limit: Maximum number of activities to retrieve  try:
    """                if activity_date_str == specific_date.isoformat():
    if not garmin_client:
        return
         If date parsing fails, include activity by default
    try:
        specific_date = None
        if start_date:
            try: {specific_date.isoformat()}.")
                specific_date = dt.date.fromisoformat(start_date)  # Validate date format
            except ValueError:d {len(filtered_activities)} activities for date {specific_date.isoformat()}")
                print(f"Invalid date format: {start_date}. Please use YYYY-MM-DD format.")
                return
        enumerate(filtered_activities, 1):
        # Always get activities from Garmin Connect
        print(f"Getting recent activities (max: {limit})...")get("activityName", "Unknown")
        activities = garmin_client.get_activities(0, limit)distance = activity.get("distance", 0)
        ration", 0) / 60  # Convert seconds to minutes
        if not activities:
            print("No activities found for the specified period.")Activity {i}:")
            return
        print(f"Type: {name}")
        # Filter activities by date if a specific date was providedrs")
        filtered_activities = activities
        if specific_date:
            filtered_activities = []
            for activity in activities:
                start_time = activity.get("startTimeLocal", "")
                if start_time and "T" in start_time:if "calories" in activity:
                    activity_date_str = start_time.split("T")[0]tivity.get('calories')} kcal")
                    try:
                        if activity_date_str == specific_date.isoformat():.get("activityId")
                            filtered_activities.append(activity)
                    except:
                        # If date parsing fails, include activity by default    
                        passfrom today
            
            if not filtered_activities:
                print(f"No activities found for date {specific_date.isoformat()}.")art from startTimeLocal (format: YYYY-MM-DDThh:mm:ss.000)
                return
            print(f"Found {len(filtered_activities)} activities for date {specific_date.isoformat()}")            activity_date = start_time.split("T")[0]
            .isoformat()
        print(f"\n===== Recent Activities =====")from_today = (activity_date == today_date)
        for i, activity in enumerate(filtered_activities, 1):
            start_time = activity.get("startTimeLocal", "Unknown")# Automatically download today's activities
            name = activity.get("activityName", "Unknown")
            distance = activity.get("distance", 0)ally downloading today's activity {i} in TCX format...")
            duration = activity.get("duration", 0) / 60  # Convert seconds to minutesctivity_file(garmin_client, activity_id, 'TCX')
            
            print(f"\nActivity {i}:")s, still ask for confirmation
            print(f"Date: {start_time}")m {start_time} in TCX format? (y/n): ").strip().lower()
            print(f"Type: {name}")
            print(f"Distance: {distance:.2f} meters")y_id, 'TCX')
            print(f"Duration: {duration:.2f} minutes")
            
            # Additional stats if availablewhile getting activities: {e}")
            if "averageHR" in activity:
                print(f"Average HR: {activity.get('averageHR')} bpm")
            if "calories" in activity:as e:
                print(f"Calories: {activity.get('calories')} kcal")
            
            activity_id = activity.get("activityId")
            if activity_id:
                print(f"Activity ID: {activity_id}")scheduled task to run the export daily"""
                
                # Check if the activity is from today
                is_from_today = False
                if start_time:
                    # Parse the date part from startTimeLocal (format: YYYY-MM-DDThh:mm:ss.000)aily Export =====")
                    if "T" in start_time:xport of your Garmin data to Nextcloud.")
                        activity_date = start_time.split("T")[0]
                        today_date = dt.date.today().isoformat()    # Create the export directory
                        is_from_today = (activity_date == today_date)
                
                # Automatically download today's activities
                if is_from_today:
                    print(f"Automatically downloading today's activity {i} in TCX format...")ting export functionality...")
                    download_activity_file(garmin_client, activity_id, 'TCX')today = dt.date.today().isoformat()
                else:ue)
                    # For older activities, still ask for confirmation
                    download = input(f"Download activity {i} from {start_time} in TCX format? (y/n): ").strip().lower()# Create a script for the crontab
                    if download == 'y':parent / "daily_export.py"
                        download_activity_file(garmin_client, activity_id, 'TCX')
                 as f:
    except (ConnectionError, TimeoutError) as e:    f.write(f'''#!/usr/bin/env python3
        print(f"Connection error while getting activities: {e}")armin data export
    except ValueError as e:
        print(f"Value error while getting activities: {e}")
    except Exception as e:
        print(f"Error getting activities: {e}")rt datetime
        traceback.print_exc()
er module
def setup_daily_export(garmin_client: Optional[Garmin]) -> None:path.append("{Path(__file__).parent}")
    """Create a scheduled task to run the export daily"""
    if not garmin_client:get_stats
        print("Not connected to Garmin Connect.")
        returndef main():
    n the daily export"""
    print("\n===== Setup Daily Export =====")f"Running daily Garmin Connect export on {{datetime.datetime.now().isoformat()}}")
    print("This will set up a daily automatic export of your Garmin data to Nextcloud.")
        # Connect to Garmin Connect using saved credentials (non-interactive)
    # Create the export directory
    export_dir = Path(__file__).parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)    if client:
    omplete than today's)
    # Export today's data as a test        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    print("Testing export functionality...")_stats(client, yesterday, export=True)
    today = dt.date.today().isoformat()
    get_stats(garmin_client, today, export=True)
        today = datetime.date.today().isoformat()
    # Create a script for the crontab
    script_path = Path(__file__).parent / "daily_export.py"
        print("Failed to connect to Garmin Connect")
    with open(script_path, "w", encoding="utf-8") as f:it(1)
        f.write(f'''#!/usr/bin/env python3
# Auto-generated script for daily Garmin data export

import os
import sys
import datetime

# Add the parent directory to the path to find the downloader module
sys.path.append("{Path(__file__).parent}")
__file__).parent / "logs"
from downloader import connect_to_garmin, get_stats    log_dir.mkdir(parents=True, exist_ok=True)
garmin_export.log"
def main():
    """Run the daily export"""# Create the crontab entry
    print(f"Running daily Garmin Connect export on {{datetime.datetime.now().isoformat()}}")cron_time = "0 9 * * *"  # Run at 9 AM every day
    script_path} >> {log_path} 2>&1'
    # Connect to Garmin Connect using saved credentials (non-interactive)
    client = connect_to_garmin()print("\nTo set up the daily export crontab, you need to run the following command:")
    ll; echo '{cron_entry}') | crontab -")
    if client:
        # Get yesterday's data (more likely to be complete than today's)
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()).strip().lower() == 'y':
        get_stats(client, yesterday, export=True)    try:
        ab -l 2>/dev/null; echo '{cron_entry}') | crontab -")
        # Also get today's dataur data will be exported daily at 9 AM.")
        today = datetime.date.today().isoformat()
        get_stats(client, today, export=True)    except Exception as e:
    else:
        print("Failed to connect to Garmin Connect")crontab -e'")
        sys.exit(1)
script anytime with:")
if __name__ == "__main__":
    main()
''')
    nal[Path]:
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    # Create a unique log file path
    log_dir = Path(__file__).parent / "logs"    activity_id: The activity ID to download
    log_dir.mkdir(parents=True, exist_ok=True)INAL')
    log_path = log_dir / "garmin_export.log"y (defaults to exports/activities if None)
            
    # Create the crontab entry
    cron_time = "0 9 * * *"  # Run at 9 AM every day
    cron_entry = f'{cron_time} {script_path} >> {log_path} 2>&1'
    if not garmin_client:
    print("\nTo set up the daily export crontab, you need to run the following command:")rint("Not connected to Garmin Connect")
    print(f"\n(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -")
    
    # Ask if user wants to set up crontab now
    if input("\nSet up crontab now? (y/n): ").strip().lower() == 'y':
        try:format_enum = None
            os.system(f"(crontab -l 2>/dev/null; echo '{cron_entry}') | crontab -")
            print("\nCrontab set up successfully! Your data will be exported daily at 9 AM.")format_type.upper())
            print(f"Logs will be written to: {log_path}") except AttributeError:
        except Exception as e:id format: {format_type}")
            print(f"\nError setting up crontab: {e}") CSV, ORIGINAL")
            print("You may need to manually add the crontab entry using 'crontab -e'")None
    
    print("\nYou can manually run the export script anytime with:")# Get activity details for filename
    print(f"python3 {script_path}")t.get_activity_details(activity_id)

def download_activity_file(garmin_client: Optional[Garmin], activity_id: str, print(f"Activity ID {activity_id} not found")
                        format_type: str = 'TCX', output_dir: Optional[Path] = None) -> Optional[Path]:
    """Download an activity file in the specified format
    
    Args: paths
        garmin_client: The Garmin Connect clientity.get("activitySummary", activity.get("summaryDTO", {}))
        activity_id: The activity ID to download
        format_type: Format type ('TCX', 'GPX', 'KML', 'CSV', 'ORIGINAL')
        output_dir: Output directory (defaults to exports/activities if None)
        paths where start time might be found
    Returns:
        Path to the downloaded file if successful, None otherwiselocal = summary.get("startTimeLocal", "")
    """elif "startTimeLocal" in activity:
    if not garmin_client:imeLocal", "")
        print("Not connected to Garmin Connect")
        return None
            # Convert YYYY-MM-DDThh:mm:ss.000 to YYYY-MM-DD_hhmmss
    try:_local.replace("T", "_").replace(":", "").split(".")[0]
        # Get valid format type
        format_enum = None
        try:ime.now().strftime("%Y-%m-%d_%H%M%S")
            format_enum = getattr(Garmin.ActivityDownloadFormat, format_type.upper())
        except AttributeError:
            print(f"Invalid format: {format_type}")
            print("Valid formats: TCX, GPX, KML, CSV, ORIGINAL")activityName" in activity:
            return Noneactivity.get("activityName", "").replace(" ", "_")
        
        # Get activity details for filename
        activity = garmin_client.get_activity_details(activity_id)ity_type = "activity"  # Default value
        if not activity:tance(activity["activityType"], dict):
            print(f"Activity ID {activity_id} not found")y")
            return None
        filename
        # Extract activity information for filename
        # For summary, check both activitySummary and summaryDTO paths
        summary = activity.get("activitySummary", activity.get("summaryDTO", {}))
        tart_time_local:
        # Get start time for the filenameappend(start_time_local)
        start_time_local = None
        # Try different paths where start time might be found
        if "startTimeLocal" in summary:
            start_time_local = summary.get("startTimeLocal", "")    filename_parts.append(activity_type)
        elif "startTimeLocal" in activity:
            start_time_local = activity.get("startTimeLocal", "") if available
            if activity_name:
        if start_time_local:activity_name)
            # Convert YYYY-MM-DDThh:mm:ss.000 to YYYY-MM-DD_hhmmss
            start_time_local = start_time_local.replace("T", "_").replace(":", "").split(".")[0]
        else:name_parts.append(str(activity_id))
            # Use current timestamp as fallback
            start_time_local = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        .{format_type.lower()}"
        # Get activity name
        activity_name = None
        if "activityName" in activity:me.replace("/", "_").replace("\\", "_")
            activity_name = activity.get("activityName", "").replace(" ", "_")
            t up output directory
        # Get activity type
        activity_type = "activity"  # Default value/ "exports" / "activities"
        if "activityType" in activity and isinstance(activity["activityType"], dict):
            activity_type = activity["activityType"].get("typeKey", "activity")
        
        # Create sanitized filename
        filename_parts = []
        
        # Always include timestamp
        if start_time_local:
            filename_parts.append(start_time_local)tivity {activity_id} in {format_type} format...")
            at_enum)
        # Add activity type if available
        if activity_type and activity_type != "activity":
            filename_parts.append(activity_type)
                f.write(activity_data)
        # Add activity name if available
        if activity_name:put_path}")
            filename_parts.append(activity_name)return output_path
            
        # Add activity ID for uniqueness
        filename_parts.append(str(activity_id))
            print("Check your internet connection and try again.")
        # Join parts with underscores and add extension
        filename = "_".join(filename_parts) + f".{format_type.lower()}"
        downloading activity: {e}")
        # Replace any invalid charactersrn None
        filename = filename.replace("/", "_").replace("\\", "_")
        while saving activity file: {e}")
        # Set up output directoryprint(f"Check if you have write permissions for {output_dir}")
        if output_dir is None:
            output_dir = Path(__file__).parent / "exports" / "activities"
        
        # Ensure the directory existsrint_exc()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Full path for the fileactivities(garmin_client: Optional[Garmin], format_type: str = 'TCX') -> None:
        output_path = output_dir / filenameoday's activities
        
        # Download the activitywnloads them automatically.
        print(f"Downloading activity {activity_id} in {format_type} format...")
        activity_data = garmin_client.download_activity(activity_id, format_enum)
        
        # Write activity data to fileype ('TCX', 'GPX', 'KML', 'CSV', 'ORIGINAL')
        with open(output_path, "wb") as f:
            f.write(activity_data)    if not garmin_client:
            
        print(f"Activity downloaded to {output_path}")
        return output_path
        
    except ConnectionError as e:print(f"Searching for activities from today ({today_date})...")
        print(f"Connection error while downloading activity: {e}")
        print("Check your internet connection and try again.")o ensure we catch all of today's
        return None
    except ValueError as e: activities = garmin_client.get_activities(0, 10)
        print(f"Value error while downloading activity: {e}")
        return None
    except IOError as e:int("No recent activities found.")
        print(f"I/O error while saving activity file: {e}")        return
        print(f"Check if you have write permissions for {output_dir}")
        return None
    except Exception as e:    todays_activities = []
        print(f"Error downloading activity: {e}")
        traceback.print_exc()    # Prefer local time; fallback to GMT timestamp
        return Noneor activity.get("startTimeGMT")
    if not start_time:
def download_today_activities(garmin_client: Optional[Garmin], format_type: str = 'TCX') -> None:
    """Download all of today's activitiesd datetime formats
     in start_time:
    This is a convenience function that gets today's activities and downloads them automatically.        date_token = start_time.split('T')[0]
    
    Args:tart_time.split()[0]
        garmin_client: The Garmin Connect clientdate:
        format_type: Format type ('TCX', 'GPX', 'KML', 'CSV', 'ORIGINAL')
    """
    if not garmin_client:activity timestamps to see why none match today
        print("Not connected to Garmin Connect"): Activity timestamps:")
        return
    ("startTimeLocal") or activity.get("startTimeGMT")
    today_date = dt.date.today().isoformat()
    print(f"Searching for activities from today ({today_date})...")(f"No activities found for today ({today_date}).")
    
    # Get a larger number of recent activities to ensure we catch all of today's
    try:ivities from today.")
        activities = garmin_client.get_activities(0, 10)
        
        if not activities:vities, 1):
            print("No recent activities found.")
            return
        
        # Filter for today's activities
        todays_activities = []int(f"\nDownloading activity {i}/{len(todays_activities)}: {name}")
        for activity in activities:        download_activity_file(garmin_client, activity_id, format_type)
            # Prefer local time; fallback to GMT timestamp
            start_time = activity.get("startTimeLocal") or activity.get("startTimeGMT")print(f"\nFinished downloading all {len(todays_activities)} activities from today.")
            if not start_time:
                continue
            # Handle both 'T' and space-separated datetime formatsities: {e}")
            if 'T' in start_time:
                date_token = start_time.split('T')[0]t(f"Value error while getting activities: {e}")
            else:
                date_token = start_time.split()[0]
            if date_token == today_date:
                todays_activities.append(activity)
        if not todays_activities:
            # Debug: list all activity timestamps to see why none match todayhow menu of options for Garmin Connect data retrieval"""
            print("Debug: Activity timestamps:")
            for idx, activity in enumerate(activities, start=1):
                ts = activity.get("startTimeLocal") or activity.get("startTimeGMT")
                print(f"  {idx}. {ts}")
            print(f"No activities found for today ({today_date}).")
            return =====")
         stats")
        print(f"Found {len(todays_activities)} activities from today.")        print("2. Get stats for a specific date")
        
        # Download each activity
        for i, activity in enumerate(todays_activities, 1):aily automatic export to Nextcloud")
            activity_id = activity.get("activityId")
            name = activity.get("activityName", "Unknown")"7. Download today's activities automatically")
                print("8. Exit")
            if activity_id:
                print(f"\nDownloading activity {i}/{len(todays_activities)}: {name}")trip()
                download_activity_file(garmin_client, activity_id, format_type)
            
        print(f"\nFinished downloading all {len(todays_activities)} activities from today.")
        
    except (ConnectionError, TimeoutError) as e:ip()
        print(f"Connection error while getting activities: {e}"))
    except ValueError as e:
        print(f"Value error while getting activities: {e}")t("Enter number of activities to retrieve (default: 5): ").strip()
    except Exception as e:    limit = int(limit) if limit.isdigit() else 5
        print(f"Error getting activities: {e}")
        traceback.print_exc()elif choice == "4":
te.today().isoformat()
def show_menu(garmin_client: Optional[Garmin]) -> None: today, export=True)
    """Show menu of options for Garmin Connect data retrieval"""
    if not garmin_client:
        print("Not connected to Garmin Connect.")
        returnnput("Enter activity ID: ").strip()
    RIGINAL): ").strip().upper()
    while True:
        print("\n===== Garmin Connect Data Menu =====")mat to TCX
        print("1. Get today's stats")ty_file(garmin_client, activity_id, format_type)
        print("2. Get stats for a specific date")
        print("3. Get recent activities")
        print("4. Export today's data to CSV and Nextcloud")nput("Enter format type (default: TCX, others: GPX, KML, CSV, ORIGINAL): ").strip().upper()
        print("5. Setup daily automatic export to Nextcloud")
        print("6. Download an activity file") = "TCX"  # Set default format to TCX
        print("7. Download today's activities automatically")pe)
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":choice. Please select 1-8.")
            get_stats(garmin_client)
        elif choice == "2":
            date_str = input("Enter date (YYYY-MM-DD): ").strip())
            get_stats(garmin_client, date_str)
        elif choice == "3":
            limit = input("Enter number of activities to retrieve (default: 5): ").strip()            limit = int(limit) if limit.isdigit() else 5            get_activities(garmin_client, limit=limit)        elif choice == "4":            today = dt.date.today().isoformat()            get_stats(garmin_client, today, export=True)        elif choice == "5":            setup_daily_export(garmin_client)        elif choice == "6":            activity_id = input("Enter activity ID: ").strip()            format_type = input("Enter format type (default: TCX, others: GPX, KML, CSV, ORIGINAL): ").strip().upper()
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

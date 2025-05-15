#!/usr/bin/env python3

"""
Command-line interface for analyzing Garmin workout data with OpenAI.
"""

import argparse
import sys
import json
import datetime as dt
from pathlib import Path
from typing import Optional, Dict, Any, List
import getpass
import os

# Add parent directory to sys.path to allow importing from parent module
sys.path.append(str(Path(__file__).parent.parent))

from garmin_sync import connect_to_garmin, download_activity_file
from utils.openai_integration import OpenAIAnalyzer, get_api_key_from_config, save_api_key_to_config

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze Garmin workout data using OpenAI"
    )
    
    parser.add_argument(
        "--date", "-d",
        help="Date to analyze (YYYY-MM-DD format). Default: today",
        default=dt.date.today().isoformat()
    )
    
    parser.add_argument(
        "--activity-id",
        help="Specific activity ID to analyze",
        default=None
    )
    
    parser.add_argument(
        "--configure", "-c",
        help="Configure OpenAI API key",
        action="store_true"
    )
    
    parser.add_argument(
        "--list-activities", "-l",
        help="List recent activities without analyzing",
        action="store_true"
    )
    
    parser.add_argument(
        "--days", "-n",
        help="Number of days to look back for activities",
        type=int,
        default=7
    )
    
    return parser.parse_args()

def configure_api_key() -> bool:
    """
    Configure OpenAI API key interactively
    
    Returns:
        True if successful, False otherwise
    """
    print("OpenAI API Key Configuration")
    print("-" * 30)
    print("Your API key is stored locally and used to interact with OpenAI's API.")
    print("You can get an API key from: https://platform.openai.com/api-keys")
    
    api_key = getpass.getpass("Enter your OpenAI API key: ")
    if not api_key.strip():
        print("API key cannot be empty.")
        return False
    
    # Test the API key
    analyzer = OpenAIAnalyzer(api_key=api_key)
    if not analyzer.is_ready():
        print("Error initializing OpenAI client with provided key.")
        return False
    
    # Save if valid
    if save_api_key_to_config(api_key):
        print("API key saved successfully!")
        return True
    else:
        print("Error saving API key.")
        return False

def get_formatted_activity_data(garmin_client, activity_id: str) -> Optional[Dict[str, Any]]:
    """
    Get and format activity data for a specific activity
    
    Args:
        garmin_client: Connected Garmin client
        activity_id: Activity ID to fetch
        
    Returns:
        Formatted activity data if successful, None otherwise
    """
    try:
        # Get detailed activity data
        activity_details = garmin_client.get_activity_details(activity_id)
        
        if not activity_details:
            print(f"No details found for activity {activity_id}")
            return None
        
        # Download the TCX file for additional data
        temp_dir = Path(__file__).parent.parent / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        tcx_path = download_activity_file(garmin_client, activity_id, 'TCX', temp_dir)
        
        # Merge data from both sources
        combined_data = activity_details.copy()
        
        # Add date for easier reference
        if "summaryDTO" in combined_data and "startTimeLocal" in combined_data["summaryDTO"]:
            start_time = combined_data["summaryDTO"]["startTimeLocal"]
            if 'T' in start_time:
                combined_data["date"] = start_time.split('T')[0]
            else:
                combined_data["date"] = start_time.split()[0]
        
        return combined_data
        
    except Exception as e:
        print(f"Error getting activity data: {e}")
        return None

def list_recent_activities(garmin_client, days: int = 7) -> List[Dict[str, Any]]:
    """
    List recent activities
    
    Args:
        garmin_client: Connected Garmin client
        days: Number of days to look back
        
    Returns:
        List of activity data dictionaries
    """
    try:
        # Get a larger set of recent activities
        activities = garmin_client.get_activities(0, 20)
        
        if not activities:
            print("No recent activities found.")
            return []
        
        # Filter for activities within the specified number of days
        cutoff_date = dt.date.today() - dt.timedelta(days=days)
        recent_activities = []
        
        for activity in activities:
            # Get the activity date
            start_time = activity.get("startTimeLocal", "") or activity.get("startTimeGMT", "")
            
            if not start_time:
                continue
                
            # Parse the date from the timestamp
            if 'T' in start_time:
                date_str = start_time.split('T')[0]
            else:
                date_str = start_time.split()[0]
                
            try:
                activity_date = dt.date.fromisoformat(date_str)
                if activity_date >= cutoff_date:
                    recent_activities.append(activity)
            except ValueError:
                # Skip activities with invalid dates
                continue
        
        # Print the activities
        if recent_activities:
            print(f"\nFound {len(recent_activities)} activities in the last {days} days:\n")
            print(f"{'ID':<15} {'Date':<12} {'Type':<20} {'Name':<30} {'Duration'}")
            print("-" * 85)
            
            for activity in recent_activities:
                activity_id = activity.get("activityId", "Unknown")
                
                # Get date
                start_time = activity.get("startTimeLocal", "") or activity.get("startTimeGMT", "")
                date_str = "Unknown"
                if start_time:
                    if 'T' in start_time:
                        date_str = start_time.split('T')[0]
                    else:
                        date_str = start_time.split()[0]
                
                # Get type
                activity_type = "Unknown"
                if "activityType" in activity and isinstance(activity["activityType"], dict):
                    activity_type = activity["activityType"].get("typeKey", "Unknown")
                
                # Get name and duration
                name = activity.get("activityName", "Unknown")
                duration_seconds = activity.get("duration", 0)
                duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
                
                print(f"{activity_id:<15} {date_str:<12} {activity_type:<20} {name:<30} {duration}")
            
            print("\nTo analyze a specific activity, use --activity-id <ID>")
        else:
            print(f"No activities found in the last {days} days.")
            
        return recent_activities
            
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while listing activities: {e}")
        return []
    except ValueError as e:
        print(f"Value error while listing activities: {e}")
        return []
    except (KeyError, TypeError) as e:
        print(f"Data format error while listing activities: {e}")
        return []

def analyze_activity(garmin_client, activity_id: str) -> bool:
    """
    Analyze a specific activity using OpenAI
    
    Args:
        garmin_client: Connected Garmin client
        activity_id: Activity ID to analyze
        
    Returns:
        True if successful, False otherwise
    """
    # Get the OpenAI API key
    api_key = get_api_key_from_config()
    if not api_key:
        print("OpenAI API key not configured. Run with --configure to set up your key.")
        return False
    
    # Initialize the OpenAI analyzer
    analyzer = OpenAIAnalyzer(api_key=api_key)
    if not analyzer.is_ready():
        print("Error initializing OpenAI client. Check your API key.")
        return False
    
    print(f"Fetching activity {activity_id} data...")
    activity_data = get_formatted_activity_data(garmin_client, activity_id)
    
    if not activity_data:
        return False
    
    # Format the data for OpenAI
    print("Preparing data for analysis...")
    formatted_data = analyzer.format_workout_data(activity_data)
    
    # Send to OpenAI for analysis
    print("Sending to OpenAI for analysis...")
    analysis = analyzer.analyze_workout(formatted_data)
    
    if not analysis:
        print("Error getting analysis from OpenAI.")
        print("Please check the logs for more information.")
        print("Possible issues:")
        print("1. The model may not be available")
        print("2. Your API key may be invalid")
        print("3. You may have exceeded your quota")
        print("4. There may be a connectivity issue")
        return False
    
    # Save the analysis
    filepath = analyzer.save_analysis(analysis)
    
    # Display the analysis
    print("\n" + "=" * 60)
    print(f"WORKOUT ANALYSIS FOR {formatted_data.get('date', 'UNKNOWN DATE')}")
    print("=" * 60 + "\n")
    print(analysis.get("analysis", "No analysis available"))
    print("\n" + "=" * 60)
    
    if filepath:
        print(f"\nAnalysis saved to: {filepath}")
    
    return True

def analyze_date_activities(garmin_client, date_str: str) -> bool:
    """
    Analyze activities for a specific date
    
    Args:
        garmin_client: Connected Garmin client
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        True if at least one activity was found and analyzed, False otherwise
    """
    try:
        # Validate date format
        dt.date.fromisoformat(date_str)
        
        # Get activities for the specified date
        print(f"Searching for activities on {date_str}...")
        activities = garmin_client.get_activities(0, 10)
        
        if not activities:
            print("No activities found.")
            return False
        
        # Filter for activities on the specified date
        date_activities = []
        for activity in activities:
            # Get the activity date
            start_time = activity.get("startTimeLocal", "") or activity.get("startTimeGMT", "")
            
            if not start_time:
                continue
                
            # Parse the date from the timestamp
            if 'T' in start_time:
                activity_date = start_time.split('T')[0]
            else:
                activity_date = start_time.split()[0]
                
            if activity_date == date_str:
                date_activities.append(activity)
        
        if not date_activities:
            print(f"No activities found for {date_str}.")
            return False
        
        print(f"Found {len(date_activities)} activities for {date_str}.")
        
        # List the activities
        print("\nActivities found:")
        print(f"{'#':<3} {'ID':<15} {'Type':<20} {'Name':<30} {'Duration'}")
        print("-" * 75)
        
        for i, activity in enumerate(date_activities, 1):
            activity_id = activity.get("activityId", "Unknown")
            
            # Get type
            activity_type = "Unknown"
            if "activityType" in activity and isinstance(activity["activityType"], dict):
                activity_type = activity["activityType"].get("typeKey", "Unknown")
            
            # Get name and duration
            name = activity.get("activityName", "Unknown")
            duration_seconds = activity.get("duration", 0)
            duration = f"{duration_seconds // 60}m {duration_seconds % 60}s"
            
            print(f"{i:<3} {activity_id:<15} {activity_type:<20} {name:<30} {duration}")
        
        # Prompt user to select an activity
        if len(date_activities) > 1:
            selection = input(f"\nEnter activity number to analyze (1-{len(date_activities)}), or A for all: ")
            
            if selection.upper() == 'A':
                # Analyze all activities
                success = False
                for activity in date_activities:
                    activity_id = activity.get("activityId")
                    if activity_id:
                        print(f"\nAnalyzing activity {activity_id}...")
                        success = analyze_activity(garmin_client, activity_id) or success
                return success
            else:
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(date_activities):
                        activity_id = date_activities[idx].get("activityId")
                        if activity_id:
                            return analyze_activity(garmin_client, activity_id)
                        else:
                            print("Invalid activity ID")
                            return False
                    else:
                        print("Invalid selection")
                        return False
                except ValueError:
                    print("Invalid selection")
                    return False
        else:
            # Only one activity, analyze it
            activity_id = date_activities[0].get("activityId")
            if activity_id:
                return analyze_activity(garmin_client, activity_id)
            else:
                print("Invalid activity ID")
                return False
                
    except ValueError as e:
        print(f"Invalid date format. Please use YYYY-MM-DD: {e}")
        return False
    except (ConnectionError, TimeoutError) as e:
        print(f"Connection error while analyzing activities: {e}")
        return False
    except (KeyError, TypeError) as e:
        print(f"Data format error while analyzing activities: {e}")
        return False
    except RuntimeError as e:
        print(f"Runtime error while analyzing activities: {e}")
        return False

def main():
    """Main entry point"""
    args = parse_args()
    
    # Handle configuration
    if args.configure:
        configure_api_key()
        return
    
    # Connect to Garmin
    garmin_client = connect_to_garmin(allow_mfa=True)
    if not garmin_client:
        print("Failed to connect to Garmin Connect")
        sys.exit(1)
        
    # List activities only
    if args.list_activities:
        list_recent_activities(garmin_client, args.days)
        return
    
    # Analyze specific activity if provided
    if args.activity_id:
        analyze_activity(garmin_client, args.activity_id)
    else:
        # Analyze activities for the specified date
        analyze_date_activities(garmin_client, args.date)

if __name__ == "__main__":
    main()

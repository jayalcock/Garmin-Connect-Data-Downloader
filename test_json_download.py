#!/usr/bin/env python3
"""
Test script to verify JSON download functionality
"""
import json
from pathlib import Path

def test_json_download():
    """Test that JSON files exist and are valid"""
    result_dir = Path("web_results/health_stats_20250530_134411")
    
    # Check if result directory exists
    if not result_dir.exists():
        print("❌ Result directory does not exist")
        return False
    
    # Look for JSON files
    json_files = list(result_dir.glob("*.json"))
    archive_json_files = []
    
    archive_dir = result_dir / "archive"
    if archive_dir.exists():
        archive_json_files = list(archive_dir.glob("*.json"))
    
    all_json_files = json_files + archive_json_files
    
    if not all_json_files:
        print("❌ No JSON files found")
        return False
    
    print(f"✅ Found {len(all_json_files)} JSON file(s):")
    
    # Validate each JSON file
    for json_file in all_json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for key fields that should be in health data
            key_fields = ['date', 'totalSteps', 'totalKilocalories', 'restingHeartRate']
            missing_fields = [field for field in key_fields if field not in data]
            
            if missing_fields:
                print(f"  ⚠️  {json_file.name}: Missing fields {missing_fields}")
            else:
                print(f"  ✅ {json_file.name}: Valid health data JSON")
                print(f"      Date: {data.get('date', 'Unknown')}")
                print(f"      Steps: {data.get('totalSteps', 'Unknown')}")
                print(f"      Calories: {data.get('totalKilocalories', 'Unknown')}")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ {json_file.name}: Invalid JSON - {e}")
            return False
        except Exception as e:
            print(f"  ❌ {json_file.name}: Error reading file - {e}")
            return False
    
    print("\n✅ JSON download functionality should work correctly!")
    return True

if __name__ == "__main__":
    test_json_download()

#!/usr/bin/env python
import sys
print(f"Python path: {sys.path}")
try:
    from garmin_cli import download_command
    print("Successfully imported download_command from garmin_cli")
    class MockArgs:
        days = 1
        id = None
        format = "ORIGINAL"
    args = MockArgs()
    print("Initialized mock arguments")
    print("Note: Not actually running download_command to avoid login prompt")
except Exception as e:
    print(f"Error importing or initializing: {e}")

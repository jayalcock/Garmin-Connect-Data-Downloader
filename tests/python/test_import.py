#!/usr/bin/env python
import sys
print(f"Python path: {sys.path}")
try:
    import garmin_sync
    print("Successfully imported garmin_sync")
except Exception as e:
    print(f"Error importing garmin_sync: {e}")

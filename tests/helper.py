#!/usr/bin/env python3
# Helper functions for tests

import os
import sys
from pathlib import Path

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Re-export modules for testing
from src import daily_export
# ARCHIVED: This helper referenced the old downloader.py, which is no longer used.
# Please use fixed_downloader.py for any new helpers.

# Function to get the correct module path for patching
def get_module_path(module, name):
    """Get the correct module path for patching, handling module structure differences"""
    return f'{module.__name__}.{name}'

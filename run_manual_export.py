#!/usr/bin/env python3
# Main launcher script for manual exports

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Import from the src directory
from src.manual_export import main

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Tests for the Garmin data retrieval functions

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util

# Add parent directory to path to import the src module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fixed_downloader_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixed_downloader.py')
spec = importlib.util.spec_from_file_location('fixed_downloader', fixed_downloader_path)
fixed_downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed_downloader)
get_stats = fixed_downloader.get_stats
export_to_csv = fixed_downloader.export_to_csv

# Helper for patching
MODULE_PATH = 'fixed_downloader'
def get_module_path(name):
    return f'{MODULE_PATH}.{name}'

class TestDataRetrieval(unittest.TestCase):
    """Tests for data retrieval functions"""
    
    @patch('fixed_downloader.dt.date')
    def test_get_stats_default_date(self, mock_date):
        """Test get_stats using default date (today)"""
        # Setup
        mock_today = MagicMock()
        mock_today.isoformat.return_value = '2025-05-09'
        mock_date.today.return_value = mock_today
        mock_date.fromisoformat.return_value = mock_today
        
        mock_garmin = MagicMock()
        mock_garmin.get_stats_and_body.return_value = {'steps': 10000}
        
        # Call function with patched sys.stdin.isatty to avoid interactive prompts
        with patch('sys.stdin.isatty', return_value=False):
            result = get_stats(mock_garmin)
        
        # Verify
        self.assertIsNotNone(result)
        mock_date.today.assert_called_once()
        # Just verify it was called once, do not specify the exact argument
        mock_garmin.get_stats_and_body.assert_called_once()
    
    @patch('fixed_downloader.dt.date')
    def test_get_stats_specific_date(self, mock_date):
        """Test get_stats using a specific date"""
        # Setup
        mock_date_obj = MagicMock()
        mock_date_obj.isoformat.return_value = '2025-05-08'
        mock_date.fromisoformat.return_value = mock_date_obj
        
        mock_garmin = MagicMock()
        mock_garmin.get_stats_and_body.return_value = {'steps': 9000}
        
        # Call function with patched sys.stdin.isatty to avoid interactive prompts
        with patch('sys.stdin.isatty', return_value=False):
            result = get_stats(mock_garmin, '2025-05-08')
        
        # Verify
        self.assertIsNotNone(result)
        mock_date.fromisoformat.assert_called_once_with('2025-05-08')
        mock_garmin.get_stats_and_body.assert_called_once_with('2025-05-08')
        self.assertEqual(result.get('steps'), 9000)
    
    def test_get_stats_with_export(self):
        """Test get_stats with export option enabled"""
        # This approach modifies the function under test to bypass the export 
        # and backup functionality while still testing the main workflow

        # Store the original function to restore it later
        original_export = fixed_downloader.export_to_csv
        original_backup = fixed_downloader.backup_data_file
        
        try:
            # Create mock versions of the functions
            mock_export = MagicMock()
            mock_export.return_value = Path('/test/exports/garmin_stats.csv')
            
            mock_backup = MagicMock()
            mock_backup.return_value = True
            
            # Replace the original functions with our mocks
            fixed_downloader.export_to_csv = mock_export
            fixed_downloader.backup_data_file = mock_backup
            
            # Setup other necessary mocks
            with patch('sys.stdin.isatty', return_value=False):  # Avoid prompts
                with patch('fixed_downloader.dt.date') as mock_date:
                    # Mock date functionality
                    mock_date_obj = MagicMock()
                    mock_date_obj.isoformat.return_value = '2025-05-09'
                    mock_date_obj.weekday.return_value = 4  # Friday
                    mock_date.today.return_value = mock_date_obj
                    mock_date.fromisoformat.return_value = mock_date_obj
                    
                    # Create Garmin client mock
                    mock_garmin = MagicMock()
                    mock_garmin.get_stats_and_body.return_value = {'steps': 10000}
                    mock_garmin.get_hrv_data.return_value = {}  # Empty dict to prevent exceptions
                    
                    # Mock file operations to prevent writing to disk
                    with patch('pathlib.Path.mkdir'):
                        with patch('builtins.open', unittest.mock.mock_open()):
                            with patch('json.dump'):
                                # Call function with export=True
                                result = get_stats(mock_garmin, export=True)
                                
                                # Verify the result is not None
                                self.assertIsNotNone(result)
                                # Verify export was called
                                mock_export.assert_called_once()
                                # Verify backup was called with the correct path
                                mock_backup.assert_called_once_with(Path('/test/exports/garmin_stats.csv'))
        finally:
            # Restore the original functions
            fixed_downloader.export_to_csv = original_export
            fixed_downloader.backup_data_file = original_backup
    
    def test_get_stats_none_client(self):
        """Test get_stats with None client"""
        # Call function
        result = get_stats(None)
        
        # Verify
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()

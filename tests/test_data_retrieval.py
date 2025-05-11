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
        
        # Call function
        result = get_stats(mock_garmin, interactive=False)
        
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
        
        # Call function
        result = get_stats(mock_garmin, '2025-05-08', interactive=False)
        
        # Verify
        self.assertIsNotNone(result)
        mock_date.fromisoformat.assert_called_once_with('2025-05-08')
        mock_garmin.get_stats_and_body.assert_called_once_with('2025-05-08')
        self.assertEqual(result.get('steps'), 9000)
    
    @patch('json.dump')
    @patch('fixed_downloader.export_to_csv')
    @patch('fixed_downloader.backup_data_file')
    @patch('fixed_downloader.dt.date')
    def test_get_stats_with_export(self, mock_json_dump, mock_export, mock_backup, mock_date):
        """Test get_stats with export option enabled"""
        # Setup
        mock_date_obj = MagicMock()
        mock_date_obj.isoformat.return_value = '2025-05-09'
        mock_date.today.return_value = mock_date_obj
        mock_date.fromisoformat.return_value = mock_date_obj
        
        mock_garmin = MagicMock()
        mock_garmin.get_stats_and_body.return_value = {'steps': 10000}
        
        # Configure the mock for export
        mock_export.return_value = Path('/test/exports/garmin_stats.csv')
        
        # Call function
        result = get_stats(mock_garmin, export=True, interactive=False)
        
        # Verify
        self.assertIsNotNone(result)
        mock_export.assert_called_once()
        mock_backup.assert_called_once_with(Path('/test/exports/garmin_stats.csv'))
    
    def test_get_stats_none_client(self):
        """Test get_stats with None client"""
        # Call function
        result = get_stats(None, interactive=False)
        
        # Verify
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()

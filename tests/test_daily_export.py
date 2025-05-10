#!/usr/bin/env python3
# Tests for the daily export script

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import daily_export

class TestDailyExport(unittest.TestCase):
    """Tests for daily export script"""
    
    @patch('sys.exit')
    @patch('json.dump')
    @patch('daily_export.Path.mkdir')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('daily_export.decrypt_password')
    @patch('daily_export.load_saved_credentials')
    @patch('daily_export.send_notification')
    @patch('daily_export.get_stats')
    @patch('daily_export.connect_to_garmin')
    def test_daily_export_success(self, mock_connect, mock_get_stats, mock_notify, 
                                  mock_load_creds, mock_decrypt, mock_open, 
                                  mock_mkdir, mock_json_dump, mock_exit):
        """Test successful daily export"""
        # Setup mocks
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        # Mock successful retrieval of data for both yesterday and today
        mock_get_stats.side_effect = [{'steps': 9000}, {'steps': 10000}]
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        mock_connect.assert_called_once_with(non_interactive=True)
        self.assertEqual(mock_get_stats.call_count, 2)
        mock_notify.assert_called_once()
        mock_exit.assert_called_once_with(0)
    
    @patch('sys.exit')
    @patch('json.dump')
    @patch('daily_export.Path.mkdir')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('daily_export.decrypt_password')
    @patch('daily_export.load_saved_credentials')
    @patch('daily_export.send_notification')
    @patch('daily_export.connect_to_garmin')
    def test_daily_export_connection_failure(self, mock_connect, mock_notify, 
                                          mock_load_creds, mock_decrypt, mock_open, 
                                          mock_mkdir, mock_json_dump, mock_exit):
        """Test daily export with connection failure"""
        # Setup mocks
        mock_connect.return_value = None  # Connection fails
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        mock_connect.assert_called_once_with(non_interactive=True)
        mock_notify.assert_called_once()
        # Check that the notification message indicates failure
        self.assertIn('fail', mock_notify.call_args[0][0].lower())
        mock_exit.assert_called_once_with(1)
    
    @patch('sys.exit')
    @patch('json.dump')
    @patch('daily_export.Path.mkdir')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('daily_export.decrypt_password')
    @patch('daily_export.load_saved_credentials')
    @patch('daily_export.send_notification')
    @patch('daily_export.get_stats')
    @patch('daily_export.connect_to_garmin')
    def test_daily_export_data_failure(self, mock_connect, mock_get_stats, mock_notify, 
                                    mock_load_creds, mock_decrypt, mock_open, 
                                    mock_mkdir, mock_json_dump, mock_exit):
        """Test daily export with data retrieval failure"""
        # Setup mocks
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        # Mock failed retrieval of data
        mock_get_stats.side_effect = [None, None]  # Both yesterday and today fail
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        mock_connect.assert_called_once_with(non_interactive=True)
        self.assertEqual(mock_get_stats.call_count, 2)
        mock_notify.assert_called_once()
        # Check that the notification message indicates failure
        self.assertIn('error', mock_notify.call_args[0][0].lower())
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

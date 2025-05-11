#!/usr/bin/env python3
# Tests for the daily export script

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Robust import of daily_export
import importlib.util

daily_export_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'daily_export.py')
spec = importlib.util.spec_from_file_location('daily_export', daily_export_path)
daily_export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_export)

# Helper function to get the correct module path for patching
MODULE_PATH = 'daily_export'
def get_module_path(name):
    return f'{MODULE_PATH}.{name}'

class TestDailyExport(unittest.TestCase):
    """Tests for daily export script"""
    
    @patch('sys.exit')
    @patch(get_module_path('download_specific_dates'))
    @patch(get_module_path('send_notification'))
    @patch(get_module_path('decrypt_password'))
    @patch(get_module_path('load_saved_credentials'))
    @patch(get_module_path('connect_to_garmin'))
    def test_daily_export_success(self, mock_connect, mock_load_creds, mock_decrypt, 
                                 mock_notify, mock_download_dates, mock_exit):
        """Test successful daily export"""
        # Setup mocks
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        # Mock successful retrieval of data for multiple dates
        mock_download_dates.return_value = ['2025-05-09', '2025-05-10']
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        mock_connect.assert_called_once_with(non_interactive=True, allow_mfa=False)
        mock_download_dates.assert_called_once()
        mock_notify.assert_called_once()
        mock_exit.assert_not_called()  # Since we've mocked sys.exit, it might not be called
    
    @patch('sys.exit')
    @patch(get_module_path('send_notification'))
    @patch(get_module_path('decrypt_password'))
    @patch(get_module_path('load_saved_credentials'))
    @patch(get_module_path('connect_to_garmin'))
    def test_daily_export_connection_failure(self, mock_connect, mock_load_creds, 
                                           mock_decrypt, mock_notify, mock_exit):
        """Test daily export with connection failure"""
        # Setup mocks
        mock_connect.return_value = None  # Connection fails
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        # We expect 3 calls due to retry logic
        self.assertEqual(mock_connect.call_count, 3)
        expected_args = {'non_interactive': True, 'allow_mfa': False}
        for call_args in mock_connect.call_args_list:
            self.assertEqual(call_args.kwargs, expected_args)
        
        # Check that at least one notification had "fail" in it
        any_failure_notification = False
        for call in mock_notify.call_args_list:
            if 'fail' in call[0][0].lower():
                any_failure_notification = True
                break
        
        self.assertTrue(any_failure_notification, "Expected at least one notification with 'fail' in it")
        mock_exit.assert_called_once_with(1)
    
    @patch('sys.exit')
    @patch(get_module_path('download_specific_dates'))
    @patch(get_module_path('send_notification'))
    @patch(get_module_path('decrypt_password'))
    @patch(get_module_path('load_saved_credentials'))
    @patch(get_module_path('connect_to_garmin'))
    def test_daily_export_data_failure(self, mock_connect, mock_load_creds, mock_decrypt,
                                      mock_notify, mock_download_dates, mock_exit):
        """Test daily export with data retrieval failure"""
        # Setup mocks
        mock_client = MagicMock()
        mock_connect.return_value = mock_client
        # Mock failed retrieval of data - empty list means no dates were downloaded
        mock_download_dates.return_value = []
        # Mock credentials
        mock_load_creds.return_value = ('test@example.com', 'encrypted_password')
        mock_decrypt.return_value = 'password'
        
        # Call main function
        daily_export.main()
        
        # Verify
        mock_connect.assert_called_once_with(non_interactive=True, allow_mfa=False)
        mock_download_dates.assert_called_once()
        mock_notify.assert_called_once()
        # Check that the notification message indicates warning
        self.assertIn('warning', mock_notify.call_args[0][0].lower(), "Expected 'warning' in notification message")
        mock_exit.assert_not_called()  # No exit on warning


if __name__ == "__main__":
    unittest.main()

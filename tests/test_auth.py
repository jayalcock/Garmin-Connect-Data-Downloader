#!/usr/bin/env python3
# Tests for the Garmin authentication functions

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory and src directory to path to import the downloader module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.downloader import connect_to_garmin, load_saved_credentials, save_credentials

class TestAuthentication(unittest.TestCase):
    """Tests for Garmin Connect authentication functions"""
    
    def setUp(self):
        """Set up test environment"""
        # Make sure GARMIN_TEST_MODE is set for all tests by default
        self.env_patcher = patch.dict('os.environ', {'GARMIN_TEST_MODE': 'true'})
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    @patch('downloader.load_saved_credentials')
    @patch('getpass.getpass')
    @patch('builtins.input')
    @patch('downloader.Garmin')
    def test_connect_interactive_with_saved_creds(self, mock_garmin, mock_input, mock_getpass, mock_load_creds):
        """Test connecting to Garmin interactively with saved credentials"""
        # Setup mocks
        mock_load_creds.return_value = ('test@example.com', 'base64_password')
        mock_input.side_effect = ['y']  # Use saved credentials
        mock_decrypt = patch('downloader.decrypt_password', return_value='password')
        mock_decrypt.start()
        mock_garmin_instance = MagicMock()
        mock_garmin.return_value = mock_garmin_instance
        
        # Call function
        result = connect_to_garmin(non_interactive=False, allow_mfa=True)
        
        # Clean up mock
        mock_decrypt.stop()
        
        # Verify
        mock_load_creds.assert_called_once()
        mock_garmin.assert_called_once()
        # In test mode, login is not called
        self.assertEqual(result, mock_garmin_instance)
        
    @patch('downloader.load_saved_credentials')
    @patch('getpass.getpass')
    @patch('builtins.input')
    @patch('downloader.save_credentials')
    @patch('downloader.Garmin')
    def test_connect_interactive_new_creds(self, mock_garmin, mock_save, mock_input, mock_getpass, mock_load_creds):
        """Test connecting to Garmin interactively with new credentials"""
        # Setup mocks
        mock_load_creds.return_value = (None, None)  # No saved credentials
        mock_input.side_effect = ['test@example.com', 'y']  # Enter email, save creds
        mock_getpass.return_value = 'testpassword'
        mock_garmin_instance = MagicMock()
        mock_garmin.return_value = mock_garmin_instance
        
        # Call function
        result = connect_to_garmin(non_interactive=False, allow_mfa=True)
        
        # Verify
        mock_load_creds.assert_called_once()
        mock_garmin.assert_called_once()
        mock_save.assert_called_once()
        # In test mode, login is not called
        self.assertEqual(result, mock_garmin_instance)
    
    @patch('downloader.load_saved_credentials')
    @patch('downloader.decrypt_password')
    @patch('downloader.Garmin')
    def test_connect_non_interactive(self, mock_garmin, mock_decrypt, mock_load_creds):
        """Test connecting to Garmin in non-interactive mode"""
        # Setup mocks
        mock_load_creds.return_value = ('test@example.com', 'base64_password')
        mock_decrypt.return_value = 'actual_password'
        mock_garmin_instance = MagicMock()
        mock_garmin.return_value = mock_garmin_instance
        
        # Call function
        result = connect_to_garmin(non_interactive=True)
        
        # Verify
        mock_load_creds.assert_called_once()
        mock_decrypt.assert_called_once_with('base64_password')
        mock_garmin.assert_called_once_with('test@example.com', 'actual_password')
        # In test mode, login is not called
        self.assertEqual(result, mock_garmin_instance)
    
    @patch('downloader.load_saved_credentials')
    def test_connect_non_interactive_no_creds(self, mock_load_creds):
        """Test connecting non-interactively with no saved credentials"""
        # Setup mocks
        mock_load_creds.return_value = (None, None)
        
        # Call function
        result = connect_to_garmin(non_interactive=True)
        
        # Verify
        mock_load_creds.assert_called_once()
        self.assertIsNone(result)
        
    @patch('downloader.Garmin')
    def test_connect_login_exception(self, mock_garmin):
        """Test handling a login exception"""
        # For this test, disable test mode to trigger the real login flow
        with patch.dict('os.environ', {'GARMIN_TEST_MODE': 'false'}):
            # Setup mock to raise exception on login
            mock_garmin_instance = MagicMock()
            mock_garmin_instance.login.side_effect = Exception("Test login error")
            mock_garmin.return_value = mock_garmin_instance
            
            # Use a context manager to patch multiple functions
            with patch('downloader.load_saved_credentials') as mock_load_creds, \
                 patch('getpass.getpass') as mock_getpass, \
                 patch('builtins.input') as mock_input:
                
                # Setup remaining mocks
                mock_load_creds.return_value = (None, None)
                mock_input.side_effect = ['test@example.com', 'n']  # Email, don't save
                mock_getpass.return_value = 'password'
                
                # Call function
                result = connect_to_garmin(non_interactive=False)
            
            # Verify
            mock_garmin.assert_called_once()
            mock_garmin_instance.login.assert_called_once()
            self.assertIsNone(result)
    
    @patch('downloader.Garmin')
    @patch('downloader.load_saved_credentials')
    @patch('downloader.decrypt_password')
    def test_connect_test_mode_vs_real_mode(self, mock_decrypt, mock_load_creds, mock_garmin):
        """Test connecting in test mode vs real mode"""
        # Setup common mocks
        mock_load_creds.return_value = ('test@example.com', 'base64_password')
        mock_decrypt.return_value = 'actual_password'
        mock_garmin_instance = MagicMock()
        mock_garmin.return_value = mock_garmin_instance
        
        # Test 1: With test mode ON
        with patch.dict('os.environ', {'GARMIN_TEST_MODE': 'true'}):
            connect_to_garmin(non_interactive=True)
            # In test mode, login should NOT be called
            mock_garmin_instance.login.assert_not_called()
        
        # Reset the mock
        mock_garmin_instance.reset_mock()
        
        # Test 2: With test mode OFF
        with patch.dict('os.environ', {'GARMIN_TEST_MODE': 'false'}):
            connect_to_garmin(non_interactive=True)
            # In real mode, login should be called
            mock_garmin_instance.login.assert_called_once()


if __name__ == "__main__":
    unittest.main()

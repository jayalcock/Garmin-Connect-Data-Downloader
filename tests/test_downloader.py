#!/usr/bin/env python3
# Tests for the Garmin data downloader

import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import base64
from pathlib import Path

# Add parent directory to path to import the downloader module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.downloader import (
    load_saved_credentials, 
    save_credentials, 
    decrypt_password,
    export_to_csv,
    copy_to_icloud
)

class TestCredentialFunctions(unittest.TestCase):
    """Tests for credential-related functions"""
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"username": "test@example.com", "encrypted_password": "dGVzdHBhc3N3b3Jk"}')
    def test_load_saved_credentials_success(self, mock_file, mock_exists):
        """Test loading credentials when the file exists and is valid"""
        mock_exists.return_value = True
        
        username, encrypted_pw = load_saved_credentials()
        
        self.assertEqual(username, "test@example.com")
        self.assertEqual(encrypted_pw, "dGVzdHBhc3N3b3Jk")
    
    @patch('pathlib.Path.exists')
    def test_load_saved_credentials_no_file(self, mock_exists):
        """Test loading credentials when the file doesn't exist"""
        mock_exists.return_value = False
        
        username, encrypted_pw = load_saved_credentials()
        
        self.assertIsNone(username)
        self.assertIsNone(encrypted_pw)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_saved_credentials_invalid_json(self, mock_file, mock_exists):
        """Test loading credentials when the file contains invalid JSON"""
        mock_exists.return_value = True
        
        username, encrypted_pw = load_saved_credentials()
        
        self.assertIsNone(username)
        self.assertIsNone(encrypted_pw)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.chmod')
    def test_save_credentials(self, mock_chmod, mock_file):
        """Test saving credentials to a file"""
        save_credentials("test@example.com", "testpassword")
        
        # Verify the file was opened for writing
        mock_file.assert_called_once()
        handle = mock_file()
        
        # In the real implementation, json.dump is called, which writes multiple chunks to the file
        # So we can't assert it was called just once, instead we check if it was called
        self.assertTrue(handle.write.called)
        
        # Mock file doesn't actually write data, so we need to check differently
        mock_chmod.assert_called_once()
    
    def test_decrypt_password(self):
        """Test decrypting a base64 encoded password"""
        # "testpassword" in base64
        encrypted = "dGVzdHBhc3N3b3Jk" 
        
        decrypted = decrypt_password(encrypted)
        
        self.assertEqual(decrypted, "testpassword")
    
    def test_decrypt_password_none(self):
        """Test decrypting None returns None"""
        self.assertIsNone(decrypt_password(None))
    
    def test_decrypt_password_invalid(self):
        """Test decrypting an invalid base64 string"""
        self.assertIsNone(decrypt_password("not-valid-base64!"))


class TestExportFunctions(unittest.TestCase):
    """Tests for export-related functions"""
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_export_to_csv_new_file(self, mock_exists, mock_file, mock_mkdir):
        """Test exporting data to a new CSV file"""
        # Setup
        mock_exists.return_value = False
        test_stats = {
            "steps": 10000,
            "totalDistanceMeters": 8000,
            "totalKilocalories": 2500,
            "restingHeartRate": 60
        }
        test_date = "2025-05-09"
        export_dir = Path("/test/exports")
        
        # Execute
        result = export_to_csv(test_stats, test_date, export_dir)
        
        # Verify
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()
        self.assertEqual(result, export_dir / "garmin_stats.csv")
    
    @patch('shutil.copy2')
    @patch('pathlib.Path.mkdir')
    def test_copy_to_icloud(self, mock_mkdir, mock_copy):
        """Test copying a file to iCloud Drive"""
        # Setup
        test_file = Path("/test/exports/garmin_stats.csv")
        
        # Execute
        result = copy_to_icloud(test_file)
        
        # Verify
        mock_mkdir.assert_called_once()
        # We now expect two calls to copy2 - one for the file, one for the backup
        self.assertEqual(2, mock_copy.call_count)
        self.assertTrue(result)
    
    @patch('shutil.copy2')
    @patch('pathlib.Path.mkdir')
    def test_copy_to_icloud_exception(self, mock_mkdir, mock_copy):
        """Test handling an exception when copying to iCloud"""
        # Setup
        test_file = Path("/test/exports/garmin_stats.csv")
        mock_copy.side_effect = Exception("Test error")
        
        # Execute
        result = copy_to_icloud(test_file)
        
        # Verify
        mock_mkdir.assert_called_once()
        mock_copy.assert_called_once()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

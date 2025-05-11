#!/usr/bin/env python3
"""
Test authentication with MFA for Garmin Connect
This script will help you test whether MFA is required for your account
and whether app passwords or other methods might work.
"""

import os

# Use fixed_downloader.py for MFA/auth tests
import importlib.util
fixed_downloader_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixed_downloader.py')
spec = importlib.util.spec_from_file_location('fixed_downloader', fixed_downloader_path)
fixed_downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed_downloader)
connect_to_garmin = fixed_downloader.connect_to_garmin

def test_mfa_auth():
    """Test different authentication methods with Garmin Connect"""
    print("=" * 60)
    print("GARMIN CONNECT MFA AUTHENTICATION TEST")
    print("=" * 60)
    print("\nThis script will test different authentication methods:")
    print("1. Standard login with MFA enabled")
    print("2. Login with MFA disabled (for testing app passwords)")
    print("\nTest 1: Standard login with MFA support")
    print("-" * 40)
    
    # First test: Standard login with MFA enabled
    print("Attempting login with MFA support enabled...")
    client1 = connect_to_garmin(non_interactive=False, allow_mfa=True)
    
    if client1:
        print("\n✅ SUCCESS: Successfully logged in with MFA support enabled.")
        print("This means your credentials are valid and you were able to complete MFA if required.")
    else:
        print("\n❌ FAILURE: Failed to login with MFA support enabled.")
        print("This could indicate invalid credentials or issues with the Garmin API.")
    
    print("\nTest 2: Login with MFA disabled (for app passwords)")
    print("-" * 40)
    
    # Second test: Login without MFA support
    print("Attempting login with MFA support disabled...")
    print("NOTE: This should succeed if you're using an app-specific password")
    print("      or if your account doesn't require MFA.")
    client2 = connect_to_garmin(non_interactive=False, allow_mfa=False)
    
    if client2:
        print("\n✅ SUCCESS: Successfully logged in without MFA support!")
        print("This means:")
        print("1. Either your account doesn't require MFA, or")
        print("2. You're using an app-specific password that bypasses MFA")
        print("\nYou should be able to use daily automated exports!")
    else:
        print("\n❌ FAILURE: Failed to login without MFA support.")
        print("This means MFA is required for your account.")
        print("\nYou have these options:")
        print("1. Use manual_export.py which will prompt for MFA codes")
        print("2. Check if Garmin allows app-specific passwords (see APP_PASSWORD_GUIDE.md)")
        print("3. Apply for API access from Garmin if you need fully automated exports")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_mfa_auth()

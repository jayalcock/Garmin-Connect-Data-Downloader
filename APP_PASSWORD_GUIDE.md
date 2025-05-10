# Setting Up App Passwords for Garmin Connect

## Why App Passwords?

Garmin Connect requires Multi-Factor Authentication (MFA) for security, which prevents automatic scripts from logging in. An app password, if available, would allow your script to authenticate without MFA.

## Instructions

1. **Log in to your Garmin Connect account** in a web browser at [connect.garmin.com](https://connect.garmin.com/)

2. **Navigate to Account Settings**:
   - Click on your profile icon in the top-right corner
   - Select "Settings" or "Account Settings"
   - Look for "Security" or "Account Security" section

3. **Look for "App Passwords" or similar option**:
   - This may be under "Security" or "Connected Apps" sections
   - If you find this option, you can create a new app password specifically for your export script

4. **Create a new App Password**:
   - Name it something like "Data Export Script"
   - Copy the generated password (you'll usually only see it once)

5. **Update your script**:
   - Save this app password in your `.garmin_config.json` file instead of your normal password

If you don't see an App Password option, Garmin Connect may not support this feature for your account type.

## Alternative: Apply for API Access

If you're serious about automating data collection from Garmin, you might want to apply for official API access through their developer program:

1. Visit [Garmin Developer Program](https://developer.garmin.com/)
2. Look for the "Connect IQ" or "Health API" options
3. Register as a developer and apply for API access
4. If approved, you'll receive API keys that can be used without MFA

## MFA Support Options

Our scripts now have several ways to handle MFA:

1. **manual_export.py**: Supports interactive MFA code entry when requested
2. **daily_export.py**: Attempts to connect without MFA (works with app passwords)
3. **test_mfa.py**: Tests both authentication methods to help identify what works for your account

## Testing Your Authentication Options

To determine the best option for your account, run:

```
python test_mfa.py
```

This will test both authentication methods and recommend the best approach for your account.

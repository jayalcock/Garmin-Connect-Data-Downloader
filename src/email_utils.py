import imaplib
import email
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import time

def get_latest_mfa_code_from_email() -> Optional[str]:
    """
    Connects to the user's email via IMAP and retrieves the latest 6-digit MFA code
    from a Garmin security email. Requires a config file ~/.garmin_email_config.json with:
    {
        "imap_server": "imap.mail.me.com",
        "imap_port": 993,
        "email": "your@email.com",
        "password": "your-app-password",
        "sender": "alerts@account.garmin.com",
        "subject": "Your Security Passcode"
    }
    """
    # Wait 15 seconds to allow the MFA email to arrive
    time.sleep(10)
    config_path = Path.home() / '.garmin_email_config.json'
    if not config_path.exists():
        print("No email config found at ~/.garmin_email_config.json")
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"Loaded email config: {config}")  # Debug print
    required_keys = ["imap_server", "imap_port", "email", "password", "sender", "subject"]
    for key in required_keys:
        if key not in config:
            print(f"Missing required config key: {key}")
            return None
    try:
        mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        mail.login(config['email'], config['password'])
        mail.select('inbox')
        date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE {date} FROM "{config["sender"]}" SUBJECT "{config["subject"]}")'
        result, data = mail.search(None, search_criteria)
        if result != 'OK' or not data or not data[0]:
            mail.logout()
            return None
        latest_id = data[0].split()[-1]
        result, msg_data = mail.fetch(latest_id, '(RFC822)')
        if result != 'OK':
            mail.logout()
            return None
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        # Unified text extraction: iterate plain-text parts, decode bytes or fallback to str
        body = ""
        parts = msg.walk() if msg.is_multipart() else [msg]
        for part in parts:
            if part.get_content_type() != 'text/plain':
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            try:
                text = payload.decode('utf-8', errors='ignore')
            except (AttributeError, UnicodeDecodeError):
                text = str(payload)
            body += text
        # Continue with code search and logout
        match = re.search(r'\b\d{6}\b', body)
        mail.logout()
        if match:
            return match.group(0)
        return None
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
        return None
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Config error: {e}")
        return None
    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error: {e}")
        return None

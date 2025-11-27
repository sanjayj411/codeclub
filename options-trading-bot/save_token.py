#!/usr/bin/env python3.9
"""
Save Schwab OAuth Token
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app_key = os.getenv("SCHWAB_APP_KEY")
app_secret = os.getenv("SCHWAB_SECRET")

if not app_key or not app_secret:
    print("Missing credentials in .env")
    sys.exit(1)

print("\n" + "=" * 80)
print("SAVE SCHWAB OAUTH TOKEN")
print("=" * 80)

print("\nFirst, run this to get the authorization URL:")
print("  python3.9 get_auth_url.py")

auth_code = input("\nEnter authorization code from redirect URL: ").strip()

if not auth_code:
    print("No code provided")
    sys.exit(1)

print("\nExchanging authorization code for token...")

payload = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "client_id": app_key,
    "client_secret": app_secret,
    "redirect_uri": "http://localhost:8001/callback"
}

try:
    response = requests.post(
        "https://api.schwabapi.com/v1/oauth/token",
        data=payload
    )
    
    if response.status_code == 200:
        token_data = response.json()
        token_data['expires_at'] = (
            datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
        ).isoformat()
        
        token_path = Path("./tokens/schwabToken.json")
        token_path.parent.mkdir(exist_ok=True)
        
        with open(token_path, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        print(f"\nToken saved successfully!")
        print(f"Location: {token_path}")
        print(f"\nYou can now run:")
        print(f"  python3.9 test_schwab_api.py")
        
    else:
        print(f"\nFailed: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except Exception as e:
    print(f"\nError: {str(e)}")
    sys.exit(1)

print("\n" + "=" * 80 + "\n")

#!/usr/bin/env python3.9
"""
Manual Schwab OAuth Authorization Helper
"""

import os
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

app_key = os.getenv("SCHWAB_APP_KEY")
app_secret = os.getenv("SCHWAB_SECRET")

if not app_key or not app_secret:
    print("Missing credentials in .env file")
    exit(1)

print("\n" + "=" * 80)
print("SCHWAB OAUTH 2.0 MANUAL AUTHORIZATION")
print("=" * 80)

print("\nSTEP 1: Copy and paste this URL in your browser:")
print("=" * 80 + "\n")

auth_params = {
    'client_id': app_key,
    'response_type': 'code',
    'redirect_uri': 'http://localhost:8001/callback',
    'scope': 'PlaceTrades AccountAccess MoveMoney'
}

auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(auth_params)}"
print(auth_url)

print("\n" + "=" * 80)
print("\nSTEP 2: After authorizing in browser:")
print("  - You will be redirected to: http://localhost:8001/callback?code=YOUR_CODE")
print("  - Copy the authorization code")

print("\nSTEP 3: Save your token")
print("  - Run: python3.9 save_token.py")
print("  - Paste your authorization code when prompted")

print("\n" + "=" * 80 + "\n")

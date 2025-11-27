#!/usr/bin/env python3.9
"""
Schwab OAuth 2.0 Authorization Helper - Based on Schwabdev library
Manual authorization flow for obtaining tokens
"""

import os
import json
import base64
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

def main():
    print("\n" + "=" * 80)
    print("SCHWAB OAUTH 2.0 AUTHORIZATION")
    print("=" * 80)
    
    app_key = os.getenv("SCHWAB_APP_KEY")
    app_secret = os.getenv("SCHWAB_SECRET")
    
    if not app_key or not app_secret:
        print("\nError: Missing SCHWAB_APP_KEY or SCHWAB_SECRET in .env")
        return False
    
    print(f"\nApp Key loaded: {app_key[:10]}...{app_key[-5:]}")
    
    # Step 1: Display authorization URL
    print("\n" + "-" * 80)
    print("STEP 1: AUTHORIZE IN BROWSER")
    print("-" * 80)
    
    callback_url = "https://127.0.0.1"
    auth_params = {
        'client_id': app_key,
        'response_type': 'code',
        'redirect_uri': callback_url,
        'scope': 'PlaceTrades AccountAccess MoveMoney'
    }
    
    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(auth_params)}"
    
    print("\nOpen this URL in your browser and authorize:")
    print(auth_url)
    
    print("\nAfter clicking 'Authorize', you'll be redirected to a URL like:")
    print("https://127.0.0.1/?code=AUTHORIZATION_CODE&...")
    
    # Step 2: Get authorization code
    print("\n" + "-" * 80)
    print("STEP 2: GET AUTHORIZATION CODE")
    print("-" * 80)
    
    auth_code = input("\nEnter the full redirect URL (starting with https://): ").strip()
    
    if not auth_code:
        print("Error: No URL provided")
        return False
    
    # Extract code from URL
    try:
        if "code=" in auth_code:
            code = auth_code[auth_code.index("code=") + 5:]
            # Stop at next parameter
            if "&" in code:
                code = code[:code.index("&")]
        else:
            code = auth_code
        
        if not code:
            raise ValueError("Could not find code in URL")
            
        print(f"\nCode extracted: {code[:20]}...{code[-10:]}")
    except Exception as e:
        print(f"Error extracting code: {str(e)}")
        return False
    
    # Step 3: Exchange code for tokens using Basic auth
    print("\n" + "-" * 80)
    print("STEP 3: EXCHANGE CODE FOR TOKENS")
    print("-" * 80)
    
    print("\nSending token request...")
    
    try:
        # Create Basic auth header (like Schwabdev)
        auth_string = f"{app_key}:{app_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': callback_url
        }
        
        response = requests.post(
            'https://api.schwabapi.com/v1/oauth/token',
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"\nError: {response.status_code}")
            print(response.text)
            return False
        
        token_data = response.json()
        
        # Step 4: Save tokens
        print("\n" + "-" * 80)
        print("STEP 4: SAVE TOKENS")
        print("-" * 80)
        
        now = datetime.now(timezone.utc)
        
        token_file_data = {
            "access_token_issued": now.isoformat(),
            "refresh_token_issued": now.isoformat(),
            "token_dictionary": token_data
        }
        
        token_path = Path("./tokens/schwabToken.json")
        token_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(token_path, 'w') as f:
            json.dump(token_file_data, f, ensure_ascii=False, indent=4)
        
        print(f"\nTokens saved to: {token_path}")
        
        # Print token info
        at_expires = now + timedelta(seconds=token_data.get('expires_in', 1800))
        rt_expires = now + timedelta(seconds=7*24*60*60)
        
        print(f"\nToken Information:")
        print(f"  Access Token expires: {at_expires.strftime('%Y-%m-%d %H:%M:%S')} (30 min)")
        print(f"  Refresh Token expires: {rt_expires.strftime('%Y-%m-%d %H:%M:%S')} (7 days)")
        
        print("\n" + "=" * 80)
        print("SUCCESS! You can now test the API:")
        print("  python3.9 test_schwab_api.py")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

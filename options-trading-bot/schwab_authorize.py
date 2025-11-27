#!/usr/bin/env python3.9
"""
Schwab OAuth 2.0 Authorization Script
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Schwab"""
    
    authorization_code = None
    
    def do_GET(self):
        """Handle GET request with authorization code"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/callback':
            query = parse_qs(parsed_path.query)
            code = query.get('code', [None])[0]
            
            if code:
                CallbackHandler.authorization_code = code
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("""
                    <html>
                    <head><title>Authorization Successful</title></head>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1>Authorization Successful</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                """.encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Authorization Failed</h1>")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def main():
    print("=" * 80)
    print("SCHWAB OAUTH 2.0 AUTHORIZATION")
    print("=" * 80)
    
    app_key = os.getenv("SCHWAB_APP_KEY")
    app_secret = os.getenv("SCHWAB_SECRET")
    
    if not app_key or not app_secret:
        print("\nMissing Schwab API credentials in .env file")
        return False
    
    print(f"\nCredentials loaded from .env")
    
    print(f"\nStarting callback server on http://localhost:8001...")
    server = HTTPServer(('localhost', 8001), CallbackHandler)
    
    try:
        auth_params = {
            'client_id': app_key,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8001/callback',
            'scope': 'PlaceTrades AccountAccess MoveMoney'
        }
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(auth_params)}"
        
        print(f"\nOpening authorization URL in browser...")
        webbrowser.open(auth_url)
        
        print("\nWaiting for authorization (30 seconds timeout)...")
        
        server.timeout = 30
        server.handle_request()
        
        if CallbackHandler.authorization_code:
            auth_code = CallbackHandler.authorization_code
            print(f"\nAuthorization code received!")
            
            print(f"\nExchanging code for access token...")
            
            import requests
            
            payload = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": app_key,
                "client_secret": app_secret,
                "redirect_uri": "http://localhost:8001/callback"
            }
            
            response = requests.post(
                "https://api.schwabapi.com/v1/oauth/token",
                data=payload
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                from datetime import datetime, timedelta
                token_data['expires_at'] = (
                    datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
                ).isoformat()
                
                token_path = Path("./tokens/schwabToken.json")
                token_path.parent.mkdir(exist_ok=True)
                
                with open(token_path, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                print(f"\nToken obtained and saved!")
                print(f"Location: {token_path}")
                print(f"\nYou can now run: python3.9 test_schwab_api.py")
                
                return True
            else:
                print(f"\nFailed to exchange code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"\nNo authorization code received")
            return False
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False
    finally:
        server.server_close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# ⚙️ Schwab OAuth Token Setup - Interactive Guide

## Problem
Your Schwab API isn't working because there's no valid OAuth token. The token needs to be obtained through Schwab's OAuth 2.0 authorization flow.

## Solution: 3-Step OAuth Authorization

### Step 1: Generate the Authorization URL

Run this command to display your authorization URL:

```bash
python3.9 get_auth_url.py
```

This will show you a long URL starting with `https://api.schwabapi.com/v1/oauth/authorize?...`

### Step 2: Authorize in Browser

1. **Copy the full URL** from the terminal output
2. **Paste it into your web browser** 
3. **Log in** with your Schwab account credentials
4. **Click "Approve"** to authorize the application
5. **You'll be redirected** to a page that looks broken (that's normal)
6. **Look at the URL bar** - it will show: `http://localhost:8001/callback?code=YOUR_CODE_HERE`

### Step 3: Extract and Save the Authorization Code

1. Copy the **code parameter** from that URL (everything after `code=`)
   - Example: `code=abcd1234efgh5678ijkl9101112131415`

2. Run this command:
   ```bash
   python3.9 save_token.py
   ```

3. **Paste your authorization code** when prompted and press Enter

The script will:
- Exchange the code for an OAuth access token
- Save it to `./tokens/schwabToken.json`
- Show success confirmation

### Step 4: Test the API

Once the token is saved, run:

```bash
python3.9 test_schwab_api.py
```

This will retrieve your account balance and positions.

---

## Troubleshooting

### "Authorization Failed"
- Make sure you used the exact URL from `get_auth_url.py`
- Check that your browser is allowing redirects to localhost
- Try with a different browser

### "Invalid Code"
- The code expires after a few minutes
- If it times out, run the authorization process again
- Copy the code immediately after approval

### "400 Client Error"
- Your token file may be corrupted
- Delete `./tokens/schwabToken.json` and start over
- Make sure `.env` has correct `SCHWAB_APP_KEY` and `SCHWAB_SECRET`

### "Token Refresh Failed"
- Your refresh token may have expired
- Redo the authorization process to get a fresh token

---

## Automated Testing (Once Token is Saved)

After successful authorization, you can test:

```bash
# Test real account data
python3.9 test_schwab_api.py

# See the process without API calls
python3.9 mock_test_schwab_api.py

# Start the API server
python3.9 -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

---

## Token Details

Your saved token (`./tokens/schwabToken.json`) contains:
- `access_token`: Used for API calls (expires in ~30 mins)
- `refresh_token`: Used to get new access tokens (lasts longer)
- `expires_at`: When the access token expires
- Token is automatically refreshed when needed

The token file is in `.gitignore` - it won't be committed to git for security.

# OAuth 2.0 Migration Quick Reference

## What Changed?

### Before (Simple Token)
```bash
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -d '{
    "account_number": "123456789",
    "token": "your_oauth_token_here"
  }'
```

### After (OAuth 2.0 with App Key/Secret)
```bash
# 1. Set environment variables once
export SCHWAB_APP_KEY="your_app_key"
export SCHWAB_SECRET="your_app_secret"
export SCHWAB_ACCOUNT_NUMBER="your_account"

# 2. Get authorization code and exchange for token (one-time setup)
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -d '{
    "account_number": "123456789",
    "authorization_code": "auth_code_from_browser"
  }'

# 3. Use the bot (tokens managed automatically!)
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -d '{
    "account_number": "123456789",
    "symbol": "MSFT"
  }'
```

## Key Improvements

| Feature | Before | After |
|---------|--------|-------|
| **Auth Method** | Direct token | OAuth 2.0 |
| **Token Storage** | Passed each call | Persisted to file |
| **Token Refresh** | Manual | Automatic |
| **Token Expiration** | Always valid | Auto-refreshed |
| **Setup Complexity** | Simple | One-time OAuth flow |
| **Security** | Token in API calls | Credentials in env vars |

## Quick Setup (5 minutes)

### Step 1: Get App Key & Secret
1. Go to https://developer.schwab.com
2. Create new application
3. Get Client ID (App Key) and Client Secret

### Step 2: Update .env
```bash
SCHWAB_APP_KEY=your_key_here
SCHWAB_SECRET=your_secret_here
SCHWAB_ACCOUNT_NUMBER=your_account
SCHWAB_TOKEN=./tokens/schwabToken.json
```

### Step 3: Get Authorization Code
Open in browser:
```
https://api.schwabapi.com/v1/oauth/authorize?client_id=YOUR_APP_KEY&redirect_uri=http://localhost:8000/callback&response_type=code&scope=PlaceTrades%20AccountAccess
```

Copy the `code` from redirect URL

### Step 4: Exchange Code for Token
```bash
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "authorization_code": "YOUR_CODE"
  }'
```

### Step 5: Done!
Token is saved automatically. Bot handles refresh!

## API Changes

### New Endpoint: POST /schwab/authorize
Exchange authorization code for OAuth token

**Parameters:**
```json
{
  "account_number": "required",
  "authorization_code": "required",
  "app_key": "optional (uses env var)",
  "app_secret": "optional (uses env var)",
  "token_path": "optional (uses env var)"
}
```

### Updated Endpoint: GET /schwab/test
Now supports OAuth authentication

**Parameters:**
```
account_number (required)
app_key (optional)
app_secret (optional)  
token_path (optional)
token (legacy, optional)
```

### Updated Endpoint: POST /schwab/analyze
Request body updated:

```json
{
  "account_number": "required",
  "app_key": "optional",
  "app_secret": "optional",
  "token_path": "optional",
  "token": "optional (legacy)",
  "account_size": 10000
}
```

Query parameters:
- `symbol` (required)
- `days` (optional, default 60)

## Environment Variables

```bash
# Required
SCHWAB_APP_KEY=your_client_id
SCHWAB_SECRET=your_client_secret
SCHWAB_ACCOUNT_NUMBER=your_account

# Optional
SCHWAB_TOKEN=./tokens/schwabToken.json  # Default path for token storage
```

## Token File

**Location:** `./tokens/schwabToken.json` (configurable)

**Format:**
```json
{
  "access_token": "token_value",
  "refresh_token": "refresh_token_value",
  "expires_in": 1800,
  "expires_at": "2025-11-27T14:30:00",
  "token_type": "Bearer"
}
```

**Auto-Management:**
- Token auto-loads from file
- Auto-refreshes if expired
- Auto-saves new token after refresh

## Backward Compatibility

The `token` parameter still works for legacy support:

```json
{
  "account_number": "123456789",
  "token": "your_direct_token"
}
```

But OAuth 2.0 is recommended for security and convenience.

## Migration Checklist

- [ ] Get App Key and App Secret from Schwab
- [ ] Update `.env` file with new credentials
- [ ] Create `./tokens/` directory (optional, auto-created)
- [ ] Run `/schwab/authorize` endpoint once to get initial token
- [ ] Test with `/schwab/test` endpoint
- [ ] Update any client code to new endpoint signatures
- [ ] Remove old token passing from code

## Troubleshooting

### Token File Issues
```bash
# Check if token exists
cat ./tokens/schwabToken.json

# Check expiration
cat ./tokens/schwabToken.json | grep expires_at

# Manually delete to force refresh
rm ./tokens/schwabToken.json
```

### Authorization Code Issues
- Code expires after 30 minutes, get a fresh one
- Ensure redirect_uri matches Schwab app settings
- Check callback URL is `http://localhost:8000/callback`

### Environment Variables
```bash
# Verify env vars are set
echo $SCHWAB_APP_KEY
echo $SCHWAB_SECRET
echo $SCHWAB_ACCOUNT_NUMBER

# Use in code
import os
app_key = os.getenv("SCHWAB_APP_KEY")
```

## Support

Full setup guide: See `SCHWAB_OAUTH_SETUP.md`

Documentation: https://developer.schwab.com/docs

Logs: `tail -f logs/$(date +%Y%m%d).log`

---

**Version**: 2.1.0  
**Migration Date**: November 27, 2025  
**Status**: ✅ Production Ready


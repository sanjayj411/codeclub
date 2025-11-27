# 🔐 Schwab OAuth 2.0 Setup Guide

## Overview

The bot now uses OAuth 2.0 with App Key/Secret authentication and persistent token storage. This is more secure and requires setup only once.

## Architecture

```
┌─────────────────────────────────┐
│   Schwab Developer Console      │
│  - App Key & App Secret         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Trading Bot (src/brokers)     │
│  - Uses App Key/Secret          │
│  - Manages token lifecycle      │
│  - Auto-refreshes tokens        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   Token Storage                 │
│  - Path: ./tokens/schwabToken.json
│  - Contains: access_token,      │
│    refresh_token, expires_at    │
└─────────────────────────────────┘
```

## Step 1: Get Your App Key & Secret

1. Go to https://developer.schwab.com
2. Sign in with your Schwab account
3. Go to **"My Apps"** section
4. Click **"Create Application"**
5. Fill in application details:
   - **App Name**: Options Trading Bot
   - **Callback URL**: `http://localhost:8000/callback`
   - Other required fields
6. Once created, you'll get:
   - **Client ID** (App Key)
   - **Client Secret**

## Step 2: Configure Environment Variables

Update your `.env` file with your credentials:

```bash
# .env
SCHWAB_APP_KEY=your_client_id_here
SCHWAB_SECRET=your_client_secret_here
SCHWAB_TOKEN=./tokens/schwabToken.json
SCHWAB_ACCOUNT_NUMBER=your_account_number
```

## Step 3: Get Authorization Code

You need to obtain an authorization code from Schwab. There are two ways:

### Option A: Manual Authorization (One-time)

1. Open this URL in your browser (replace YOUR_APP_KEY):
```
https://api.schwabapi.com/v1/oauth/authorize?client_id=YOUR_APP_KEY&redirect_uri=http://localhost:8000/callback&response_type=code&scope=PlaceTrades%20AccountAccess
```

2. Log in with your Schwab account
3. Authorize the application
4. You'll be redirected to a URL with the authorization code:
```
http://localhost:8000/callback?code=YOUR_AUTHORIZATION_CODE&session=...
```

5. Copy the `code` value

### Option B: Automated OAuth Flow (Recommended)

Use the `/schwab/authorize` endpoint to exchange the code for a token:

```bash
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "authorization_code": "YOUR_AUTHORIZATION_CODE",
    "app_key": "YOUR_APP_KEY",
    "app_secret": "YOUR_APP_SECRET"
  }'
```

Response (Success):
```json
{
  "status": "SUCCESS",
  "message": "Token obtained and saved successfully",
  "token_path": "./tokens/schwabToken.json",
  "account_number": "XXXXXXXXXX"
}
```

Token is automatically saved to `./tokens/schwabToken.json`

## Step 4: Test Your Setup

Run the test endpoint to verify everything works:

```bash
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=YOUR_ACCOUNT"
```

The endpoint will:
1. Load the token from file (or refresh if expired)
2. Test account info retrieval
3. Test quote retrieval
4. Test price history retrieval

Success response:
```json
{
  "status": "SUCCESS",
  "account": {
    "account_number": "...",
    "buying_power": 50000,
    "cash_balance": 25000
  },
  "test_quote": {
    "symbol": "AAPL",
    "price": 150.25
  },
  "price_history_candles": 5,
  "message": "All tests passed!"
}
```

## Step 5: Use the Bot

Now you can use any endpoint with just the account number (no token needed):

```bash
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "account_size": 10000,
    "symbol": "MSFT",
    "days": 60
  }'
```

## Token Management

### Automatic Token Refresh

Tokens expire after ~1800 seconds. The bot automatically:
1. Loads token from file
2. Checks expiration time
3. Refreshes if expired
4. Saves new token back to file

You don't need to do anything - it's automatic!

### Manual Token Refresh

If you need to get a new token manually:

```bash
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "authorization_code": "NEW_AUTH_CODE"
  }'
```

### Token File Location

Default: `./tokens/schwabToken.json`

You can change this with the `SCHWAB_TOKEN` environment variable:
```bash
SCHWAB_TOKEN=/custom/path/token.json
```

### Token File Format

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 1800,
  "expires_at": "2025-11-27T14:30:00.123456",
  "token_type": "Bearer"
}
```

## Security Best Practices

✅ **DO:**
- Store `.env` locally (never commit to git)
- Keep App Secret safe (don't share publicly)
- Use `.gitignore` for `tokens/` directory
- Rotate tokens periodically
- Use HTTPS in production

❌ **DON'T:**
- Commit `.env` file to git
- Share your App Secret
- Hardcode credentials in code
- Use same credentials across multiple apps
- Leave tokens in public directories

## Troubleshooting

### "Token file not found"
- Ensure `./tokens/` directory exists and is writable
- Run authorize endpoint first to create token file
- Check `SCHWAB_TOKEN` environment variable

### "Token expired"
- Tokens expire after ~30 minutes
- Bot auto-refreshes automatically
- If manual refresh needed, use `/schwab/authorize`

### "Invalid authorization code"
- Authorization codes expire after 30 minutes
- Get a fresh code from the OAuth URL
- Ensure `response_type=code` is in URL

### "Callback URL mismatch"
- Ensure redirect_uri in OAuth URL matches Schwab app settings
- Default: `http://localhost:8000/callback`

## API Endpoints

### Authorize (Get Token)
```
POST /schwab/authorize
Parameters:
  - account_number (required)
  - authorization_code (required)
  - app_key (optional, uses env var if not provided)
  - app_secret (optional, uses env var if not provided)
  - token_path (optional, uses env var if not provided)
```

### Test Connection
```
GET /schwab/test
Parameters:
  - account_number (required)
  - app_key (optional)
  - app_secret (optional)
  - token_path (optional)
  - token (optional, for legacy support)
```

### Analyze Symbol
```
POST /schwab/analyze
Body:
  {
    "account_number": "...",
    "app_key": "...",
    "app_secret": "...",
    "token_path": "...",
    "account_size": 10000
  }
Parameters:
  - symbol (required)
  - days (optional, default 60)
```

### Execute Trade
```
POST /schwab/execute
Body:
  {
    "account_number": "...",
    "app_key": "...",
    "app_secret": "...",
    "account_size": 10000
  }
```

### Monitor Positions
```
POST /schwab/monitor
Body:
  {
    "account_number": "...",
    "app_key": "...",
    "app_secret": "...",
    "account_size": 10000
  }
```

## Environment Variables

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| SCHWAB_APP_KEY | Client ID from Schwab | Yes | `eAOSWa4Jvf...` |
| SCHWAB_SECRET | Client Secret from Schwab | Yes | `LUvCrZxarY...` |
| SCHWAB_TOKEN | Path to token file | No | `./tokens/token.json` |
| SCHWAB_ACCOUNT_NUMBER | Your Schwab account | Yes | `123456789` |

## Example Workflow

```bash
# 1. Set environment variables
export SCHWAB_APP_KEY="your_app_key"
export SCHWAB_SECRET="your_app_secret"
export SCHWAB_ACCOUNT_NUMBER="your_account"

# 2. Start the bot
python3.9 -m uvicorn src.api:app --port 8000

# 3. Get authorization code (do this in browser)
# Open: https://api.schwabapi.com/v1/oauth/authorize?client_id=YOUR_APP_KEY&redirect_uri=http://localhost:8000/callback&response_type=code&scope=PlaceTrades%20AccountAccess

# 4. Exchange code for token
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "authorization_code": "YOUR_AUTH_CODE"
  }'

# 5. Test the connection
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=YOUR_ACCOUNT"

# 6. Analyze a symbol
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "symbol": "MSFT",
    "days": 60
  }'
```

## Common Scopes

When authorizing, you may need these scopes:

- `PlaceTrades` - Execute trades
- `AccountAccess` - View account info
- `MoveMoney` - Transfer funds

Scope example in OAuth URL:
```
&scope=PlaceTrades%20AccountAccess
```

## Support

For Schwab OAuth documentation:
- https://developer.schwab.com/docs
- https://api.schwabapi.com/v1/oauth/authorize

For bot issues:
- Check logs: `tail -f logs/$(date +%Y%m%d).log`
- Run diagnostic: `GET /schwab/test`
- Check token file: `cat ./tokens/schwabToken.json`

---

**Version**: 2.1.0 (OAuth 2.0)  
**Updated**: November 27, 2025


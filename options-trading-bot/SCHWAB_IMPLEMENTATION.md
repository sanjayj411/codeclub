# Schwab API - OAuth 2.0 Implementation

## Overview

This implementation uses **OAuth 2.0** with **Basic Authorization** (Base64-encoded App Key:Secret) for secure token management, based on the proven [Schwabdev library](https://github.com/tylerebowers/Schwabdev).

### Key Features

✅ **Base64-encoded Basic Authentication** - Secure credential handling  
✅ **Automatic Token Management** - Automatic expiration tracking and refresh  
✅ **Persistent Token Storage** - Tokens saved with timestamps  
✅ **Access Token: 30 minutes** - Auto-refreshes before expiration  
✅ **Refresh Token: 7 days** - Valid for a week  
✅ **Callback URL Capture** - Optional automatic authorization  

## Quick Start

### Step 1: Authorize

```bash
python3.9 authorize_schwab.py
```

Follow the instructions:
1. Copy the authorization URL
2. Paste into browser
3. Login and authorize
4. Copy the redirect URL
5. Paste into the script
6. Tokens are saved!

### Step 2: Test

```bash
python3.9 test_schwab_api.py
```

This retrieves account balance and positions.

## Implementation Details

### Token Storage Format

Tokens are stored in `./tokens/schwabToken.json`:

```json
{
  "access_token_issued": "2025-11-27T13:30:00+00:00",
  "refresh_token_issued": "2025-11-27T13:30:00+00:00",
  "token_dictionary": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "scope": "PlaceTrades AccountAccess MoveMoney"
  }
}
```

### Authentication Method

Uses **Basic Authorization** header:

```python
# Instead of:
payload = {"client_id": app_key, "client_secret": app_secret, ...}

# We use:
headers = {
    'Authorization': f'Basic {base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()}',
    'Content-Type': 'application/x-www-form-urlencoded'
}
```

### Token Lifecycle

1. **Initial Authorization**
   - User gets authorization code from browser
   - Code exchanged for access + refresh tokens
   - Tokens saved with timestamps

2. **Automatic Token Refresh**
   - Every 30 seconds, tokens are checked
   - If access token expires soon, it's auto-refreshed using refresh token
   - If refresh token < 30 min remaining, user is warned

3. **API Calls**
   - All API calls use Bearer token authentication
   - Tokens automatically updated before expiration

## API Usage

### Basic Usage

```python
from src.brokers import SchwabBrokerAPI

# Initialize broker
broker = SchwabBrokerAPI(
    account_number="6578-7226",
    app_key="your_app_key",
    app_secret="your_app_secret",
    token_path="./tokens/schwabToken.json"
)

# Get account info
account_info = broker.get_account_info()
print(f"Buying Power: ${account_info['buying_power']:,.2f}")

# Get positions
positions = account_info['positions']
for pos in positions:
    print(f"{pos['instrument']['symbol']}: {pos['longQuantity']} shares")

# Get quote
quote = broker.get_quote("AAPL")
print(f"AAPL: ${quote['price']:.2f}")

# Get price history
history = broker.get_price_history("AAPL", days=5)
for candle in history:
    print(f"Close: ${candle['close']:.2f}")
```

### Token Management

```python
# Update tokens (checks expiration and refreshes if needed)
broker.update_tokens()

# Manual authorization with new code
broker.authorize_and_save_token(authorization_code)

# Update access token manually
broker.update_access_token()
```

## Troubleshooting

### "No valid tokens found"

**Solution:**
```bash
python3.9 authorize_schwab.py
```

### "Access token expired"

**Automatic:** Refreshed automatically on next API call  
**Manual:** `broker.update_access_token()`

### "Refresh token expired"

**Solution:** Re-authorize
```bash
python3.9 authorize_schwab.py
```

### "401 Unauthorized"

Check that you have:
- ✓ Both APIs added to your Schwab app
- ✓ Valid refresh token (< 7 days old)
- ✓ Correct account number

### "400 Bad Request"

Check:
- ✓ App Key and Secret are correct
- ✓ Authorization code is valid (expires after 30 seconds)
- ✓ Redirect URL matches registration

## Environment Configuration

In `.env`:

```bash
SCHWAB_APP_KEY="your_32_char_key"
SCHWAB_SECRET="your_16_char_secret"
SCHWAB_ACCOUNT_NUMBER="your_account"
SCHWAB_TOKEN=./tokens/schwabToken.json
```

## Files

- `src/brokers/__init__.py` - SchwabBrokerAPI class with OAuth 2.0
- `authorize_schwab.py` - Interactive authorization script
- `test_schwab_api.py` - Test account balance and positions
- `.tokens/schwabToken.json` - Token storage (auto-created, .gitignored)

## Differences from Previous Implementation

| Feature | Old | New |
|---------|-----|-----|
| Authentication | Request body credentials | Base64 Basic Auth |
| Token Storage | expires_at only | issued timestamps + dictionary |
| Token Timeout | 1800 sec calculation | explicit 1800/604800 sec |
| Access Token Check | Check expires_at | Check time delta |
| Authorization | Manual API exchange | Helper script with proper auth |
| Error Handling | Basic logging | Detailed error messages |

## References

- [Schwabdev GitHub](https://github.com/tylerebowers/Schwabdev)
- [Schwabdev Documentation](https://tylerebowers.github.io/Schwabdev/)
- [Schwab Developer](https://developer.schwab.com)

## Next Steps

Once authorization is complete:

1. **Test individual endpoints** via the test script
2. **Start the API server**: `python3.9 -m uvicorn src.api:app`
3. **Access Swagger UI**: http://127.0.0.1:8000/docs
4. **Integrate with trading bot** for automated strategies

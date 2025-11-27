# Schwab API OAuth 2.0 Setup Guide

## Problem Solved

The Schwab API integration was failing with "400 Bad Request" errors because the OAuth 2.0 authentication wasn't correctly implemented. 

We've now refactored the implementation based on the proven [Schwabdev library](https://github.com/tylerebowers/Schwabdev) which is the most popular and reliable Python Schwab API wrapper.

## What Changed

### 1. Authentication Method
- **Before**: Credentials sent in request body ❌
- **After**: Base64-encoded Basic Authorization header ✓

### 2. Token Management  
- **Before**: Simple expires_at tracking
- **After**: Proper issued timestamp tracking with delta calculations

### 3. Token Lifecycle
- **Before**: Manual refresh required
- **After**: Automatic background checking every 30 seconds

### 4. Files Updated
- `src/brokers/__init__.py` - New OAuth 2.0 implementation
- `authorize_schwab.py` - Manual authorization helper
- `test_schwab_api.py` - Updated test script
- New documentation files

## Getting Started

### Option A: Quick Authorization (Recommended)

```bash
# Step 1: Get authorization URL
python3.9 authorize_schwab.py

# Step 2: Copy URL into browser, authorize, paste redirect URL back
# Step 3: Tokens are saved!

# Step 4: Test the API
python3.9 test_schwab_api.py
```

### Option B: Manual Authorization

If the script doesn't work:

1. Visit this URL in your browser:
```
https://api.schwab.com/v1/oauth/authorize?client_id=YOUR_APP_KEY&response_type=code&redirect_uri=https://127.0.0.1&scope=PlaceTrades+AccountAccess+MoveMoney
```

2. Login and authorize

3. Copy the redirect URL from your browser's address bar

4. Run:
```bash
python3.9 authorize_schwab.py
```
And paste the URL when prompted

## Verify It's Working

```bash
python3.9 test_schwab_api.py
```

Should show:
```
SCHWAB API TEST - Account Balance and Positions
✓ Access Token: ...
✓ Refresh Token available

TEST 1: Get Account Information
✓ Account Info Retrieved!
  Account: 6578-7226
  Buying Power: $25,000.00
  ...
```

## Understanding the New Implementation

### Token Storage

Tokens stored in `./tokens/schwabToken.json`:
- Access token: 30 minutes validity
- Refresh token: 7 days validity  
- Issued timestamps: Track expiration accurately

### Automatic Refresh

- Every 30 seconds, tokens are checked
- If access token expiring soon, it's auto-refreshed
- All happens in background automatically

### API Calls

All requests use Bearer token:
```python
headers = {"Authorization": f"Bearer {access_token}"}
```

## Troubleshooting

### Issue: "No valid tokens found"
**Fix:**
```bash
python3.9 authorize_schwab.py
```

### Issue: "401 Unauthorized"
- Check both APIs are added to your Schwab app
- Check account number is correct
- Try refreshing tokens: `python3.9 authorize_schwab.py`

### Issue: "400 Bad Request"
- Authorization code expires after 30 seconds
- Re-run the authorization script

## Next Steps

1. ✓ Test authorization
2. ✓ Run test_schwab_api.py
3. Start FastAPI server: `python3.9 -m uvicorn src.api:app`
4. Use Swagger UI: http://127.0.0.1:8000/docs
5. Integrate with trading strategies

## Technical Details

See `SCHWAB_IMPLEMENTATION.md` for:
- Detailed implementation documentation
- API usage examples
- Token management details
- Troubleshooting guide

## References

- [Schwabdev Library](https://github.com/tylerebowers/Schwabdev) - Base implementation
- [Schwab Developer](https://developer.schwab.com) - API documentation
- [OAuth 2.0](https://oauth.net/2/) - Authentication standard

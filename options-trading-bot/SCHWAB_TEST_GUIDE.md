# Schwab API Testing Guide

## Overview
This guide walks you through obtaining OAuth tokens and testing the Schwab API integration to retrieve account balance and positions.

## Prerequisites
- Schwab brokerage account
- Schwab API credentials (App Key and Secret) in `.env` file
- Python 3.9+
- Internet connection

## Step-by-Step Instructions

### Step 1: Check Your Environment
Verify credentials are in `.env`:
```bash
grep SCHWAB .env
```

Should show:
```
SCHWAB_APP_KEY="your_key"
SCHWAB_SECRET="your_secret"
SCHWAB_ACCOUNT_NUMBER="your_account"
SCHWAB_TOKEN=./tokens/schwabToken.json
```

### Step 2: Get Authorization URL
```bash
python3.9 get_auth_url.py
```

This displays the OAuth authorization URL you need to visit.

### Step 3: Authorize in Browser
1. Copy the URL from the output
2. Open it in your browser
3. Login with your Schwab credentials
4. Grant the application the requested permissions:
   - PlaceTrades
   - AccountAccess
   - MoveMoney
5. You'll be redirected to `http://localhost:8001/callback?code=YOUR_CODE`
6. Copy the authorization code

### Step 4: Save OAuth Token
```bash
python3.9 save_token.py
```

Then paste your authorization code when prompted.

The token will be saved to `./tokens/schwabToken.json`

### Step 5: Test Account Balance & Positions
```bash
python3.9 test_schwab_api.py
```

This will:
- ✅ Test account information retrieval
- ✅ Display account balance and buying power
- ✅ Show all open positions
- ✅ Get real-time quotes (if market is open)
- ✅ Retrieve 5 days of price history

## Expected Output

```
================================================================================
SCHWAB API TEST - Account Balance and Positions
================================================================================

Connecting to Schwab API...
Account: 6578-7226

================================================================================
TEST 1: Get Account Information
================================================================================

Account Info Retrieved Successfully!
  Account Number: 6578-7226
  Buying Power: $25,000.00
  Cash Balance: $5,000.00
  Margin Available: $20,000.00
  Positions Count: 3

================================================================================
TEST 2: Account Positions
================================================================================

Found 3 position(s):

  Position 1: AAPL
    Quantity: 10
    Market Value: $1,650.00
    Avg Price: $165.00

  Position 2: GOOGL
    Quantity: 5
    Market Value: $2,100.00
    Avg Price: $420.00

  Position 3: SPY
    Quantity: 20
    Market Value: $8,500.00
    Avg Price: $425.00

================================================================================
TEST 3: Real-time Quote (AAPL)
================================================================================

Quote Retrieved!
  Symbol: AAPL
  Price: $165.50
  Bid: $165.48
  Ask: $165.52

...
```

## Troubleshooting

### "No authorization code received"
- Browser popup may have been blocked
- Try visiting the URL directly in a new tab

### "Token not found" error
- Run `save_token.py` again to obtain a new token
- Tokens expire after 30 minutes of inactivity

### "400 Client Error" on API call
- Token may have expired
- Run `save_token.py` with a new authorization code
- Check account number is correct in `.env`

### Market Data Not Available
- Quotes/history only available during market hours
- Real quotes available weekdays 9:30 AM - 4:00 PM ET

## Token Refresh

Tokens are automatically refreshed when they expire. The refresh token is used to obtain new access tokens without requiring manual authorization again.

To manually refresh:
```bash
# The next API call will automatically refresh if needed
python3.9 test_schwab_api.py
```

## API Endpoints Available

After successful authorization, you can use:

### Account Information
```python
broker = SchwabBrokerAPI(
    account_number="6578-7226",
    app_key=os.getenv("SCHWAB_APP_KEY"),
    app_secret=os.getenv("SCHWAB_SECRET"),
    token_path="./tokens/schwabToken.json"
)

account_info = broker.get_account_info()
```

### Real-time Quotes
```python
quote = broker.get_quote("AAPL")
# Returns: price, bid, ask, volume, etc.
```

### Price History
```python
history = broker.get_price_history("AAPL", days=5)
# Returns list of OHLCV candles
```

### Place Orders
```python
order_result = broker.place_order({
    "symbol": "AAPL",
    "quantity": 10,
    "order_type": "limit",
    "price": 165.00
})
```

## Security Notes

- ✅ Tokens stored in `./tokens/` directory (ignored by git)
- ✅ App Key and Secret in `.env` (not committed)
- ✅ Tokens automatically refreshed before expiration
- ✅ Session headers always use Bearer token authentication

## Next Steps

Once testing is successful:

1. **Start the FastAPI server**:
   ```bash
   python3.9 -m uvicorn src.api:app --host 127.0.0.1 --port 8000
   ```

2. **Test via API endpoints**:
   - `GET /schwab/test` - Test connection
   - `GET /schwab/analyze?symbol=AAPL` - Get trading signals
   - `POST /schwab/execute` - Execute trades
   - `GET /schwab/monitor` - Monitor positions

3. **Use Swagger UI**:
   - Navigate to http://127.0.0.1:8000/docs
   - Test endpoints interactively

## Support

For issues with:
- **OAuth flow**: Check https://developer.schwab.com
- **API errors**: Review token expiration and account number
- **Integration**: See `src/brokers/__init__.py` and `src/api/__init__.py`

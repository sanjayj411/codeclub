# 🚀 Using the New OAuth 2.0 Schwab Integration

## Complete Example Workflow

This guide shows you exactly how to use the new system step by step.

## Part 1: Initial Setup (One-time)

### Step 1: Get Your Credentials from Schwab

```
1. Go to: https://developer.schwab.com
2. Log in with your Schwab account
3. Click "My Apps"
4. Click "Create Application"
5. Fill in the form:
   - App Name: "Options Trading Bot"
   - App Type: Select appropriate type
   - Callback URL: http://localhost:8000/callback
6. Accept terms and create
7. You'll get:
   - Client ID (this is your APP_KEY)
   - Client Secret
```

### Step 2: Update Your .env File

```bash
# .env
SCHWAB_APP_KEY=eAOSWa4JvYdCWfSlnMLRQ1JAhmM8iYFA
SCHWAB_SECRET=LUvCrZxarYzg6uVB
SCHWAB_ACCOUNT_NUMBER=123456789
SCHWAB_TOKEN=./tokens/schwabToken.json
```

### Step 3: Get Authorization Code

This is the OAuth dance. You do this once:

```bash
# Open this URL in your browser (replace YOUR_APP_KEY):
https://api.schwabapi.com/v1/oauth/authorize?client_id=eAOSWa4JvYdCWfSlnMLRQ1JAhmM8iYFA&redirect_uri=http://localhost:8000/callback&response_type=code&scope=PlaceTrades%20AccountAccess

# You'll be asked to log in to Schwab
# Then asked to authorize the app
# Then redirected to: http://localhost:8000/callback?code=YOUR_CODE&session=...
# Copy the CODE value
```

### Step 4: Exchange Code for Token

```bash
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "123456789",
    "authorization_code": "your_code_here"
  }'
```

Response:
```json
{
  "status": "SUCCESS",
  "message": "Token obtained and saved successfully",
  "token_path": "./tokens/schwabToken.json",
  "account_number": "123456789"
}
```

✅ **Done! Your token is now saved and will auto-refresh.**

## Part 2: Using the Bot

### Test Your Connection

```bash
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=123456789"
```

Should return:
```json
{
  "status": "SUCCESS",
  "account": {
    "account_number": "123456789",
    "buying_power": 50000.00,
    "cash_balance": 25000.00,
    "margin_available": 25000.00
  },
  "test_quote": {
    "symbol": "AAPL",
    "price": 150.25,
    "bid": 150.24,
    "ask": 150.26,
    "volume": 12345678
  },
  "price_history_candles": 5,
  "message": "All tests passed. Your Schwab connection is working!"
}
```

### Analyze a Stock

```bash
curl -X POST "http://127.0.0.1:8000/schwab/analyze?symbol=MSFT&days=60" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "123456789"
  }'
```

Response:
```json
{
  "symbol": "MSFT",
  "current_price": 416.25,
  "bid": 416.20,
  "ask": 416.30,
  "volume": 18234567,
  "technical": {
    "signal": "BUY",
    "entry": 416.25,
    "stop_loss": 407.52,
    "take_profit": 435.00,
    "signal_strength": 0.85
  },
  "quantitative": {
    "volatility": 0.18,
    "sharpe_ratio": 1.45,
    "max_drawdown": -12.5,
    "trend": "UP",
    "slope": 0.85
  },
  "monte_carlo": {
    "mean_price": 425.30,
    "std_dev": 18.5,
    "prob_up": 0.68
  },
  "recommendation": "STRONG_BUY"
}
```

### Execute a Trade

```bash
curl -X POST "http://127.0.0.1:8000/schwab/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "123456789",
    "symbol": "MSFT",
    "signal": "BUY",
    "entry": 416.25,
    "stop_loss": 407.52,
    "take_profit": 435.00,
    "contracts": 1
  }'
```

### Monitor Your Positions

```bash
curl -X POST "http://127.0.0.1:8000/schwab/monitor" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "123456789"
  }'
```

## Part 3: Using in Python Code

### Simple Example

```python
from src.bot import EnhancedTradingBot

# Initialize bot (uses env vars automatically)
bot = EnhancedTradingBot(
    account_number="123456789",
    account_size=10000
)

# Analyze a symbol
analysis = bot.analyze_symbol("MSFT", days=60)

print(f"Signal: {analysis['technical']['signal']}")
print(f"Entry: {analysis['technical']['entry']}")
print(f"Stop Loss: {analysis['technical']['stop_loss']}")
print(f"Take Profit: {analysis['technical']['take_profit']}")
print(f"Recommendation: {analysis['recommendation']}")
```

### With Custom Credentials

```python
from src.bot import EnhancedTradingBot

# Use custom paths/credentials
bot = EnhancedTradingBot(
    account_number="123456789",
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    token_path="/custom/path/token.json",
    account_size=10000
)

analysis = bot.analyze_symbol("AAPL")
```

### Execute a Signal

```python
from src.bot import EnhancedTradingBot

bot = EnhancedTradingBot(account_number="123456789")
analysis = bot.analyze_symbol("MSFT")

# Execute if signal is BUY
if analysis['technical']['signal'] == 'BUY':
    result = bot.execute_signal("MSFT", analysis['technical'])
    print(f"Order Status: {result['status']}")
    print(f"Order ID: {result['order_id']}")
```

### Monitor Positions

```python
from src.bot import EnhancedTradingBot

bot = EnhancedTradingBot(account_number="123456789")
updates = bot.monitor_positions()

for position in updates:
    print(f"{position['symbol']}: {position.get('pnl_percent', 0):.2f}%")
```

## Part 4: Common Tasks

### Check Token Status

```bash
# View token file
cat ./tokens/schwabToken.json

# Check expiration
cat ./tokens/schwabToken.json | grep expires_at

# Token size
ls -lh ./tokens/schwabToken.json
```

### Refresh Token Manually

Token refreshes automatically, but to force it:

```bash
# Delete old token
rm ./tokens/schwabToken.json

# Get new authorization code and run authorize endpoint again
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -d '{
    "account_number": "123456789",
    "authorization_code": "new_auth_code"
  }'
```

### Check Account Info

```bash
from src.brokers import SchwabBrokerAPI

broker = SchwabBrokerAPI(account_number="123456789")
account_info = broker.get_account_info()

print(f"Buying Power: ${account_info['buying_power']}")
print(f"Cash Balance: ${account_info['cash_balance']}")
print(f"Margin Available: ${account_info['margin_available']}")
```

### Get Real-time Quote

```bash
from src.brokers import SchwabBrokerAPI

broker = SchwabBrokerAPI(account_number="123456789")
quote = broker.get_quote("MSFT")

print(f"Price: ${quote['price']}")
print(f"Bid: ${quote['bid']}")
print(f"Ask: ${quote['ask']}")
print(f"Volume: {quote['volume']}")
```

### Get Historical Data

```bash
from src.brokers import SchwabBrokerAPI

broker = SchwabBrokerAPI(account_number="123456789")
history = broker.get_price_history("MSFT", days=60)

print(f"Total candles: {len(history)}")
for candle in history[-5:]:  # Last 5 candles
    print(f"Close: ${candle['close']}, Volume: {candle['volume']}")
```

## Part 5: Troubleshooting

### "Token file not found"

```bash
# Create tokens directory
mkdir -p ./tokens

# Run authorize endpoint to create file
curl -X POST "http://127.0.0.1:8000/schwab/authorize" \
  -d '{
    "account_number": "123456789",
    "authorization_code": "your_code"
  }'
```

### "Authorization failed"

Check your credentials:
```bash
echo $SCHWAB_APP_KEY
echo $SCHWAB_SECRET
echo $SCHWAB_ACCOUNT_NUMBER
```

Verify they match Schwab Developer Console.

### "Invalid scope"

Ensure you're using correct scopes in OAuth URL:
```
PlaceTrades AccountAccess
```

Properly encoded:
```
PlaceTrades%20AccountAccess
```

### "Connection timeout"

Check network connectivity:
```bash
curl -X GET "https://api.schwabapi.com/trader/v1/accounts" -H "Authorization: Bearer $TOKEN"
```

### View Logs

```bash
# Today's logs
tail -f logs/$(date +%Y%m%d).log

# Last 50 lines
tail -50 logs/$(date +%Y%m%d).log

# Filter errors
grep -i error logs/$(date +%Y%m%d).log
```

## Part 6: Advanced Usage

### Custom Token Path

```bash
# Use custom token location
export SCHWAB_TOKEN=/home/user/secure/tokens/schwab.json

# Or pass directly
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=123456789&token_path=/custom/path/token.json"
```

### Multiple Accounts

```bash
from src.bot import EnhancedTradingBot

# Account 1
bot1 = EnhancedTradingBot(
    account_number="111111111",
    token_path="./tokens/account1.json"
)

# Account 2
bot2 = EnhancedTradingBot(
    account_number="222222222",
    token_path="./tokens/account2.json"
)

analysis1 = bot1.analyze_symbol("MSFT")
analysis2 = bot2.analyze_symbol("AAPL")
```

### Batch Analysis

```python
from src.bot import EnhancedTradingBot

bot = EnhancedTradingBot(account_number="123456789")

symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

for symbol in symbols:
    analysis = bot.analyze_symbol(symbol)
    if analysis.get('technical', {}).get('signal') == 'BUY':
        print(f"BUY Signal: {symbol}")
```

## Summary

✅ **Initial Setup**: 15 minutes (one-time)
✅ **Daily Usage**: Automatic - no token management needed
✅ **Security**: App Key/Secret in env vars, tokens auto-managed
✅ **Reliability**: Auto-refresh handles token expiration
✅ **Flexibility**: Environment or parameter configuration

---

**Version**: 2.1.0  
**Date**: November 27, 2025  
**Status**: ✅ Production Ready


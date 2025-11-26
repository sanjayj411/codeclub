# 🔧 Debugging Guide - "No data for MSFT" Error

## Issue Description
When calling the `/schwab/analyze` endpoint with a ticker like MSFT, you're getting:
```json
{
  "error": "No data for MSFT"
}
```

## Root Causes & Solutions

### 1. **Invalid or Expired Schwab OAuth Token** (Most Common)
The `token` parameter you're passing is either invalid or expired.

**Solution:**
```bash
# First, test the connection directly
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=YOUR_ACCOUNT&token=YOUR_TOKEN"
```

This will tell you exactly which part is failing:
- ✅ Account info retrieval
- ✅ Quote API
- ✅ Price history API

If any fail, the response will include troubleshooting steps.

**Get a New Token:**
1. Go to https://developer.schwab.com
2. Sign in with your Schwab account
3. Go to "My Apps"
4. Refresh your OAuth token
5. Copy the new token and use it

---

### 2. **Incorrect Symbol**
You might be using an incorrect ticker symbol.

**Solution:**
```bash
# Test with a known symbol
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "token": "YOUR_TOKEN",
    "account_size": 10000,
    "symbol": "AAPL",
    "days": 60
  }'
```

Try with `AAPL`, `MSFT`, `GOOGL` - all major stocks. If none work, check token validity first.

---

### 3. **Market Data Unavailable**
The symbol exists but market data is not available (e.g., OTC stocks, delisted symbols, non-US exchanges).

**Solution:**
```bash
# Use supported symbols:
# ✅ AAPL, MSFT, GOOGL, TSLA, AMZN
# ✅ SPY, QQQ, DIA, VTI, VOO (ETFs)
# ✅ Any US-listed stock on major exchanges

# Avoid:
# ❌ OTC pink sheets
# ❌ Delisted stocks
# ❌ Crypto (use crypto exchanges instead)
# ❌ Forex pairs
```

---

### 4. **API Rate Limiting**
You might be hitting Schwab API rate limits.

**Solution:**
- Wait a few minutes before retrying
- Reduce frequency of API calls
- Use the `/schwab/test` endpoint to check current status

---

### 5. **Schwab API Service Down**
The Schwab API service might be temporarily unavailable.

**Solution:**
1. Check status at https://developer.schwab.com
2. Wait and retry in a few minutes
3. Contact Schwab support if outage persists

---

## 🔍 Diagnostic Steps

### Step 1: Test Connection
```bash
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=YOUR_ACCOUNT&token=YOUR_TOKEN"
```

**Expected Response (Success):**
```json
{
  "status": "SUCCESS",
  "account": {
    "account_number": "...",
    "buying_power": 50000,
    "cash_balance": 25000,
    "margin_available": 25000,
    "positions": []
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

**Response if Token is Invalid:**
```json
{
  "status": "FAILED",
  "test": "account_info",
  "error": "Could not retrieve account info",
  "troubleshooting": [
    "Check if token is valid and not expired",
    "Verify account number is correct",
    "Check API endpoint URL is accessible"
  ]
}
```

---

### Step 2: Test with Sample Data (No Broker Needed)
If your Schwab connection isn't working, you can test the bot without a broker:

```python
from src.strategy import OptionsStrategy
from src.indicators import TechnicalIndicators

# Create sample price data
prices = [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85]

strategy = OptionsStrategy(account_size=10000)
signal = strategy.generate_signal(prices, current_price=85)

print(f"Signal: {signal['signal']}")
print(f"Entry: {signal['entry']}")
print(f"Stop Loss: {signal['stop_loss']}")
print(f"Take Profit: {signal['take_profit']}")
```

---

### Step 3: Check Logs
View detailed error messages in logs:

```bash
# View today's log
tail -f logs/$(date +%Y%m%d).log

# View specific errors
grep -i "error\|exception" logs/$(date +%Y%m%d).log
```

---

## 📋 Troubleshooting Checklist

- [ ] Token is valid (not expired)
- [ ] Account number is correct (format: XXXXXXXXXX)
- [ ] Symbol is valid (MSFT should work)
- [ ] Market is open (or has data for today)
- [ ] Network connection is stable
- [ ] `/schwab/test` endpoint returns SUCCESS
- [ ] No API rate limiting (wait a few minutes)
- [ ] Schwab service is operational

---

## 💻 Alternative: Use Without Broker

If you don't have Schwab access yet or want to test locally, use the signal generation without broker:

```bash
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{
    "prices": [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85],
    "current_price": 85
  }'
```

This will work without Schwab credentials and shows you the technical analysis is working.

---

## 🚀 Getting Schwab API Access

If you don't have API access yet:

1. **Create Account**
   - Go to https://developer.schwab.com
   - Sign up (free)

2. **Create App**
   - Go to "My Apps"
   - Create new application
   - Get Client ID and Client Secret

3. **Get OAuth Token**
   - Follow OAuth flow in docs
   - Get your access token
   - Use in API calls

4. **Test Connection**
   - Use the `/schwab/test` endpoint
   - Verify everything is working

---

## 📝 Error Messages & Meanings

| Error | Cause | Fix |
|-------|-------|-----|
| "No data for MSFT" | Can't fetch price history | Check token, symbol, network |
| "Authorization failed" | Invalid token | Get new OAuth token |
| "Symbol not found" | Invalid ticker | Use valid US stock symbols |
| "Connection timeout" | Network issue | Check internet, try again |
| "API rate limit exceeded" | Too many requests | Wait and retry |

---

## 🎯 Quick Fix Steps

**If getting "No data for MSFT":**

1. Run test endpoint first:
```bash
curl -X GET "http://127.0.0.1:8000/schwab/test?account_number=YOUR_ACCOUNT&token=YOUR_TOKEN"
```

2. Check the test response for specific failure point

3. Address the issue (e.g., get new token)

4. Try analyze again:
```bash
curl -X POST "http://127.0.0.1:8000/schwab/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "token": "YOUR_TOKEN",
    "symbol": "MSFT"
  }'
```

---

## 📞 Still Not Working?

1. Check logs: `tail -f logs/$(date +%Y%m%d).log`
2. Run `/schwab/test` for diagnostic info
3. Verify Schwab service status
4. Check token validity
5. Verify account number
6. Contact Schwab support if service issues

---

**Remember:** Always test with `/schwab/test` first to isolate the problem! 🔍


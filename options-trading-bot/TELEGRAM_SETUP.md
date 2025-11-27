# Telegram Configuration Guide

## Quick Start

Your `.env` file is already configured with placeholders for Telegram credentials. Here's how to fill them in:

### Step 1: Create Bot (on Telegram)
1. Search for `@BotFather` in Telegram
2. Send `/newbot`
3. Follow prompts to create your bot
4. **Copy your BOT_TOKEN** (looks like: `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Get Chat ID
1. Send any message to your bot (e.g., "hello")
2. Open this URL in your browser (replace `<TOKEN>` with your actual token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Find the `"id"` value inside the `"chat"` object
4. **Copy that ID** (it's a number like `987654321`)

### Step 3: Update .env File
```bash
# Edit your .env file and fill in:
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
```

### Step 4: Verify Setup
```bash
python setup_telegram.py --verify
```

Expected output:
```
✓ BOT_TOKEN configured: 123456789:ABC-DEF...
✓ CHAT_ID configured: 987654321
✓ Telegram is configured and ready to use!
```

## Test Telegram

Once configured, test your setup:

```bash
# Method 1: Interactive test (sends 5 test messages)
python test_telegram.py --env

# Method 2: Run paper trading with live alerts
python paper_trading_telegram.py --env

# Method 3: View example messages
python telegram_demo.py
```

## Configuration File Reference

Your `.env` file now has:

```dotenv
# Telegram Configuration (Optional)
TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
# For multiple recipients: TELEGRAM_CHAT_IDS=123456789,987654321
```

## Features

Once set up, you'll receive Telegram alerts for:

✅ **BUY Signals** - When RSI oversold + MACD bullish
```
🟢 BUY SIGNAL - AAPL
Price: $150.25
Confidence: 85.5%
📊 Indicators: RSI: 28.5, MACD: 0.45
```

✅ **SELL Signals** - When RSI overbought + MACD bearish
```
🔴 SELL SIGNAL - SPY
Price: $445.80
Confidence: 72.0%
📊 Indicators: RSI: 72.5, MACD: -0.32
```

✅ **Daily Summary** - P&L, win rate, best/worst trades
```
📈 DAILY SUMMARY
Trades: 5 | Wins: 3 (60%) | P&L: +$245.75
```

✅ **Error Alerts** - System issues and problems

## Multiple Recipients

To send alerts to multiple people, use:

```dotenv
TELEGRAM_CHAT_IDS=123456789,987654321,555555555
```

Each person must have chat IDs configured. Then run:
```bash
python paper_trading_telegram.py --env
```

## Troubleshooting

**Q: Where is my bot token?**
A: In @BotFather, send `/mybots` → select your bot → click "API Token"

**Q: How do I find my chat ID?**
A: After sending a message to your bot:
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Look for `"chat": {"id": YOUR_ID_HERE}`

**Q: Test sends but paper trading doesn't?**
A: Make sure you use `--env` flag:
   ```bash
   python paper_trading_telegram.py --env
   ```

**Q: Can I use the same bot for multiple accounts?**
A: Yes! Create one bot, then add multiple CHAT_IDs

**Q: How often are alerts sent?**
A: Every time a trade opens or closes (real-time)

## Helper Commands

```bash
# Setup instructions
python setup_telegram.py

# Verify configuration
python setup_telegram.py --verify

# Show current values
python setup_telegram.py --show

# Test connectivity
python test_telegram.py --env

# View example messages
python telegram_demo.py

# Run with alerts
python paper_trading_telegram.py --env
python paper_trading_example.py  # (no alerts)
```

## Security

⚠️ **Important**: Never commit your `.env` file to git!
- `.env` is listed in `.gitignore` for security
- Credentials are stored locally only
- Each developer has their own `.env` file

## Support

If you encounter issues:

1. Check token format: `numbers:letters_and_symbols`
2. Verify chat ID is numeric: `987654321`
3. Test with: `python test_telegram.py`
4. Check demo: `python telegram_demo.py`

Happy trading! 🚀

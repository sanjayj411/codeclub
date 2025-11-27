# Telegram Integration Guide

## Quick Setup (5 minutes)

### 1. Create Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts and get your **Bot Token**

Example Token: `123456789:ABCDefghIJKlmnopQRSTuvwxyz123456789`

### 2. Get Your Chat ID
- Send a message to your bot
- Check: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Find the `chat.id` value in the JSON response

Or run: `python test_telegram.py --get-chat-id`

### 3. Environment Setup
Create `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 4. Run Paper Trading with Alerts
```bash
# Method 1: Command line arguments
python paper_trading_telegram.py --token YOUR_TOKEN --chat-id YOUR_CHAT_ID

# Method 2: Environment variables
python paper_trading_telegram.py --env

# Method 3: No alerts (test without credentials)
python paper_trading_telegram.py
```

## Test Telegram Connection
```bash
python test_telegram.py
```

## Demo and Examples
```bash
python telegram_demo.py
```

## Code Examples

### Basic Usage
```python
from src.notifications.telegram import TelegramNotifier, NotificationConfig
from src.strategy.trading_strategy import TradeSignal
from datetime import datetime

# Setup
config = NotificationConfig(
    token='YOUR_TOKEN',
    chat_ids=['YOUR_CHAT_ID']
)
notifier = TelegramNotifier(config)

# Send trade signal
signal = TradeSignal(
    symbol='AAPL',
    action='BUY',
    confidence=85.5,
    price=150.25,
    timestamp=datetime.now(),
    indicators={'RSI': 28.5, 'MACD': 0.45},
    reason='RSI oversold + MACD bullish crossover'
)
notifier.send_trade_signal_sync(signal)
```

### Integration with Paper Trading
```python
from src.paper_trading import PaperTrader
from src.strategy import TradingStrategy

# Create trader
strategy = TradingStrategy()
trader = PaperTrader(strategy)

# Add Telegram callback
def on_trade_opened(pos_info):
    signal = TradeSignal(
        symbol=pos_info['symbol'],
        action='BUY',
        confidence=85.0,
        price=pos_info['price'],
        timestamp=pos_info['timestamp'],
        indicators={},
        reason='Strategy Signal'
    )
    notifier.send_trade_signal_sync(signal)

trader.on_position_opened = on_trade_opened
```

## Available Methods

All methods have both async and sync versions:

1. **Trade Signals**
   ```python
   notifier.send_trade_signal_sync(signal)
   # Sends: Symbol, Price, Confidence, Indicators, Reason
   ```

2. **Order Confirmations**
   ```python
   notifier.send_order_confirmation_sync(order)
   # Sends: Symbol, Quantity, Price, Total, Order ID
   ```

3. **Daily Summary**
   ```python
   notifier.send_daily_summary_sync(summary)
   # Sends: Trades, Win Rate, P&L, Returns
   ```

4. **Error Alerts**
   ```python
   notifier.send_error_alert_sync(error)
   # Sends: Error title and message
   ```

## Message Format

### Buy Signal Example
```
🟢 BUY SIGNAL - AAPL
━━━━━━━━━━━━━━━━━━━━━━
Price: $150.25
Confidence: 85.5%

📊 Indicators:
• RSI: 28.5 (OVERSOLD)
• MACD: 0.45 (BULLISH)

📝 Reason:
RSI oversold + MACD bullish crossover

Time: 2025-11-27 15:30:45
```

### Daily Summary Example
```
📈 DAILY SUMMARY - 2025-11-27
━━━━━━━━━━━━━━━━━━━━━━
Total Trades: 5
✅ Wins: 3 (60%)
❌ Losses: 2 (40%)

💰 P&L: +$245.75
📊 Return: +2.46%

🏆 Best Trade: +$125.50
📉 Worst Trade: -$45.25

Capital: $10,245.75
```

## Troubleshooting

### Invalid Token
```
Error: 401 Unauthorized
```
- Check token is correct
- Token format: `numbers:letters_and_symbols`
- Use `@BotFather` to verify or regenerate

### Wrong Chat ID
```
Error: 400 Bad Request
```
- Verify chat ID is a number (e.g., 123456789)
- Multiple IDs: `TELEGRAM_CHAT_IDS=123,456,789`
- Run `test_telegram.py --get-chat-id`

### Connection Issues
```
Error: [Errno 110] Connection timed out
```
- Check internet connection
- Telegram API might be blocked in some regions
- Try using a VPN

### Library Not Installed
```
ModuleNotFoundError: No module named 'telegram'
```
- Install: `pip install python-telegram-bot`

## Tips

1. **Test First**: Always test with paper trading before going live
2. **Multiple Recipients**: Send alerts to multiple chats
   ```python
   chat_ids=['chat1', 'chat2', 'chat3']
   ```
3. **Settings**: Customize notification content
   ```python
   settings={
       'include_indicators': True,
       'include_confidence': True,
       'use_emojis': True
   }
   ```
4. **Monitoring**: Check daily summary for strategy performance
5. **Error Alerts**: Gets immediate notification of issues

## Files

- `test_telegram.py` - Test Telegram connectivity
- `telegram_demo.py` - Setup guide and examples
- `paper_trading_telegram.py` - Paper trading with alerts
- `src/notifications/telegram.py` - Main implementation

## Status

✅ Telegram integration fully tested and working
✅ Paper trading with alerts tested (5-15 trades per run)
✅ All notification types working (signals, orders, summaries, alerts)
✅ Ready for live trading deployment

#!/usr/bin/env python
"""
Telegram Integration Demo
Shows how to use Telegram notifications with the trading system
"""
from datetime import datetime
from src.notifications.telegram import TelegramNotifier, NotificationConfig
from src.strategy.trading_strategy import TradeSignal
from src.core.logger import logger


def demo_telegram_setup():
    """Show how to set up Telegram notifications"""
    print("\n" + "="*70)
    print("TELEGRAM NOTIFICATIONS - SETUP GUIDE")
    print("="*70 + "\n")
    
    print("Step 1: Create a Telegram Bot")
    print("-" * 70)
    print("1. Open Telegram and search for '@BotFather'")
    print("2. Send /newbot and follow instructions")
    print("3. Copy your Bot Token (looks like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)")
    print()
    
    print("Step 2: Get Your Chat ID")
    print("-" * 70)
    print("1. Run: python test_telegram.py --get-chat-id")
    print("2. Or send a message to your bot and check:")
    print("   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
    print("3. Look for 'chat' -> 'id' in the JSON response")
    print()
    
    print("Step 3: Set Up in Your Code")
    print("-" * 70)
    print("""
from src.notifications.telegram import TelegramNotifier, NotificationConfig

# Create config
config = NotificationConfig(
    token='YOUR_BOT_TOKEN_HERE',
    chat_ids=['YOUR_CHAT_ID_HERE'],  # Can be a list for multiple recipients
    settings={
        'include_indicators': True,
        'include_confidence': True,
        'use_emojis': True
    }
)

# Create notifier
notifier = TelegramNotifier(config)

# Send trade signal
from src.strategy.trading_strategy import TradeSignal
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
""")
    
    print("\nStep 4: Use in Your Trading System")
    print("-" * 70)
    print("""
# In your paper trading or live trading module:

# On trade entry
notifier.send_trade_signal_sync(signal)

# On order execution
notifier.send_order_confirmation_sync(order_details)

# Daily summary
notifier.send_daily_summary_sync(daily_stats)

# On errors
notifier.send_error_alert_sync(error_details)
""")
    
    print("\n" + "="*70)
    print("Available Methods (All have _sync versions for easy integration):")
    print("="*70)
    print("""
1. send_trade_signal(signal) - Send buy/sell signals
2. send_order_confirmation(order) - Confirm order execution
3. send_daily_summary(summary) - Daily P&L report
4. send_error_alert(error) - Error notifications

All methods have synchronous versions (e.g., send_trade_signal_sync)
that handle the event loop automatically.
""")


def demo_integration():
    """Show integration with paper trading"""
    print("\n" + "="*70)
    print("TELEGRAM + PAPER TRADING INTEGRATION EXAMPLE")
    print("="*70 + "\n")
    
    print("""
# Integrate Telegram with Paper Trading:

from src.paper_trading import PaperTrader
from src.strategy import TradingStrategy
from src.notifications.telegram import TelegramNotifier, NotificationConfig

# Set up Telegram
config = NotificationConfig(token='BOT_TOKEN', chat_ids=['CHAT_ID'])
notifier = TelegramNotifier(config)

# Create paper trader
strategy = TradingStrategy()
trader = PaperTrader(strategy, initial_capital=10000)

# Set up callbacks
def on_position_opened(pos_info):
    signal = TradeSignal(
        symbol=pos_info['symbol'],
        action='BUY',
        confidence=85.0,
        price=pos_info['price'],
        timestamp=pos_info['timestamp'],
        indicators={},
        reason='Strategy signal generated'
    )
    notifier.send_trade_signal_sync(signal)

def on_position_closed(pos_info):
    signal = TradeSignal(
        symbol=pos_info['symbol'],
        action='SELL',
        confidence=85.0,
        price=pos_info.get('exit_price', 0),
        timestamp=datetime.now(),
        indicators={},
        reason=f"Position closed: P&L ${pos_info['pnl']:.2f}"
    )
    notifier.send_trade_signal_sync(signal)

# Attach callbacks
trader.on_position_opened = on_position_opened
trader.on_position_closed = on_position_closed

# Now every trade will send Telegram alerts automatically!
""")


def show_telegram_message_examples():
    """Show what the Telegram messages look like"""
    print("\n" + "="*70)
    print("TELEGRAM MESSAGE EXAMPLES")
    print("="*70 + "\n")
    
    print("BUY SIGNAL MESSAGE:")
    print("-" * 70)
    print("""
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
""")
    
    print("\n\nSELL SIGNAL MESSAGE:")
    print("-" * 70)
    print("""
🔴 SELL SIGNAL - SPY
━━━━━━━━━━━━━━━━━━━━━━
Price: $445.80
Confidence: 72.0%

📊 Indicators:
• RSI: 72.5 (OVERBOUGHT)
• MACD: -0.32 (BEARISH)

📝 Reason:
RSI overbought + MACD bearish crossover

Time: 2025-11-27 15:45:30
""")
    
    print("\n\nORDER CONFIRMATION MESSAGE:")
    print("-" * 70)
    print("""
✅ ORDER FILLED
━━━━━━━━━━━━━━━━━━━━━━
Symbol: AAPL
Action: BUY
Quantity: 10.5 shares
Price: $150.25/share
Total: $1,577.63

Order ID: ORD-20251127-001
Time: 2025-11-27 15:30:50
""")
    
    print("\n\nDAILY SUMMARY MESSAGE:")
    print("-" * 70)
    print("""
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
""")
    
    print("\n\nERROR ALERT MESSAGE:")
    print("-" * 70)
    print("""
⚠️ ERROR ALERT
━━━━━━━━━━━━━━━━━━━━━━
Strategy Error

RSI calculation failed for AAPL - 
invalid price data

Time: 2025-11-27 15:35:20
Action Required: Check data source
""")


def show_environment_setup():
    """Show how to set up environment variables"""
    print("\n" + "="*70)
    print("ENVIRONMENT VARIABLE SETUP")
    print("="*70 + "\n")
    
    print("Create a .env file in your project root:")
    print("-" * 70)
    print("""
# .env file
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321
TELEGRAM_CHAT_IDS=987654321,123456789  # Multiple recipients
""")
    
    print("\nLoad in your code:")
    print("-" * 70)
    print("""
import os
from dotenv import load_dotenv

load_dotenv()

config = NotificationConfig(
    token=os.getenv('TELEGRAM_BOT_TOKEN'),
    chat_ids=os.getenv('TELEGRAM_CHAT_IDS', '').split(',')
)
notifier = TelegramNotifier(config)
""")


if __name__ == '__main__':
    demo_telegram_setup()
    demo_integration()
    show_telegram_message_examples()
    show_environment_setup()
    
    print("\n" + "="*70)
    print("Ready to send Telegram alerts!")
    print("="*70 + "\n")

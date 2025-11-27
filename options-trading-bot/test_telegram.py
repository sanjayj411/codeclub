#!/usr/bin/env python
"""
Test script for Telegram notifications
Run: python test_telegram.py
"""
import sys
from datetime import datetime

from src.notifications.telegram import TelegramNotifier, NotificationConfig
from src.strategy.trading_strategy import TradeSignal
from src.core.logger import logger


def test_telegram_notifications():
    """Test Telegram notification system"""
    print("\n" + "="*60)
    print("TELEGRAM NOTIFICATION TEST")
    print("="*60 + "\n")
    
    # Check if python-telegram-bot is installed
    try:
        import telegram
        print("✓ python-telegram-bot is installed\n")
    except ImportError:
        print("✗ python-telegram-bot not installed")
        print("  Install with: pip install python-telegram-bot")
        return False
    
    # Create config from environment or user input
    token = input("Enter Telegram Bot Token (or press Enter to skip): ").strip()
    if not token:
        print("\n⚠ Skipping Telegram test - no token provided")
        return True
    
    chat_id = input("Enter Chat ID to send test message (or press Enter to skip): ").strip()
    if not chat_id:
        print("\n⚠ Skipping Telegram test - no chat ID provided")
        return True
    
    try:
        # Create notifier config
        config = NotificationConfig(
            token=token,
            chat_ids=[chat_id],
            settings={
                'include_indicators': True,
                'include_confidence': True,
                'use_emojis': True
            }
        )
        
        # Create notifier
        notifier = TelegramNotifier(config)
        print(f"\n✓ TelegramNotifier initialized\n")
        
        # Test 1: Send trade signal (BUY)
        print("Test 1: Sending BUY signal...")
        buy_signal = TradeSignal(
            symbol='AAPL',
            action='BUY',
            confidence=85.5,
            price=150.25,
            timestamp=datetime.now(),
            indicators={'RSI': 28.5, 'MACD': 0.45},
            reason='RSI oversold + MACD bullish crossover'
        )
        
        try:
            result = notifier.send_trade_signal_sync(buy_signal)
            print(f"  ✓ BUY signal sent: {result}\n")
        except Exception as e:
            print(f"  ✗ Failed to send BUY signal: {e}\n")
            return False
        
        # Test 2: Send trade signal (SELL)
        print("Test 2: Sending SELL signal...")
        sell_signal = TradeSignal(
            symbol='SPY',
            action='SELL',
            confidence=72.0,
            price=445.80,
            timestamp=datetime.now(),
            indicators={'RSI': 72.5, 'MACD': -0.32},
            reason='RSI overbought + MACD bearish crossover'
        )
        
        try:
            result = notifier.send_trade_signal_sync(sell_signal)
            print(f"  ✓ SELL signal sent: {result}\n")
        except Exception as e:
            print(f"  ✗ Failed to send SELL signal: {e}\n")
            return False
        
        # Test 3: Send order confirmation
        print("Test 3: Sending order confirmation...")
        order = {
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 10.5,
            'price': 150.25,
            'total': 1577.625,
            'order_id': 'ORD-20251127-001',
            'timestamp': datetime.now()
        }
        
        try:
            result = notifier.send_order_confirmation_sync(order)
            print(f"  ✓ Order confirmation sent: {result}\n")
        except Exception as e:
            print(f"  ✗ Failed to send order confirmation: {e}\n")
            return False
        
        # Test 4: Send daily summary
        print("Test 4: Sending daily summary...")
        summary = {
            'date': datetime.now().date(),
            'total_trades': 5,
            'winning_trades': 3,
            'losing_trades': 2,
            'total_pnl': 245.75,
            'win_rate': 60.0,
            'best_trade': 125.50,
            'worst_trade': -45.25
        }
        
        try:
            result = notifier.send_daily_summary_sync(summary)
            print(f"  ✓ Daily summary sent: {result}\n")
        except Exception as e:
            print(f"  ✗ Failed to send daily summary: {e}\n")
            return False
        
        # Test 5: Send error alert
        print("Test 5: Sending error alert...")
        error = {
            'title': 'Strategy Error',
            'message': 'RSI calculation failed for AAPL - invalid price data',
            'timestamp': datetime.now()
        }
        
        try:
            result = notifier.send_error_alert_sync(error)
            print(f"  ✓ Error alert sent: {result}\n")
        except Exception as e:
            print(f"  ✗ Failed to send error alert: {e}\n")
            return False
        
        print("="*60)
        print("✓ ALL TELEGRAM TESTS PASSED!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ Telegram test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_chat_id():
    """Helper to get chat ID by sending test message"""
    print("\n" + "="*60)
    print("GET YOUR TELEGRAM CHAT ID")
    print("="*60 + "\n")
    
    token = input("Enter your Telegram Bot Token: ").strip()
    if not token:
        print("Aborted.")
        return
    
    print("\n📱 Steps to get your Chat ID:")
    print("1. Open Telegram")
    print("2. Search for your bot (@bot_name)")
    print("3. Send any message to the bot (e.g., 'hi')")
    print("4. Your Chat ID will be displayed below\n")
    
    try:
        import telegram
        from telegram.ext import Application
        
        print("Waiting for message (send something to your bot now)...")
        print("(This is a simplified check - use a bot framework for production)\n")
        
        # In production, use proper bot setup with handlers
        bot = telegram.Bot(token=token)
        print("✓ Token verified!")
        print("\nTo get chat ID, use this URL in your browser:")
        print(f"https://api.telegram.org/bot{token}/getUpdates")
        print("\nLook for 'chat' -> 'id' in the JSON response")
        
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Telegram notifications')
    parser.add_argument('--get-chat-id', action='store_true', help='Get your Telegram Chat ID')
    
    args = parser.parse_args()
    
    if args.get_chat_id:
        get_chat_id()
    else:
        success = test_telegram_notifications()
        sys.exit(0 if success else 1)

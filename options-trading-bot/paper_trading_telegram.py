"""
Paper Trading + Telegram Integration Example
Demonstrates real-time notifications for all trades
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
import random

from dotenv import load_dotenv

from src.paper_trading import PaperTrader
from src.strategy import TradingStrategy
from src.notifications.telegram import TelegramNotifier, NotificationConfig
from src.strategy.trading_strategy import TradeSignal
from src.core.logger import logger

# Load environment variables from .env file
load_dotenv(Path('.env'))


def generate_sample_data():
    """Generate sample OHLCV data"""
    symbols = ['AAPL', 'SPY', 'QQQ']
    data = {}
    
    for symbol in symbols:
        candles = []
        price = 100.0
        
        for i in range(100):
            timestamp = datetime.now() - timedelta(days=100-i)
            change = random.uniform(-2, 2)
            open_price = price
            close_price = price + change
            high_price = max(open_price, close_price) + abs(random.uniform(0, 1))
            low_price = min(open_price, close_price) - abs(random.uniform(0, 1))
            
            candles.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.randint(1000000, 10000000)
            })
            
            price = close_price
        
        data[symbol] = candles
    
    return data


def run_paper_trading_with_telegram(notifier=None):
    """Run paper trading with optional Telegram notifications"""
    logger.info("Starting paper trading with Telegram integration...")
    
    # Generate sample data
    price_data = generate_sample_data()
    
    # Create strategy and paper trader
    strategy = TradingStrategy()
    paper_trader = PaperTrader(
        strategy=strategy,
        initial_capital=10000.0,
        commission_percent=0.1,
        slippage_percent=0.05
    )
    
    # Set up callbacks with Telegram notifications
    def on_position_opened(pos_info):
        msg = (f"🟢 POSITION OPENED: {pos_info['symbol']}\n"
               f"Quantity: {pos_info['quantity']:.4f}\n"
               f"Entry Price: ${pos_info['price']:.2f}")
        logger.info(msg)
        
        if notifier:
            try:
                notifier.send_trade_signal_sync(
                    symbol=pos_info['symbol'],
                    action='BUY',
                    price=pos_info['price'],
                    confidence=85.0,
                    indicators={}
                )
            except Exception as e:
                logger.warning(f"Could not send Telegram notification: {e}")
    
    def on_position_closed(pos_info):
        status = "✅ WIN" if pos_info['pnl'] > 0 else "❌ LOSS"
        msg = (f"{status}: {pos_info['symbol']}\n"
               f"P&L: ${pos_info['pnl']:.2f} ({pos_info['pnl_pct']:.2f}%)")
        logger.info(msg)
        
        if notifier:
            try:
                notifier.send_trade_signal_sync(
                    symbol=pos_info['symbol'],
                    action='SELL',
                    price=pos_info.get('exit_price', 0),
                    confidence=85.0,
                    indicators={}
                )
            except Exception as e:
                logger.warning(f"Could not send Telegram notification: {e}")
    
    paper_trader.on_position_opened = on_position_opened
    paper_trader.on_position_closed = on_position_closed
    
    # Get all timestamps
    all_timestamps = set()
    for symbol, candles in price_data.items():
        for candle in candles:
            all_timestamps.add(candle['timestamp'])
    
    timestamps = sorted(all_timestamps)
    logger.info(f"Simulating {len(timestamps)} time periods...")
    
    # Simulate trading
    for timestamp in timestamps:
        current_prices = {}
        closes_by_symbol = {symbol: [] for symbol in price_data.keys()}
        
        for symbol, candles in price_data.items():
            candles_up_to = [c for c in candles if c['timestamp'] <= timestamp]
            if candles_up_to:
                current_prices[symbol] = candles_up_to[-1]['close']
                closes_by_symbol[symbol] = [c['close'] for c in candles_up_to]
        
        paper_trader.update_positions(current_prices)
        
        for symbol, closes in closes_by_symbol.items():
            if not closes or len(closes) < 30:
                continue
            
            if symbol in current_prices:
                paper_trader.analyze_and_trade(
                    symbol,
                    closes,
                    current_prices[symbol]
                )
    
    # Close remaining positions
    final_timestamp = timestamps[-1] if timestamps else datetime.now()
    for symbol in list(paper_trader.positions.keys()):
        if symbol in current_prices:
            paper_trader.close_position(symbol, current_prices[symbol], final_timestamp)
    
    # Print summary
    paper_trader.print_summary()
    
    # Send daily summary via Telegram
    if notifier:
        summary = paper_trader.get_portfolio_summary()
        try:
            daily_summary = {
                'date': datetime.now().date(),
                'total_trades': summary['trades_executed'],
                'winning_trades': summary['winning_trades'],
                'losing_trades': summary['losing_trades'],
                'total_pnl': summary['realized_pnl'],
                'win_rate': summary['win_rate'],
                'best_trade': max([t['pnl'] for t in paper_trader.closed_trades], default=0),
                'worst_trade': min([t['pnl'] for t in paper_trader.closed_trades], default=0)
            }
            notifier.send_daily_summary_sync(daily_summary)
            logger.info("Daily summary sent via Telegram")
        except Exception as e:
            logger.warning(f"Could not send daily summary: {e}")
    
    # Export trades
    paper_trader.export_trades('paper_trades_telegram.json')
    
    return paper_trader


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper trading with Telegram integration')
    parser.add_argument('--token', help='Telegram bot token')
    parser.add_argument('--chat-id', help='Telegram chat ID')
    parser.add_argument('--env', action='store_true', help='Load from environment variables')
    
    args = parser.parse_args()
    
    notifier = None
    
    # Set up Telegram if credentials provided
    if args.env:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            try:
                config = NotificationConfig(
                    enabled=True,
                    token=token,
                    chat_ids=[chat_id],
                    include_indicators=True,
                    include_charts=False
                )
                notifier = TelegramNotifier(config)
                logger.info("✓ Telegram notifier initialized from environment")
            except Exception as e:
                logger.warning(f"Could not initialize Telegram: {e}")
        else:
            logger.warning("Telegram credentials not found in environment")
    
    elif args.token and args.chat_id:
        try:
            config = NotificationConfig(
                enabled=True,
                token=args.token,
                chat_ids=[args.chat_id],
                include_indicators=True,
                include_charts=False
            )
            notifier = TelegramNotifier(config)
            logger.info("✓ Telegram notifier initialized from arguments")
        except Exception as e:
            logger.warning(f"Could not initialize Telegram: {e}")
    else:
        logger.info("Running without Telegram notifications")
        logger.info("To enable: python paper_trading_telegram.py --token YOUR_TOKEN --chat-id YOUR_CHAT_ID")
    
    # Run paper trading
    trader = run_paper_trading_with_telegram(notifier)
    
    return trader


if __name__ == '__main__':
    main()

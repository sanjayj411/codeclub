"""
Example paper trading script for RSI/MACD strategy
Simulates live trading without risking capital
"""
import sys
from datetime import datetime, timedelta
import random

from src.paper_trading import PaperTrader
from src.strategy import TradingStrategy
from src.core.logger import logger


def generate_sample_data_with_timestamps():
    """Generate sample OHLCV data with streaming simulation"""
    symbols = ['AAPL', 'SPY', 'QQQ']
    data = {}
    
    for symbol in symbols:
        candles = []
        price = 100.0
        
        # Generate 100 days of sample data
        for i in range(100):
            timestamp = datetime.now() - timedelta(days=100-i)
            
            # Random walk
            change = random.uniform(-2, 2)
            open_price = price
            close_price = price + change
            high_price = max(open_price, close_price) + abs(random.uniform(0, 1))
            low_price = min(open_price, close_price) - abs(random.uniform(0, 1))
            volume = random.randint(1000000, 10000000)
            
            candles.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            price = close_price
        
        data[symbol] = candles
    
    return data


def run_paper_trading():
    """Run paper trading simulation"""
    logger.info("Starting paper trading simulation...")
    
    # Generate sample data
    price_data = generate_sample_data_with_timestamps()
    
    # Create strategy and paper trader
    strategy = TradingStrategy()
    paper_trader = PaperTrader(
        strategy=strategy,
        initial_capital=10000.0,
        commission_percent=0.1,  # 0.1% per trade
        slippage_percent=0.05    # 0.05% slippage
    )
    
    # Set up notification callbacks
    def on_order_filled(order_info):
        logger.info(f"Order filled: {order_info}")
    
    def on_position_opened(pos_info):
        logger.info(f"Position opened: {pos_info['symbol']} - "
                   f"{pos_info['quantity']:.4f} @ ${pos_info['price']:.2f}")
    
    def on_position_closed(pos_info):
        status = "WIN ✓" if pos_info['pnl'] > 0 else "LOSS ✗"
        logger.info(f"Position closed: {pos_info['symbol']} - "
                   f"${pos_info['pnl']:.2f} ({pos_info['pnl_pct']:.2f}%) {status}")
    
    paper_trader.on_position_opened = on_position_opened
    paper_trader.on_position_closed = on_position_closed
    
    # Get all timestamps and sort them
    all_timestamps = set()
    for symbol, candles in price_data.items():
        for candle in candles:
            all_timestamps.add(candle['timestamp'])
    
    timestamps = sorted(all_timestamps)
    
    # Simulate live trading
    logger.info(f"Simulating {len(timestamps)} time periods...")
    
    for timestamp in timestamps:
        # Get current prices for all symbols
        current_prices = {}
        closes_by_symbol = {symbol: [] for symbol in price_data.keys()}
        
        for symbol, candles in price_data.items():
            candles_up_to = [c for c in candles if c['timestamp'] <= timestamp]
            if candles_up_to:
                current_prices[symbol] = candles_up_to[-1]['close']
                closes_by_symbol[symbol] = [c['close'] for c in candles_up_to]
        
        # Update position prices
        paper_trader.update_positions(current_prices)
        
        # Analyze each symbol for trading signals
        for symbol, closes in closes_by_symbol.items():
            if not closes or len(closes) < 30:
                continue
            
            if symbol in current_prices:
                paper_trader.analyze_and_trade(
                    symbol,
                    closes,
                    current_prices[symbol]
                )
    
    # Close any remaining positions
    final_timestamp = timestamps[-1] if timestamps else datetime.now()
    for symbol in list(paper_trader.positions.keys()):
        if symbol in current_prices:
            paper_trader.close_position(symbol, current_prices[symbol], final_timestamp)
    
    # Print results
    paper_trader.print_summary()
    
    # Export trades
    paper_trader.export_trades('paper_trades.json')
    
    # Print open positions
    if paper_trader.positions:
        print("\n====== OPEN POSITIONS ======")
        for symbol, position in paper_trader.positions.items():
            summary = paper_trader.get_position_summary(symbol)
            if summary:
                print(f"\n{symbol}:")
                print(f"  Quantity: {summary['quantity']:.4f}")
                print(f"  Entry: ${summary['entry_price']:.2f}")
                print(f"  Current: ${summary['current_price']:.2f}")
                print(f"  Unrealized P&L: ${summary['unrealized_pnl']:.2f} ({summary['unrealized_pnl_pct']:.2f}%)")
    
    # Print trade details
    if paper_trader.closed_trades:
        print("\n====== TRADE DETAILS (First 10) ======")
        for i, trade in enumerate(paper_trader.closed_trades[:10], 1):
            print(f"\nTrade {i}: {trade['symbol']}")
            print(f"  Entry: ${trade['entry_price']:.2f}")
            print(f"  Exit: ${trade['exit_price']:.2f}")
            print(f"  Quantity: {trade['quantity']:.4f}")
            print(f"  P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")


if __name__ == '__main__':
    try:
        run_paper_trading()
    except Exception as e:
        logger.error(f"Paper trading error: {e}")
        import traceback
        traceback.print_exc()

"""
Example backtest script for RSI/MACD strategy
Run: python backtest_example.py
"""
import sys
from datetime import datetime, timedelta
import json

from src.backtesting import Backtester
from src.strategy import TradingStrategy
from src.brokers import SchwabBrokerAPI
from src.core.logger import logger


def generate_sample_data() -> dict:
    """
    Generate sample OHLCV data for testing
    In production, this would come from Schwab API or CSV files
    """
    import random
    
    data = {}
    symbols = ['AAPL', 'SPY', 'QQQ']
    
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


def backtest_with_live_data():
    """Backtest using live Schwab API data"""
    try:
        # Initialize Schwab API
        api = SchwabBrokerAPI(account_number="0")  # Account number will be fetched
        
        # Try to load credentials (tokens are auto-loaded in __init__)
        if not api.access_token:
            logger.error("Unable to load Schwab credentials. Run 'python main.py auth' first.")
            return
        
        # Get account hash
        account_hash = api.get_account_hash()
        if not account_hash:
            logger.error("Unable to get account hash")
            return
        
        # Get price history for multiple symbols
        symbols = ['AAPL', 'SPY', 'QQQ']
        price_data = {}
        
        for symbol in symbols:
            logger.info(f"Fetching price history for {symbol}...")
            history = api.get_price_history(symbol, days=60)
            
            if history and 'candles' in history:
                candles = []
                for candle in history['candles']:
                    candles.append({
                        'timestamp': datetime.fromtimestamp(candle['datetime'] / 1000),
                        'open': candle['open'],
                        'high': candle['high'],
                        'low': candle['low'],
                        'close': candle['close'],
                        'volume': candle.get('volume', 0)
                    })
                price_data[symbol] = candles
                logger.info(f"Loaded {len(candles)} candles for {symbol}")
        
        if not price_data:
            logger.error("No price data retrieved")
            return
        
        # Run backtest
        strategy = TradingStrategy()
        backtester = Backtester(strategy, initial_capital=10000.0)
        stats = backtester.run(price_data)
        
        # Print results
        print(backtester.get_summary())
        
        # Print trade details
        if stats.trades:
            print("\n====== TRADE DETAILS ======")
            for i, trade in enumerate(stats.trades[:10], 1):  # Show first 10 trades
                print(f"\nTrade {i}: {trade.symbol}")
                print(f"  Entry: ${trade.entry_price:.2f} @ {trade.entry_time}")
                print(f"  Exit: ${trade.exit_price:.2f} @ {trade.exit_time}")
                print(f"  P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")
        
        # Save results to file
        results = {
            'total_trades': stats.total_trades,
            'winning_trades': stats.winning_trades,
            'losing_trades': stats.losing_trades,
            'win_rate': stats.win_rate,
            'total_pnl': stats.total_pnl,
            'total_pnl_pct': stats.total_pnl_pct,
            'avg_win': stats.avg_win,
            'avg_loss': stats.avg_loss,
            'profit_factor': stats.profit_factor,
            'max_drawdown': stats.max_drawdown,
            'max_drawdown_pct': stats.max_drawdown_pct,
            'sharpe_ratio': stats.sharpe_ratio
        }
        
        with open('backtest_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved to backtest_results.json")
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        import traceback
        traceback.print_exc()


def backtest_with_sample_data():
    """Backtest using generated sample data"""
    logger.info("Running backtest with sample data...")
    
    # Generate sample data
    price_data = generate_sample_data()
    
    # Create strategy and backtester
    strategy = TradingStrategy()
    backtester = Backtester(strategy, initial_capital=10000.0)
    
    # Run backtest
    stats = backtester.run(price_data)
    
    # Print results
    print(backtester.get_summary())
    
    # Print trade details
    if stats.trades:
        print("\n====== TRADE DETAILS ======")
        for i, trade in enumerate(stats.trades[:10], 1):
            print(f"\nTrade {i}: {trade.symbol}")
            print(f"  Entry: ${trade.entry_price:.2f} @ {trade.entry_time}")
            print(f"  Exit: ${trade.exit_price:.2f} @ {trade.exit_time}")
            print(f"  P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backtest trading strategy')
    parser.add_argument('--live', action='store_true', help='Use live Schwab API data')
    parser.add_argument('--sample', action='store_true', help='Use sample data')
    
    args = parser.parse_args()
    
    if args.live:
        try:
            backtest_with_live_data()
        except Exception as e:
            logger.error(f"Live data backtest failed: {e}")
            logger.info("Falling back to sample data...")
            backtest_with_sample_data()
    else:
        # Default to sample data
        backtest_with_sample_data()

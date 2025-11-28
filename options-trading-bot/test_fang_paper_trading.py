#!/usr/bin/env python
"""
Paper trading simulation on FANG stocks with 2% drawdown filter
"""
import random
from datetime import datetime, timedelta
from src.paper_trading.trader import PaperTrader
from src.strategy import TradingStrategy
from src.core.logger import logger

def generate_fang_price_data(num_candles: int = 100) -> dict:
    """Generate OHLCV data for FANG stocks"""
    
    symbols = {
        'META': 450.0,
        'AAPL': 235.0,
        'NFLX': 280.0,
        'GOOGL': 140.0
    }
    
    data = {}
    
    for symbol, base_price in symbols.items():
        candles = []
        price = base_price
        
        for i in range(num_candles):
            timestamp = datetime.now() - timedelta(days=num_candles - i)
            
            # Generate realistic OHLCV
            daily_change = random.gauss(0.1, 2.5)  # Mean 0.1%, std dev 2.5%
            change_amount = price * (daily_change / 100)
            
            open_price = price
            close_price = price + change_amount
            high_price = max(open_price, close_price) + abs(random.uniform(0, 1.5))
            low_price = min(open_price, close_price) - abs(random.uniform(0, 1.0))
            
            candles.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.randint(10000000, 100000000)
            })
            
            price = close_price
        
        data[symbol] = candles
    
    return data

def run_fang_paper_trading():
    """Run paper trading on FANG stocks"""
    
    print("\n" + "=" * 100)
    print("PAPER TRADING SIMULATION: FANG STOCKS WITH 2% DRAWDOWN FILTER")
    print("=" * 100)
    
    # Create strategy with 2% drawdown filter
    strategy = TradingStrategy(min_drawdown_for_buy=2.0)
    
    # Create paper trader
    trader = PaperTrader(
        strategy=strategy,
        initial_capital=50000.0,
        commission_percent=0.1,
        slippage_percent=0.05
    )
    
    print(f"\n💼 Initial Setup:")
    print(f"   Capital: ${trader.capital:,.2f}")
    print(f"   Commission: {trader.commission_percent}%")
    print(f"   Slippage: {trader.slippage_percent}%")
    print(f"   Position Size: 20% per trade")
    
    # Generate FANG price data
    price_data = generate_fang_price_data(100)
    
    print(f"\n📊 Trading on: META, AAPL, NFLX, GOOGL")
    print(f"   Duration: {len(price_data['META'])} candles (days)")
    
    # Get all timestamps
    all_timestamps = set()
    for symbol, candles in price_data.items():
        for candle in candles:
            all_timestamps.add(candle['timestamp'])
    
    timestamps = sorted(all_timestamps)
    
    trades_by_symbol = {'META': 0, 'AAPL': 0, 'NFLX': 0, 'GOOGL': 0}
    
    # Simulate trading
    for timestamp in timestamps:
        current_prices = {}
        closes_by_symbol = {symbol: [] for symbol in price_data.keys()}
        
        # Collect data for each symbol at this timestamp
        for symbol, candles in price_data.items():
            for candle in candles:
                if candle['timestamp'] <= timestamp:
                    closes_by_symbol[symbol].append(candle['close'])
                    if candle['timestamp'] == timestamp:
                        current_prices[symbol] = candle['close']
        
        # Analyze each symbol
        for symbol in price_data.keys():
            if symbol not in current_prices:
                continue
            
            closes = closes_by_symbol[symbol]
            price = current_prices[symbol]
            
            signal = strategy.analyze(symbol, closes, price)
            
            # Execute trades
            if signal.action == 'BUY':
                trader.open_position(symbol, price, timestamp)
                trades_by_symbol[symbol] += 1
                
            elif signal.action == 'SELL':
                trader.close_position(symbol, price, timestamp)
    
    # Print results
    print("\n" + "-" * 100)
    print("TRADING RESULTS")
    print("-" * 100)
    
    print(f"\n📈 Portfolio Performance:")
    print(f"   Initial Capital:  ${50000.0:,.2f}")
    print(f"   Current Capital:  ${trader.capital:,.2f}")
    
    summary = trader.get_portfolio_summary()
    total_equity = summary.get('total_equity', trader.capital)
    print(f"   Total Equity:     ${total_equity:,.2f}")
    print(f"   Total Return:     ${total_equity - 50000:,.2f} ({((total_equity / 50000) - 1) * 100:.2f}%)")
    
    print(f"\n📊 Trading Statistics:")
    print(f"   Total Trades:     {summary['trades_executed']}")
    print(f"   Winning Trades:   {summary['winning_trades']}")
    print(f"   Losing Trades:    {summary['losing_trades']}")
    print(f"   Win Rate:         {summary['win_rate']:.1f}%")
    print(f"   Realized P&L:     ${summary['realized_pnl']:,.2f}")
    
    print(f"\n📋 Trades by Symbol:")
    for symbol in sorted(trades_by_symbol.keys()):
        print(f"   {symbol}: {trades_by_symbol[symbol]} trades")
    
    # Print closed trades
    if trader.closed_trades:
        print(f"\n📑 Closed Trades (First 5):")
        for i, trade in enumerate(trader.closed_trades[:5], 1):
            print(f"   {i}. {trade['symbol']:6} Entry: ${trade['entry_price']:<8.2f} Exit: ${trade['exit_price']:<8.2f} "
                  f"P&L: ${trade['pnl']:<10.2f} ({trade['pnl_pct']:+6.2f}%)")
    
    print("\n" + "=" * 100)
    print("✅ FANG PAPER TRADING TEST COMPLETE")
    print("=" * 100 + "\n")
    
    return trader

if __name__ == '__main__':
    trader = run_fang_paper_trading()

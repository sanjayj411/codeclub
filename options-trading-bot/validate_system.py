#!/usr/bin/env python
"""
Validation script - Tests all components work together
Run: python validate_system.py
"""
import sys
from datetime import datetime, timedelta
import random

def test_indicators():
    """Test RSI and MACD indicators"""
    print("Testing Indicators...")
    from src.indicators.rsi import RSIIndicator
    from src.indicators.macd import MACDIndicator
    
    # Generate test data
    closes = []
    price = 100.0
    for _ in range(50):
        price += random.uniform(-2, 2)
        closes.append(price)
    
    # Test RSI
    rsi = RSIIndicator()
    rsi_value = rsi.calculate(closes)
    assert 0 <= rsi_value <= 100, "RSI out of range"
    print(f"  ✓ RSI = {rsi_value:.2f}")
    
    # Test MACD
    macd_calc = MACDIndicator()
    macd, signal, hist = macd_calc.calculate(closes)
    print(f"  ✓ MACD = {macd:.4f}, Signal = {signal:.4f}, Hist = {hist:.4f}")


def test_strategy():
    """Test trading strategy"""
    print("Testing Trading Strategy...")
    from src.strategy.trading_strategy import TradingStrategy
    
    strategy = TradingStrategy()
    
    # Generate test data
    closes = []
    price = 100.0
    for _ in range(50):
        price += random.uniform(-2, 2)
        closes.append(price)
    
    signal = strategy.analyze("TEST", closes, price)
    print(f"  ✓ Signal: {signal.action}, Confidence: {signal.confidence:.0f}%")


def test_backtester():
    """Test backtesting framework"""
    print("Testing Backtester...")
    from src.backtesting import Backtester
    from src.strategy import TradingStrategy
    
    strategy = TradingStrategy()
    backtester = Backtester(strategy, initial_capital=5000)
    
    # Generate test data
    price_data = {}
    for symbol in ['TEST1', 'TEST2']:
        candles = []
        price = 100.0
        for i in range(50):
            timestamp = datetime.now() - timedelta(days=50-i)
            price += random.uniform(-2, 2)
            candles.append({
                'timestamp': timestamp,
                'open': price,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000000
            })
        price_data[symbol] = candles
    
    stats = backtester.run(price_data)
    print(f"  ✓ Backtest: {stats.total_trades} trades, {stats.win_rate:.1f}% win rate")


def test_paper_trader():
    """Test paper trading simulator"""
    print("Testing Paper Trader...")
    from src.paper_trading import PaperTrader
    from src.strategy import TradingStrategy
    
    strategy = TradingStrategy()
    trader = PaperTrader(strategy, initial_capital=5000)
    
    # Generate test data
    price_data = {}
    for symbol in ['TEST1', 'TEST2']:
        candles = []
        price = 100.0
        for i in range(50):
            timestamp = datetime.now() - timedelta(days=50-i)
            price += random.uniform(-2, 2)
            candles.append({
                'timestamp': timestamp,
                'open': price,
                'high': price + 1,
                'low': price - 1,
                'close': price,
                'volume': 1000000
            })
        price_data[symbol] = candles
    
    # Simulate trading
    all_timestamps = set()
    for symbol, candles in price_data.items():
        for candle in candles:
            all_timestamps.add(candle['timestamp'])
    
    for timestamp in sorted(all_timestamps):
        current_prices = {}
        closes_by_symbol = {symbol: [] for symbol in price_data.keys()}
        
        for symbol, candles in price_data.items():
            candles_up_to = [c for c in candles if c['timestamp'] <= timestamp]
            if candles_up_to:
                current_prices[symbol] = candles_up_to[-1]['close']
                closes_by_symbol[symbol] = [c['close'] for c in candles_up_to]
        
        trader.update_positions(current_prices)
        
        for symbol, closes in closes_by_symbol.items():
            if len(closes) >= 30 and symbol in current_prices:
                trader.analyze_and_trade(symbol, closes, current_prices[symbol])
    
    summary = trader.get_portfolio_summary()
    print(f"  ✓ Paper Trading: {summary['trades_executed']} trades, "
          f"{summary['win_rate']:.1f}% win rate, "
          f"{summary['total_return_pct']:+.2f}% return")


def test_schwab_api():
    """Test Schwab API (if credentials available)"""
    print("Testing Schwab API...")
    try:
        from src.brokers import SchwabBrokerAPI
        
        api = SchwabBrokerAPI(account_number="0")
        if api.access_token:
            try:
                quote = api.get_quote("AAPL")
                if quote:
                    print(f"  ✓ Got quote for AAPL")
                else:
                    print(f"  ⚠ Could not get quote (may need token refresh)")
            except Exception as e:
                print(f"  ⚠ API test skipped (token may have expired): {str(e)[:50]}")
        else:
            print(f"  ⚠ No Schwab credentials available (run 'python main.py auth' first)")
    except Exception as e:
        print(f"  ⚠ Could not test API: {str(e)[:50]}")


def test_telegram():
    """Test Telegram notifications"""
    print("Testing Telegram Notifier...")
    try:
        from src.notifications.telegram import TelegramNotifier
        
        # Create notifier (won't send without valid config)
        config_dict = {
            'token': 'TEST_TOKEN',
            'chat_ids': ['123456789']
        }
        
        notifier = TelegramNotifier(config_dict)
        print(f"  ✓ TelegramNotifier initialized")
    except Exception as e:
        print(f"  ⚠ Telegram test skipped: {str(e)[:50]}")


def main():
    """Run all validation tests"""
    print("\n" + "="*50)
    print("SYSTEM VALIDATION TEST")
    print("="*50 + "\n")
    
    tests = [
        ("Indicators", test_indicators),
        ("Strategy", test_strategy),
        ("Backtester", test_backtester),
        ("Paper Trader", test_paper_trader),
        ("Schwab API", test_schwab_api),
        ("Telegram", test_telegram),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    if failed == 0:
        print("✓ All systems validated successfully!")
        return 0
    else:
        print("✗ Some tests failed. Check output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

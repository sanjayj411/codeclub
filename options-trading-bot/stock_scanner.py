#!/usr/bin/env python3
"""
Stock Scanner with Options Trigger

Scans provided list of stocks for technical signals (RSI + MACD + Bollinger Bands).
When stock BUY signal triggered, analyzes options for call opportunities.

Usage:
    python stock_scanner.py --stocks AAPL,SPY,QQQ --days-to-expiry 30
    python stock_scanner.py --config stocks.txt --live
    python stock_scanner.py --help
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import json

from src.strategy.enhanced_strategy import (
    EnhancedStockStrategy,
    StockSignal,
    OptionsOpportunity,
    format_stock_signal,
    format_options_opportunity
)
from src.core.logger import logger

# Try to import Schwab API, but don't fail if not available
try:
    from src.api.schwab import SchwabBrokerAPI
except ImportError:
    SchwabBrokerAPI = None
    logger.debug("Schwab API not available, using sample data only")


class StockScanner:
    """Stock scanner with options trigger capability"""
    
    def __init__(
        self,
        strategy: EnhancedStockStrategy,
        api: Optional[object] = None,
        use_live_data: bool = False
    ):
        """
        Initialize scanner
        
        Args:
            strategy: EnhancedStockStrategy instance
            api: Optional Schwab API for live data
            use_live_data: Use live API data vs sample data
        """
        self.strategy = strategy
        self.api = api
        self.use_live_data = use_live_data
        self.scan_results: Dict[str, Dict] = {}
    
    def get_price_data(
        self,
        symbol: str,
        days: int = 60
    ) -> Optional[Tuple[List[float], float]]:
        """
        Get price data from API or sample
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            
        Returns:
            Tuple of (closes_list, current_price) or None
        """
        if self.use_live_data and self.api:
            try:
                history = self.api.get_price_history(symbol, days=days)
                if not history or 'candles' not in history:
                    logger.warning(f"{symbol}: No data from API")
                    return self._generate_sample_data(symbol, days)
                
                candles = history['candles']
                closes = [float(c['close']) for c in candles]
                current_price = float(candles[-1]['close'])
                
                logger.info(f"{symbol}: Retrieved {len(closes)} candles from Schwab API")
                return closes, current_price
                
            except Exception as e:
                logger.error(f"{symbol}: Error fetching from API - {e}")
                logger.info(f"{symbol}: Falling back to sample data")
                return self._generate_sample_data(symbol, days)
        else:
            # Use sample data
            return self._generate_sample_data(symbol, days)
    
    def _generate_sample_data(self, symbol: str, days: int) -> Tuple[List[float], float]:
        """Generate consistent sample data for a symbol"""
        import random
        random.seed(hash(symbol) % 2**32)  # Consistent data per symbol
        
        closes = [100]
        for _ in range(days - 1):
            change = random.uniform(-2, 2)
            closes.append(closes[-1] * (1 + change / 100))
        
        return closes, closes[-1]
    
    def scan_single_stock(
        self,
        symbol: str,
        days_of_history: int = 60
    ) -> Dict:
        """
        Scan single stock for signals
        
        Args:
            symbol: Stock symbol
            days_of_history: Days to retrieve
            
        Returns:
            Dictionary with scan results
        """
        logger.info(f"Scanning {symbol}...")
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'stock_signal': None,
            'options_opportunity': None,
            'error': None
        }
        
        try:
            # Get price data
            price_data = self.get_price_data(symbol, days_of_history)
            if not price_data:
                result['error'] = 'Failed to retrieve price data'
                logger.warning(f"{symbol}: {result['error']}")
                return result
            
            closes, current_price = price_data
            
            # Analyze stock
            stock_signal = self.strategy.analyze_stock(symbol, closes, current_price)
            
            if not stock_signal:
                logger.info(f"{symbol}: No trading signal")
                return result
            
            result['stock_signal'] = {
                'action': stock_signal.action,
                'confidence': stock_signal.confidence,
                'signal_type': stock_signal.signal_type,
                'price': stock_signal.price,
                'rsi': stock_signal.rsi,
                'macd': stock_signal.macd,
                'bb_position': stock_signal.bb_position,
                'reason': stock_signal.reason
            }
            
            # If BUY signal, analyze options
            if stock_signal.action == 'BUY':
                options_opp = self.strategy.analyze_options_for_stock_signal(
                    stock_signal,
                    closes,
                    current_price,
                    days_to_expiry=30,
                    num_simulations=5000
                )
                
                if options_opp:
                    result['options_opportunity'] = {
                        'strike': options_opp.strike_price,
                        'entry_price': options_opp.entry_price,
                        'delta': options_opp.delta,
                        'gamma': options_opp.gamma,
                        'vega': options_opp.vega,
                        'theta': options_opp.theta,
                        'prob_itm': options_opp.prob_itm,
                        'var_95': options_opp.var_95,
                        'recommendation': options_opp.recommendation,
                        'confidence': options_opp.confidence,
                        'contracts': options_opp.contracts_suggested
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"{symbol}: Error during scan - {e}")
            result['error'] = str(e)
            return result
    
    def scan_multiple_stocks(
        self,
        symbols: List[str],
        days_of_history: int = 60
    ) -> List[Dict]:
        """
        Scan multiple stocks
        
        Args:
            symbols: List of stock symbols
            days_of_history: Days to retrieve
            
        Returns:
            List of scan results
        """
        results = []
        
        print(f"\n{'='*70}")
        print(f"  STOCK SCANNER - {len(symbols)} symbols")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Data Type: {'Live (Schwab API)' if self.use_live_data else 'Sample'}")
        print(f"{'='*70}\n")
        
        for symbol in symbols:
            result = self.scan_single_stock(symbol, days_of_history)
            results.append(result)
            self.scan_results[symbol] = result
        
        return results
    
    def print_results_summary(self, results: List[Dict]):
        """Print summary of scan results"""
        
        buy_signals = [r for r in results if r['stock_signal'] and r['stock_signal']['action'] == 'BUY']
        sell_signals = [r for r in results if r['stock_signal'] and r['stock_signal']['action'] == 'SELL']
        options_opportunities = [r for r in results if r['options_opportunity']]
        
        print(f"\n{'='*70}")
        print(f"  SCAN SUMMARY")
        print(f"{'='*70}")
        print(f"  Total Scanned: {len(results)}")
        print(f"  BUY Signals: {len(buy_signals)}")
        print(f"  SELL Signals: {len(sell_signals)}")
        print(f"  Options Opportunities: {len(options_opportunities)}")
        print(f"{'='*70}\n")
        
        if buy_signals:
            print("📈 BUY SIGNALS")
            print("-" * 70)
            for result in buy_signals:
                sig = result['stock_signal']
                print(f"  {result['symbol']:<8} | {sig['signal_type']:<20} | Conf: {sig['confidence']:>5.0f}% | Price: ${sig['price']:>7.2f}")
                print(f"  └─ {sig['reason']}")
            print()
        
        if options_opportunities:
            print("📞 OPTIONS OPPORTUNITIES (Call Options)")
            print("-" * 70)
            for result in options_opportunities:
                opp = result['options_opportunity']
                print(f"  {result['symbol']:<8} | ${opp['strike']:>7.2f} Call | Delta: {opp['delta']:>6.3f} | Prob ITM: {opp['prob_itm']:>5.1%}")
                print(f"  └─ Entry: ${opp['entry_price']:>6.2f} | Contracts: {opp['contracts']} | Conf: {opp['confidence']:.0f}%")
            print()
        
        if sell_signals:
            print("📉 SELL SIGNALS")
            print("-" * 70)
            for result in sell_signals:
                sig = result['stock_signal']
                print(f"  {result['symbol']:<8} | {sig['signal_type']:<20} | Conf: {sig['confidence']:>5.0f}% | Price: ${sig['price']:>7.2f}")
                print(f"  └─ {sig['reason']}")
            print()
    
    def export_results(self, results: List[Dict], output_file: str):
        """Export results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results exported to {output_file}")


def load_stock_list_from_file(filepath: str) -> List[str]:
    """Load stock symbols from file (one per line)"""
    try:
        with open(filepath, 'r') as f:
            symbols = [line.strip().upper() for line in f if line.strip() and not line.startswith('#')]
        return symbols
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return []


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Stock Scanner with Options Trigger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan specific stocks
  python stock_scanner.py --stocks AAPL,SPY,QQQ,META,GOOGL
  
  # Scan from file
  python stock_scanner.py --config my_stocks.txt
  
  # Use live Schwab API data
  python stock_scanner.py --stocks AAPL,SPY --live
  
  # Export results
  python stock_scanner.py --stocks AAPL,SPY --output results.json
        """
    )
    
    parser.add_argument(
        '--stocks',
        type=str,
        help='Comma-separated list of stock symbols (e.g., AAPL,SPY,QQQ)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to file with stock symbols (one per line)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=60,
        help='Days of historical data to retrieve (default: 60)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Use live Schwab API data (requires authentication)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--rsi-oversold',
        type=float,
        default=30,
        help='RSI oversold threshold (default: 30)'
    )
    parser.add_argument(
        '--rsi-overbought',
        type=float,
        default=70,
        help='RSI overbought threshold (default: 70)'
    )
    parser.add_argument(
        '--bb-period',
        type=int,
        default=20,
        help='Bollinger Bands period (default: 20)'
    )
    parser.add_argument(
        '--min-drawdown',
        type=float,
        default=2.0,
        help='Minimum drawdown % for buy signal (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    # Determine stock list
    symbols = []
    if args.stocks:
        symbols = [s.strip().upper() for s in args.stocks.split(',')]
    elif args.config:
        symbols = load_stock_list_from_file(args.config)
    else:
        parser.print_help()
        return 1
    
    if not symbols:
        logger.error("No stocks provided")
        return 1
    
    logger.info(f"Scanning {len(symbols)} stocks: {', '.join(symbols)}")
    
    # Initialize strategy
    strategy = EnhancedStockStrategy(
        rsi_oversold=args.rsi_oversold,
        rsi_overbought=args.rsi_overbought,
        bb_period=args.bb_period,
        min_drawdown_for_buy=args.min_drawdown
    )
    
    # Initialize API if using live data
    api = None
    if args.live:
        try:
            api = SchwabBrokerAPI(account_number="0")
            logger.info("Connected to Schwab API")
        except Exception as e:
            logger.error(f"Failed to connect to Schwab API: {e}")
            logger.info("Falling back to sample data")
            args.live = False
    
    # Create scanner
    scanner = StockScanner(strategy, api, args.live)
    
    # Run scan
    results = scanner.scan_multiple_stocks(symbols, args.days)
    
    # Print results
    scanner.print_results_summary(results)
    
    # Export if requested
    if args.output:
        scanner.export_results(results, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Quick backtester utility for different stock combinations
Usage: python quick_backtest.py [--symbols AAPL,SPY,QQQ] [--days 365] [--capital 100000]
"""

import sys
sys.path.insert(0, '/Users/sanjayj/codeclub/options-trading-bot')

from fang_backtest import FANGBacktester, YahooDataFetcher
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Quick backtest any stock list')
    parser.add_argument('--symbols', type=str, default='META,AMZN,NFLX,GOOGL,NVDA,TSLA',
                       help='Comma-separated stock symbols')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital (default: $100,000)')
    parser.add_argument('--days', type=int, default=365,
                       help='Backtest period in days (default: 365)')
    parser.add_argument('--output', type=str, default='backtest_results.xlsx',
                       help='Output Excel filename')
    
    args = parser.parse_args()
    
    # Override symbols
    backtester = FANGBacktester(initial_capital=args.capital)
    backtester.symbols = args.symbols.split(',')
    
    # Run backtest
    print(f"Running backtest for: {', '.join(backtester.symbols)}")
    print(f"Period: {args.days} days | Capital: ${args.capital:,.0f}\n")
    
    results = backtester.run(days=args.days)
    
    # Export Excel
    backtester.export_to_excel(args.output)
    print(f"\n✓ Results saved to: {args.output}")

#!/usr/bin/env python3.9
"""
Mock Schwab API Test - Shows what successful output looks like
"""

import json
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

print("\n")
print("=" * 80)
print("SCHWAB API TEST - Account Balance and Positions (MOCK DATA)")
print("=" * 80)

print("\nConnecting to Schwab API...")
print("Account: 6578-7226")

# TEST 1: Account Info
print_header("TEST 1: Get Account Information")

account_info = {
    "account_number": "6578-7226",
    "buying_power": 25000.00,
    "cash_balance": 5000.00,
    "margin_available": 20000.00,
    "positions": [
        {
            "instrument": {"symbol": "AAPL"},
            "longQuantity": 10,
            "marketValue": 1650.00,
            "averagePrice": 165.00
        },
        {
            "instrument": {"symbol": "GOOGL"},
            "longQuantity": 5,
            "marketValue": 2100.00,
            "averagePrice": 420.00
        },
        {
            "instrument": {"symbol": "SPY"},
            "longQuantity": 20,
            "marketValue": 8500.00,
            "averagePrice": 425.00
        }
    ]
}

print(f"\nAccount Info Retrieved Successfully!")
print(f"  Account Number: {account_info['account_number']}")
print(f"  Buying Power: ${account_info['buying_power']:,.2f}")
print(f"  Cash Balance: ${account_info['cash_balance']:,.2f}")
print(f"  Margin Available: ${account_info['margin_available']:,.2f}")
print(f"  Positions Count: {len(account_info['positions'])}")

# TEST 2: Positions
print_header("TEST 2: Account Positions")

positions = account_info['positions']
print(f"\nFound {len(positions)} position(s):\n")

for i, pos in enumerate(positions, 1):
    symbol = pos['instrument']['symbol']
    qty = pos['longQuantity']
    market_value = pos['marketValue']
    avg_price = pos['averagePrice']
    
    print(f"  Position {i}: {symbol}")
    print(f"    Quantity: {qty}")
    print(f"    Market Value: ${market_value:,.2f}")
    print(f"    Avg Price: ${avg_price:,.2f}")

# TEST 3: Quote
print_header("TEST 3: Real-time Quote (AAPL)")

quote = {
    "symbol": "AAPL",
    "price": 165.50,
    "bid": 165.48,
    "ask": 165.52,
    "volume": 50000000
}

print(f"\nQuote Retrieved!")
print(f"  Symbol: {quote['symbol']}")
print(f"  Price: ${quote['price']:.2f}")
print(f"  Bid: ${quote['bid']:.2f}")
print(f"  Ask: ${quote['ask']:.2f}")
print(f"  Volume: {quote['volume']:,}")

# TEST 4: Price History
print_header("TEST 4: Price History (AAPL, 5 days)")

history = [
    {"date": "2025-11-27", "open": 164.00, "high": 166.00, "low": 163.50, "close": 165.50, "volume": 45000000},
    {"date": "2025-11-26", "open": 163.50, "high": 164.50, "low": 162.00, "close": 164.00, "volume": 42000000},
    {"date": "2025-11-25", "open": 162.00, "high": 165.00, "low": 161.50, "close": 163.50, "volume": 55000000},
    {"date": "2025-11-24", "open": 165.00, "high": 167.00, "low": 163.00, "close": 162.00, "volume": 51000000},
    {"date": "2025-11-23", "open": 166.00, "high": 168.00, "low": 165.00, "close": 165.00, "volume": 48000000},
]

print(f"\nPrice History Retrieved! ({len(history)} candles)\n")
for i, candle in enumerate(history[::-1], 1):
    print(f"  {i}. {candle['date']}: Close: ${candle['close']:.2f}, Volume: {candle['volume']:,}")

# Summary
print_header("TESTS COMPLETED SUCCESSFULLY!")

total_position_value = sum(pos['marketValue'] for pos in positions)
total_portfolio_value = account_info['buying_power'] + total_position_value

print(f"\nPortfolio Summary:")
print(f"  Cash Available: ${account_info['buying_power']:,.2f}")
print(f"  Position Value: ${total_position_value:,.2f}")
print(f"  Total Portfolio: ${total_portfolio_value:,.2f}")

print(f"\nToken Status: VALID")
print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print("\n" + "=" * 80)
print("Ready to test with real account data!")
print("=" * 80 + "\n")

print("To test with your live account:")
print("  1. Authorize: python3.9 save_token.py")
print("  2. Test: python3.9 test_schwab_api.py")
print()

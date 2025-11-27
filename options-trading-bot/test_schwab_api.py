#!/usr/bin/env python3.9
"""
Test Schwab API - Account Balance and Positions
Uses improved OAuth 2.0 implementation based on Schwabdev
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.brokers import SchwabBrokerAPI
from src.core.logger import logger

def main():
    print("\n" + "=" * 80)
    print("SCHWAB API TEST - Account Balance and Positions")
    print("=" * 80)
    
    # Get config
    account_number = os.getenv("SCHWAB_ACCOUNT_NUMBER")
    app_key = os.getenv("SCHWAB_APP_KEY")
    app_secret = os.getenv("SCHWAB_SECRET")
    token_path = os.getenv("SCHWAB_TOKEN", "./tokens/schwabToken.json")
    
    if not all([account_number, app_key, app_secret]):
        print("\nError: Missing environment variables")
        print("  SCHWAB_ACCOUNT_NUMBER:", account_number)
        print("  SCHWAB_APP_KEY:", app_key)
        print("  SCHWAB_SECRET:", app_secret)
        return False
    
    print(f"\nConfiguration:")
    print(f"  Account: {account_number}")
    print(f"  Token Path: {token_path}")
    
    # Initialize broker
    print(f"\nInitializing Schwab API...")
    
    try:
        broker = SchwabBrokerAPI(
            account_number=account_number,
            app_key=app_key,
            app_secret=app_secret,
            token_path=token_path
        )
        
        # Check if we have valid tokens
        if not broker.access_token or not broker.refresh_token:
            print("\nError: No valid tokens found!")
            print("Please authorize first:")
            print("  python3.9 authorize_schwab.py")
            return False
        
        print(f"  ✓ Access Token: {broker.access_token[:20]}...{broker.access_token[-10:]}")
        print(f"  ✓ Refresh Token available")
        
        # Update tokens if needed
        print(f"\nChecking token expiration...")
        broker.update_tokens()
        
        # TEST 1: Get Account Info
        print("\n" + "=" * 80)
        print("TEST 1: Get Account Information")
        print("=" * 80)
        
        account_info = broker.get_account_info()
        
        if account_info:
            print(f"\n✓ Account Info Retrieved!")
            print(f"  Account: {account_info.get('account_number')}")
            print(f"  Buying Power: ${account_info.get('buying_power', 0):,.2f}")
            print(f"  Cash Balance: ${account_info.get('cash_balance', 0):,.2f}")
            print(f"  Margin: ${account_info.get('margin_available', 0):,.2f}")
            print(f"  Positions: {len(account_info.get('positions', []))}")
        else:
            print("\n✗ Failed to retrieve account info")
            return False
        
        # TEST 2: Display Positions
        print("\n" + "=" * 80)
        print("TEST 2: Account Positions")
        print("=" * 80)
        
        positions = account_info.get('positions', [])
        
        if positions:
            print(f"\n✓ Found {len(positions)} position(s):\n")
            total_value = 0
            for i, pos in enumerate(positions, 1):
                symbol = pos.get('instrument', {}).get('symbol', 'N/A')
                qty = pos.get('longQuantity', 0)
                market_value = pos.get('marketValue', 0)
                avg_price = pos.get('averagePrice', 0)
                
                print(f"  [{i}] {symbol}")
                print(f"      Quantity: {qty} shares")
                print(f"      Avg Price: ${avg_price:.2f}")
                print(f"      Market Value: ${market_value:,.2f}")
                total_value += market_value
            
            print(f"\n  Total Position Value: ${total_value:,.2f}")
        else:
            print("\n  No open positions")
        
        # TEST 3: Get Quote
        print("\n" + "=" * 80)
        print("TEST 3: Real-time Quote (AAPL)")
        print("=" * 80)
        
        quote = broker.get_quote("AAPL")
        if quote:
            print(f"\n✓ Quote Retrieved!")
            print(f"  Symbol: {quote.get('symbol')}")
            print(f"  Price: ${quote.get('price', 0):.2f}")
            print(f"  Bid: ${quote.get('bid', 0):.2f}")
            print(f"  Ask: ${quote.get('ask', 0):.2f}")
        else:
            print("\n  Quote not available (market may be closed)")
        
        # TEST 4: Price History
        print("\n" + "=" * 80)
        print("TEST 4: Price History (AAPL, 5 days)")
        print("=" * 80)
        
        history = broker.get_price_history("AAPL", days=5)
        
        if history:
            print(f"\n✓ Price History Retrieved ({len(history)} candles)\n")
            for i, candle in enumerate(history[-5:], 1):
                print(f"  [{i}] Close: ${candle.get('close', 0):.2f}, "
                      f"Volume: {candle.get('volume', 0):,}")
        else:
            print("\n  Price history not available")
        
        # Summary
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

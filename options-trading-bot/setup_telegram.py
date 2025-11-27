"""
Load Telegram credentials from .env file
Usage: python setup_telegram.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_telegram_config():
    """Load Telegram config from .env file"""
    # Load environment
    env_path = Path('.env')
    load_dotenv(env_path)
    
    token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    chat_ids = os.getenv('TELEGRAM_CHAT_IDS', '').strip()
    
    return {
        'token': token,
        'chat_id': chat_id,
        'chat_ids': chat_ids
    }


def show_setup_instructions():
    """Display setup instructions"""
    print("\n" + "="*70)
    print("TELEGRAM SETUP INSTRUCTIONS")
    print("="*70 + "\n")
    
    print("Step 1: Create a Telegram Bot")
    print("-" * 70)
    print("1. Open Telegram app")
    print("2. Search for '@BotFather'")
    print("3. Send '/newbot'")
    print("4. Follow the instructions to create your bot")
    print("5. Copy your BOT_TOKEN (looks like: 123456789:ABC-DEF1234...)\n")
    
    print("Step 2: Get Your Chat ID")
    print("-" * 70)
    print("1. Send a message to your bot (any message)")
    print("2. Visit this URL in your browser:")
    print("   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("   (Replace <YOUR_BOT_TOKEN> with your actual token)")
    print("3. Look for the 'chat' section in the JSON response")
    print("4. Copy the 'id' value\n")
    
    print("Step 3: Add to .env File")
    print("-" * 70)
    print("Open .env file and fill in:")
    print("  TELEGRAM_BOT_TOKEN=123456789:ABC-DEF1234...")
    print("  TELEGRAM_CHAT_ID=987654321\n")
    
    print("Or for multiple recipients:")
    print("  TELEGRAM_CHAT_IDS=987654321,111111111,222222222\n")


def verify_config():
    """Verify Telegram config is set up"""
    config = load_telegram_config()
    
    print("\n" + "="*70)
    print("TELEGRAM CONFIGURATION STATUS")
    print("="*70 + "\n")
    
    if config['token']:
        print(f"✓ BOT_TOKEN configured: {config['token'][:20]}...")
    else:
        print("✗ BOT_TOKEN not configured")
    
    if config['chat_id']:
        print(f"✓ CHAT_ID configured: {config['chat_id']}")
    elif config['chat_ids']:
        print(f"✓ CHAT_IDS configured: {config['chat_ids']}")
    else:
        print("✗ CHAT_ID or CHAT_IDS not configured")
    
    print()
    
    if config['token'] and (config['chat_id'] or config['chat_ids']):
        print("✓ Telegram is configured and ready to use!\n")
        print("Test with: python test_telegram.py --env")
        print("           or")
        print("           python paper_trading_telegram.py --env\n")
        return True
    else:
        print("✗ Telegram is not fully configured\n")
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Telegram credentials')
    parser.add_argument('--verify', action='store_true', help='Verify configuration')
    parser.add_argument('--instructions', action='store_true', help='Show setup instructions')
    parser.add_argument('--show', action='store_true', help='Show current config')
    
    args = parser.parse_args()
    
    if args.instructions:
        show_setup_instructions()
    elif args.verify:
        verify_config()
    elif args.show:
        config = load_telegram_config()
        print("\nCurrent Telegram Configuration:")
        print(f"  BOT_TOKEN: {config['token'] if config['token'] else '(not set)'}")
        print(f"  CHAT_ID: {config['chat_id'] if config['chat_id'] else '(not set)'}")
        print(f"  CHAT_IDS: {config['chat_ids'] if config['chat_ids'] else '(not set)'}\n")
    else:
        # Default: show instructions and verify
        show_setup_instructions()
        verify_config()


if __name__ == '__main__':
    main()

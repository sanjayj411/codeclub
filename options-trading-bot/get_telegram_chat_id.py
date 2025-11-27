#!/usr/bin/env python
"""
Helper script to get your Telegram chat ID
Instructions:
1. Get your bot token from @BotFather
2. Run this script
3. Send a message to your bot in Telegram
4. The script will display your chat ID
"""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(Path('.env'))

token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
    print("1. Create a bot with @BotFather")
    print("2. Add TELEGRAM_BOT_TOKEN to .env")
    exit(1)

print("=" * 60)
print("TELEGRAM CHAT ID FINDER")
print("=" * 60)
print(f"\n✓ Using bot token: {token[:30]}...")
print("\n📱 Steps:")
print("1. Open Telegram and search for your bot (name configured in @BotFather)")
print("2. Send ANY message to your bot")
print("3. Your chat ID will appear below\n")

# Get updates
url = f"https://api.telegram.org/bot{token}/getUpdates"
try:
    response = requests.get(url, timeout=5)
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ Error: {data.get('description', 'Unknown error')}")
        exit(1)
    
    messages = data.get('result', [])
    
    if not messages:
        print("⚠️  No messages received yet")
        print("Make sure you:")
        print("  - Sent a message to your bot")
        print("  - Are using the correct bot token")
        print("\nTry running this script again after sending a message")
        exit(1)
    
    # Get the most recent chat ID
    chat_ids = set()
    for msg in messages:
        if 'message' in msg:
            chat_id = msg['message'].get('chat', {}).get('id')
            if chat_id:
                chat_ids.add(chat_id)
        elif 'edited_message' in msg:
            chat_id = msg['edited_message'].get('chat', {}).get('id')
            if chat_id:
                chat_ids.add(chat_id)
    
    if not chat_ids:
        print("❌ Could not find chat ID in messages")
        print("Raw response:", data)
        exit(1)
    
    print("=" * 60)
    print("✓ FOUND CHAT IDs:")
    print("=" * 60)
    for chat_id in sorted(chat_ids):
        is_personal = chat_id > 0
        chat_type = "Personal" if is_personal else "Group/Channel"
        print(f"  • {chat_id:15} ({chat_type})")
    
    print("\n" + "=" * 60)
    print("📝 UPDATE YOUR .env FILE:")
    print("=" * 60)
    
    # Recommend personal chat ID
    personal_ids = [cid for cid in chat_ids if cid > 0]
    if personal_ids:
        recommended = max(personal_ids)  # Use the highest personal ID
        print(f"\nAdd this to your .env file:")
        print(f'TELEGRAM_CHAT_ID={recommended}')
        print(f"\nOr replace the existing line with the above")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n✓ Done! Update .env and try again")

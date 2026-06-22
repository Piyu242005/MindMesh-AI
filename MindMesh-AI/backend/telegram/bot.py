import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"

def send_message(msg: str, chat_id: str = None) -> bool:
    """Send a Telegram message."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
        return False
        
    target_chat_id = chat_id or TELEGRAM_ADMIN_CHAT_ID
    if not target_chat_id:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": target_chat_id, "text": msg, "parse_mode": "HTML"},
            timeout=3
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[Telegram Bot] Failed to send message: {e}")
        return False

# Polling support for development
async def start_polling(dispatcher_callback):
    """Simple long polling loop for local development."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    offset = 0
    
    print("[Telegram Bot] Started long polling...")
    while True:
        try:
            res = await asyncio.to_thread(
                requests.get, url, params={"timeout": 10, "offset": offset}, timeout=15
            )
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    # Process message
                    if "message" in update:
                        await dispatcher_callback(update["message"])
        except Exception as e:
            print(f"[Telegram Bot] Polling error: {e}")
            
        await asyncio.sleep(1)

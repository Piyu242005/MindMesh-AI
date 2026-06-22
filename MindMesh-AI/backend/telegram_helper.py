import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", TELEGRAM_CHAT_ID)

def send_notification(msg: str, chat_id: str = None) -> bool:
    """Send a Telegram message to a specific chat ID (defaults to TELEGRAM_CHAT_ID)."""
    if not TELEGRAM_BOT_TOKEN:
        return False
        
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not target_chat_id:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": target_chat_id, "text": msg, "parse_mode": "HTML"}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[Telegram] Failed to send notification: {e}")
        return False

def send_admin_alert(alert_msg: str) -> bool:
    """Send an alert to the admin chat ID."""
    if not TELEGRAM_ADMIN_CHAT_ID:
        return False
        
    msg = f"🚨 <b>MindMesh AI Alert</b>\n\n{alert_msg}"
    return send_notification(msg, TELEGRAM_ADMIN_CHAT_ID)

def send_daily_report(videos_processed: int, chunks_indexed: int, questions_asked: int, status: str = "Healthy"):
    """Send a daily summary report."""
    msg = f"""🧠 <b>MindMesh AI Daily Report</b>

Videos Processed: {videos_processed}
Chunks Indexed: {chunks_indexed}
Questions Asked: {questions_asked}
Qdrant Vectors: {chunks_indexed}

System Status: {status}"""
    return send_admin_alert(msg)

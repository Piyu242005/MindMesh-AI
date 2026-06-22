import os
import psutil
import requests
from backend.telegram.bot import send_message
from backend.telegram.analytics import AnalyticsStore

# Configuration for URLs
LOCAL_URL = f"http://localhost:{os.getenv('PORT', '8000')}"
MONITOR_URLS = [
    LOCAL_URL + "/",
    LOCAL_URL + "/chat",
    LOCAL_URL + "/upload",
    LOCAL_URL + "/health"
]

def check_website_health():
    """Ping website URLs every 5 mins."""
    for url in MONITOR_URLS:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                send_message(f"🚨 <b>Website Issue</b>\n\nURL: {url}\nStatus: {r.status_code}")
            elif r.elapsed.total_seconds() > 5:
                send_message(f"⚠️ <b>High Response Time</b>\n\nURL: {url}\nTime: {r.elapsed.total_seconds():.2f}s")
        except Exception as e:
            send_message(f"🚨 <b>Website Offline</b>\n\nURL: {url}\nError: {str(e)}")

def check_system_resources():
    """Monitor CPU and RAM."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    if cpu > 85 or ram > 85:
        msg = f"""⚠️ <b>High Resource Usage</b>

Memory: {ram}%
CPU: {cpu}%"""
        send_message(msg)

def send_daily_backup_status():
    """Check Qdrant backup / vectors status (mocked or actual query)."""
    # Assuming Qdrant client exists. We would normally inject it or import it.
    from backend.embeddings import get_qdrant_client
    try:
        client, error = get_qdrant_client()
        if client:
            count_result = client.count(collection_name=os.getenv('QDRANT_COLLECTION', 'mindmesh_courses'))
            vectors_count = count_result.count
            status = "Healthy"
        else:
            vectors_count = 0
            status = "Client not configured"
    except Exception as e:
        vectors_count = 0
        status = f"Error: {e}"

    msg = f"""📦 <b>Daily Status</b>

Vectors: {vectors_count}
Collection: {os.getenv('QDRANT_COLLECTION', 'mindmesh_courses')}
Status: {status}"""
    send_message(msg)

def run_daily_analytics():
    """Send Daily Analytics Report and Backup Status."""
    report = AnalyticsStore.generate_report()
    send_message(report)
    AnalyticsStore.reset()
    send_daily_backup_status()

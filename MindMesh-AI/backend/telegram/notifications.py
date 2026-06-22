from datetime import datetime, timezone
from backend.telegram.bot import send_message

def send_startup_alert():
    msg = f"""🚀 <b>MindMesh AI Started</b>

Environment: Production
Version: 1.0.0
Time: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}"""
    send_message(msg)

def send_shutdown_alert():
    msg = f"""🛑 <b>MindMesh AI Shutdown</b>

Environment: Production
Time: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}"""
    send_message(msg)

def send_error_alert(service: str, route: str, error: str):
    msg = f"""🚨 <b>ERROR DETECTED</b>

Service: {service}
Route: {route}
Error: {error}
Time: {datetime.now(timezone.utc).strftime("%H:%M UTC")}"""
    send_message(msg)

def send_upload_alert(filename: str, size_mb: float, user: str = "Admin"):
    msg = f"""📹 <b>New Video Uploaded</b>

File: {filename}
Size: {size_mb:.2f}MB
User: {user}"""
    send_message(msg)

def send_query_alert(question: str, provider: str, response_time: float):
    msg = f"""💬 <b>New Query</b>

Question:
{question}

Provider:
{provider}

Response Time:
{response_time:.2f}s"""
    send_message(msg)

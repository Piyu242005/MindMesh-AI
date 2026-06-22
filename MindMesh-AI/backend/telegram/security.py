import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.telegram.bot import send_message

class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.ip_requests = defaultdict(list)
        self.RATE_LIMIT = 50
        self.TIME_WINDOW = 60 # seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean up old requests
        self.ip_requests[client_ip] = [t for t in self.ip_requests[client_ip] if now - t < self.TIME_WINDOW]
        self.ip_requests[client_ip].append(now)

        if len(self.ip_requests[client_ip]) > self.RATE_LIMIT:
            # Send alert
            msg = f"""🔒 <b>Security Alert</b>

IP: {client_ip}

Reason:
Rate Limit Exceeded

Count:
{len(self.ip_requests[client_ip])} Requests in 1 Minute"""
            send_message(msg)

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Re-raise to be caught by global exception handler
            raise e

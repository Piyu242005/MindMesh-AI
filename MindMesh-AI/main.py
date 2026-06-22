import os
import sys
import traceback
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

# Setup paths
ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
TEMPLATES_DIR = ROOT / "templates"

for d in [STATIC_DIR, TEMPLATES_DIR, ROOT / "videos", ROOT / "audios", ROOT / "jsons"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Telegram Integrations ──────────────────────────────────────────────────
from backend.telegram.notifications import send_startup_alert, send_shutdown_alert, send_error_alert
from backend.telegram.health_monitor import check_website_health, check_system_resources, run_daily_analytics
from backend.telegram.security import SecurityMonitoringMiddleware
from backend.telegram.bot import start_polling
from backend.telegram.commands import process_telegram_message

# ── APScheduler Setup ──────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()
scheduler.add_job(check_website_health, 'interval', minutes=int(os.getenv("MONITOR_INTERVAL_MINUTES", "5")))
scheduler.add_job(check_system_resources, 'interval', minutes=5)
scheduler.add_job(run_daily_analytics, 'cron', hour=int(os.getenv("DAILY_REPORT_HOUR", "9")), minute=0)

# ── Lifespan Events ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    send_startup_alert()
    scheduler.start()
    
    # Start long polling if not strictly using webhook
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    if not webhook_url:
        asyncio.create_task(start_polling(process_telegram_message))
        
    yield
    # Shutdown
    send_shutdown_alert()
    scheduler.shutdown()

# ── FastAPI Initialization ─────────────────────────────────────────────────
app = FastAPI(title="MindMesh AI", version="1.0", lifespan=lifespan)

# ── Middlewares ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityMonitoringMiddleware)

# ── Exception Handler ──────────────────────────────────────────────────────
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("error.html", {"request": request, "status_code": 404, "message": "Page Not Found"}, status_code=404)
    return templates.TemplateResponse("error.html", {"request": request, "status_code": exc.status_code, "message": exc.detail}, status_code=exc.status_code)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    send_error_alert(
        service="FastAPI Application",
        route=request.url.path,
        error=repr(exc)
    )
    return templates.TemplateResponse("error.html", {"request": request, "status_code": 500, "message": "Internal Server Error"}, status_code=500)

# ── Mounts & Routes ────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "MindMesh AI"
    }

# ── Routers ───────────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

from routes import dashboard, upload, chat, settings
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(settings.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data:
            await process_telegram_message(data["message"])
    except Exception as e:
        pass
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

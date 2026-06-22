import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Setup paths
ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"
TEMPLATES_DIR = ROOT / "templates"

# Create directories if they don't exist
for d in [STATIC_DIR, TEMPLATES_DIR, ROOT / "videos", ROOT / "audios", ROOT / "jsons"]:
    d.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI
app = FastAPI(title="MindMesh AI", version="1.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Import routes
from routes import dashboard, upload, chat, settings
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(settings.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

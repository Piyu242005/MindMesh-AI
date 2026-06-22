from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
from dotenv import set_key

router = APIRouter()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
ENV_FILE = Path(__file__).parent.parent / ".env"

@router.get("/settings")
async def settings_page(request: Request):
    from backend.llm_manager import check_providers
    health = check_providers()
    
    provider = os.getenv("LLM_PROVIDER", "gemini")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    return templates.TemplateResponse(request=request, name="settings.html", context={
        "request": request,
        "health": health,
        "provider": provider,
        "gemini_model": gemini_model,
        "groq_model": groq_model
    })

@router.post("/api/settings")
async def update_settings(
    request: Request,
    provider: str = Form(...),
    gemini_model: str = Form(...),
    groq_model: str = Form(...)
):
    # Update environment variables
    os.environ["LLM_PROVIDER"] = provider
    os.environ["GEMINI_MODEL"] = gemini_model
    os.environ["GROQ_MODEL"] = groq_model
    
    # If .env exists, update it to persist (requires python-dotenv set_key or similar)
    if ENV_FILE.exists():
        try:
            set_key(str(ENV_FILE), "LLM_PROVIDER", provider)
            set_key(str(ENV_FILE), "GEMINI_MODEL", gemini_model)
            set_key(str(ENV_FILE), "GROQ_MODEL", groq_model)
        except Exception as e:
            pass
            
    return HTMLResponse("<div class='p-4 bg-green-500/20 text-green-400 rounded-lg'>Settings saved successfully!</div>")

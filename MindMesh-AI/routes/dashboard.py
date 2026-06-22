from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

from backend.llm_manager import _cli_metrics
from backend import qdrant_helper as qh

router = APIRouter()

# Get the templates directory relative to the current file
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/")
async def dashboard(request: Request):
    # Fetch basic analytics (V1)
    
    # Qdrant Status
    try:
        client = qh.get_client()
        info = qh.collection_info(client)
        vcount = info.get("vector_count", 0)
        qdrant_status = f"{vcount} chunks" if vcount > 0 else "Empty"
    except Exception as e:
        qdrant_status = "Error"

    # Count courses (unique JSON files = courses for now)
    jsons_dir = Path(__file__).parent.parent / "jsons"
    total_courses = len(list(jsons_dir.glob("*.json"))) if jsons_dir.exists() else 0

    # Total Queries and Model from CLI metrics
    total_queries = _cli_metrics["total_requests"]
    
    import os
    active_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") # default
    
    context = {
        "request": request,
        "total_courses": total_courses,
        "total_chunks": vcount if qdrant_status != "Error" and qdrant_status != "Empty" else 0,
        "total_queries": total_queries,
        "qdrant_status": qdrant_status,
        "active_model": active_model
    }
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)

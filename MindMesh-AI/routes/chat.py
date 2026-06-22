from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from pathlib import Path
import os
import json

from backend import qdrant_helper as qh
from backend.embeddings import get_embedding_model, get_qdrant_client
from backend.retrieval import retrieve, build_rag_prompt

router = APIRouter()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")

@router.post("/api/chat")
async def chat_endpoint(request: Request, query: str = Form(...)):
    # 1. Retrieve
    embed_model = get_embedding_model()
    q_client, _ = get_qdrant_client()
    
    # Default settings
    top_k = 5
    score_threshold = 0.0
    
    hits, source_label = retrieve(
        embed_model=embed_model,
        query=query,
        qdrant_client=q_client,
        top_k=top_k,
        score_threshold=score_threshold
    )
    
    from backend.telegram.analytics import AnalyticsStore
    AnalyticsStore.add_search()
    
    prompt = build_rag_prompt(query, hits)
    
    from backend.llm_manager import generate_response
    
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    stream_gen = generate_response(prompt, provider=provider, model_name=model_name, stream=True)
    
    # We will format the output as SSE (Server-Sent Events) for HTMX
    # HTMX SSE extension expects events: 'data: <div>...</div>\n\n'
    
    async def sse_generator():
        # First send the sources
        sources_html = "<div class='text-sm text-gray-400 mb-2'><strong>Sources:</strong><ul class='list-disc pl-5'>"
        for h in hits:
            sources_html += f"<li>Video {h.get('number', '?')}: {h.get('title', '?')}</li>"
        sources_html += "</ul></div>"
        
        yield f"data: {sources_html}\n\n"
        
        for chunk in stream_gen:
            # Simple chunk escaping (basic)
            safe_chunk = chunk.replace('\n', '<br>')
            yield f"data: {safe_chunk}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")

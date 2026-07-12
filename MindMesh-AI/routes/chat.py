from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from pathlib import Path
import os
import json

from backend import qdrant_helper as qh
from backend.embeddings import get_embedding_model, get_qdrant_client
from backend.retrieval import retrieve, build_rag_prompt, rewrite_query
from backend.session import get_current_user_id

from cachetools import TTLCache

# Cache up to 1000 responses for 24 hours (86400 seconds)
response_cache = TTLCache(maxsize=1000, ttl=86400)

router = APIRouter()
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"

@router.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")

@router.post("/api/chat")
def chat_endpoint(request: Request, query: str = Form(...), conversation_id: str = Form(None)):
    try:
        return _chat_endpoint_internal(request, query, conversation_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        def err_gen():
            yield sse_event({"error": "Sorry, an error occurred while processing your request."})
        return StreamingResponse(err_gen(), media_type="text/event-stream")

def _chat_endpoint_internal(request: Request, query: str, conversation_id: str):
    from backend.memory import (
        create_conversation, get_chat_history, add_message, 
        generate_conversation_title, update_conversation_title,
        get_conversation, generate_conversation_summary, update_conversation_summary
    )
    user_id = get_current_user_id(request)
    query = query.strip()
    if not query:
        def err_gen():
            yield sse_event({"error": "Please enter a question."})
        return StreamingResponse(err_gen(), media_type="text/event-stream", status_code=400)

    # Check cache first ONLY if there is no active conversation context
    if not conversation_id and query in response_cache:
        cached_response, conf = response_cache[query]
        def cached_sse_generator():
            yield sse_event({"confidence": conf})
            yield sse_event({"content": cached_response})
        return StreamingResponse(cached_sse_generator(), media_type="text/event-stream")

    chat_history = []
    summary = ""
    is_new = False
    
    if not conversation_id or conversation_id.strip() == "":
        conversation_id = create_conversation(user_id=user_id, title="New Conversation")
        is_new = True
    else:
        chat_history = get_chat_history(conversation_id, user_id=user_id, limit=8)
        conv = get_conversation(conversation_id, user_id=user_id)
        if not conv:
            def err_gen():
                yield sse_event({"error": "Conversation not found."})
            return StreamingResponse(err_gen(), media_type="text/event-stream", status_code=404)
        if conv and conv.get("summary"):
            summary = conv["summary"]

    # Add User Message to DB
    add_message(conversation_id, role="user", content=query)

    # 0. Query Rewriting (Skip for simple queries to save 500-1500ms)
    if len(query.split()) < 5:
        optimized_query = query
    else:
        optimized_query = rewrite_query(query)

    print(f"DEBUG: Incoming Question: {query}")
    print(f"DEBUG: Optimized Query: {optimized_query}")

    # 1. Retrieve
    embed_model = get_embedding_model()
    q_client, _ = get_qdrant_client()
    
    # Default settings
    top_k = 5
    score_threshold = 0.0
    
    # Fix dict unpacking error
    retrieval_result = retrieve(
        embed_model=embed_model,
        query=optimized_query,
        qdrant_client=q_client,
        top_k=top_k,
        score_threshold=score_threshold
    )
    confidence = retrieval_result.get("confidence", "Medium")
    print(f"DEBUG: Confidence Score: {confidence}")
    print(f"DEBUG: Retrieved Course Chunks Count: {len(retrieval_result.get('course_hits', []))}")
    print(f"DEBUG: Retrieved Web Hits Count: {len(retrieval_result.get('web_hits', []))}")
    
    from backend.telegram.analytics import AnalyticsStore
    AnalyticsStore.add_search()
    
    prompt = build_rag_prompt(optimized_query, retrieval_result, chat_history=chat_history, summary=summary)
    print(f"DEBUG: LLM Request Prompt length: {len(prompt)}")
    
    from backend.llm_manager import generate_response
    provider = os.getenv("LLM_PROVIDER", "groq") # Default to Groq for speed
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    stream_gen = generate_response(prompt, provider=provider, model_name=model_name, stream=True)
    
    # Synchronous generator allows Starlette to safely offload blocking next() to threadpool
    def sse_generator():
        yield sse_event({"confidence": confidence})
        
        full_response = ""
        for chunk in stream_gen:
            full_response += chunk
            yield sse_event({"content": chunk})
            
        # Store the completed response in the cache ONLY if standalone
        if is_new:
            response_cache[query] = (full_response, confidence)
            
        # Add Assistant Message to DB
        add_message(conversation_id, role="assistant", content=full_response, confidence=confidence)
        
        # Background Tasks (Title & Summary)
        if is_new:
            title = generate_conversation_title(query)
            update_conversation_title(conversation_id, title, user_id=user_id)
            
        # Generate summary every 20 messages (approx. 10 pairs)
        if len(chat_history) >= 18 and len(chat_history) % 10 == 0:
            from backend.memory import get_full_chat_history
            full_history = get_full_chat_history(conversation_id, user_id=user_id)
            new_summary = generate_conversation_summary(full_history)
            update_conversation_summary(conversation_id, new_summary, user_id=user_id)
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream", headers={"X-Conversation-Id": conversation_id})

@router.get("/api/conversations")
def list_conversations(request: Request):
    from backend.memory import get_all_conversations
    return {"conversations": get_all_conversations(get_current_user_id(request))}

@router.get("/api/conversations/search")
def search_conversations_endpoint(request: Request, q: str):
    from backend.memory import search_conversations
    return {"conversations": search_conversations(q, get_current_user_id(request))}

@router.get("/api/conversations/{conversation_id}")
def get_conversation_data(request: Request, conversation_id: str):
    from backend.memory import get_conversation, get_full_chat_history
    user_id = get_current_user_id(request)
    conv = get_conversation(conversation_id, user_id=user_id)
    if not conv:
        return {"error": "Not found"}
    messages = get_full_chat_history(conversation_id, user_id=user_id)
    return {"conversation": conv, "messages": messages}

@router.delete("/api/conversations/{conversation_id}")
def delete_conv(request: Request, conversation_id: str):
    from backend.memory import delete_conversation
    delete_conversation(conversation_id, user_id=get_current_user_id(request))
    return {"status": "deleted"}

@router.patch("/api/conversations/{conversation_id}")
def update_conv(request: Request, conversation_id: str, title: str = Form(None), is_pinned: int = Form(None)):
    from backend.memory import update_conversation_title, toggle_pin
    user_id = get_current_user_id(request)
    if title is not None:
        update_conversation_title(conversation_id, title, user_id=user_id)
    if is_pinned is not None:
        toggle_pin(conversation_id, is_pinned, user_id=user_id)
    return {"status": "updated"}

@router.get("/api/conversations/{conversation_id}/export/{format}")
def export_conversation(request: Request, conversation_id: str, format: str):
    from backend.memory import get_conversation, get_full_chat_history
    from fastapi.responses import PlainTextResponse
    import json
    
    user_id = get_current_user_id(request)
    conv = get_conversation(conversation_id, user_id=user_id)
    if not conv:
        return {"error": "Not found"}
        
    messages = get_full_chat_history(conversation_id, user_id=user_id)
    title = conv.get("title", "Export")
    
    if format == "json":
        return {"title": title, "messages": messages}
    
    elif format == "markdown" or format == "md":
        md = f"# {title}\n\n"
        for msg in messages:
            md += f"### {msg['role'].capitalize()}\n"
            md += f"{msg['content']}\n\n"
        headers = {"Content-Disposition": f'attachment; filename="{title}.md"'}
        return PlainTextResponse(md, headers=headers, media_type="text/markdown")
        
    elif format == "txt":
        txt = f"--- {title} ---\n\n"
        for msg in messages:
            txt += f"{msg['role'].upper()}: {msg['content']}\n\n"
        headers = {"Content-Disposition": f'attachment; filename="{title}.txt"'}
        return PlainTextResponse(txt, headers=headers, media_type="text/plain")

    return {"error": "Unsupported format"}

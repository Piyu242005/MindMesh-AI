import logging
import uuid
import json
import httpx
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import ChatRequest, ChatResponse, Message
from .rag_pipeline import RAGPipeline
from .config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG.driver")

app = FastAPI(title="RAG Chat API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .database import init_db, save_message, get_chat_history, create_session, get_all_sessions, delete_session, update_session_title

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RAG API...")
    init_db()
    # Initialize engine
    RAGPipeline.get_engine()

@app.get("/sessions")
async def list_sessions():
    return get_all_sessions()

@app.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    # Save user message
    save_message(session_id, "user", request.query)
    
    # Generate title if new session (first message)
    history = get_chat_history(session_id)
    if len(history) <= 1:
        # Simple title generaion strategy: use first 30 chars of query
        title = (request.query[:30] + '..') if len(request.query) > 30 else request.query
        update_session_title(session_id, title)
    
    async def event_generator():
        combined_response = ""
        try:
            async for chunk_str in RAGPipeline.chat_stream(
                query=request.query,
                model=request.model,
                use_reranker=request.use_reranker
            ):
                chunk_str = chunk_str.strip()
                if not chunk_str: continue

                chunk_data = json.loads(chunk_str)
                event_type = chunk_data.get("type")
                
                if event_type == "content":
                    text_chunk = chunk_data.get("data", "")
                    combined_response += text_chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': text_chunk})}\n\n"
                    
                elif event_type == "sources":
                    sources = chunk_data.get("data", [])
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            # Save assistant response to history
            save_message(session_id, "assistant", combined_response)
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/history/{session_id}")
async def get_history_by_id(session_id: str):
    return get_chat_history(session_id)

@app.get("/history")
async def get_history(session_id: str):
    return get_chat_history(session_id)

@app.post("/clear")
async def clear_history(session_id: str = Body(..., embed=True)):
    delete_session(session_id)
    return {"status": "cleared"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/models")
async def get_models():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                # Return list of model names
                return {"models": [m["name"] for m in data.get("models", [])]}
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
    
    return {"models": [Config.LLM_MODEL, "llama3.2", "mistral"]}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = ""
        filename = file.filename
        
        # Extract text based on file type
        if filename.endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(file.file)
            content = "\n".join([page.extract_text() for page in reader.pages])
        else:
            # Assume text/md
            content = (await file.read()).decode("utf-8")
            
        if not content.strip():
            raise HTTPException(status_code=400, detail="Empty file contend")

        # Simple Chunking (reuse from chunking.py logic or simple split)
        # For now, simple split by paragraphs/size
        chunk_size = 500
        overlap = 50
        
        text_chunks = []
        for i in range(0, len(content), chunk_size - overlap):
            text_chunks.append(content[i : i + chunk_size])
            
        # Prepare for RAG
        rag_chunks = [
            {"text": chunk, "title": filename} 
            for chunk in text_chunks
        ]
        
        # Add to pipeline
        RAGPipeline.add_documents(rag_chunks)
        
        return {"status": "success", "chunks_added": len(rag_chunks), "filename": filename}
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

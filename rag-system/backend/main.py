from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import shutil
import os
import logging
import json
from datetime import datetime
import uuid

from config import settings
from rag.ingestion import ingestion_pipeline
from rag.retriever import retriever
from rag.generator import generator

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- InMemory Session Store (Replace with DB in real production) ---
SESSIONS_FILE = os.path.join(settings.CHROMA_DB_DIR, "sessions.json")

def load_sessions() -> Dict:
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sessions(sessions: Dict):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f)

sessions_db = load_sessions()

# --- Models ---

class ChatRequest(BaseModel):
    query: str
    session_id: str
    model: Optional[str] = settings.LLM_MODEL

class Session(BaseModel):
    id: str
    title: str
    timestamp: float

# --- Endpoints ---

@app.on_event("startup")
async def startup_event():
    logger.info("Starting RAG System...")

@app.get("/api/v1/models")
async def get_models():
    """Return available models."""
    return {"models": [settings.LLM_MODEL, "llama3", "mistral"]}

@app.get("/api/v1/sessions")
async def get_sessions():
    """Get all sessions."""
    # Convert dict to list and sort by timestamp desc
    session_list = [
        {"id": k, "title": v.get("title", "New Chat"), "timestamp": v.get("timestamp", 0)}
        for k, v in sessions_db.items()
    ]
    session_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return session_list

@app.get("/api/v1/history/{session_id}")
async def get_history(session_id: str):
    """Get chat history for a session."""
    session = sessions_db.get(session_id)
    if not session:
        return []
    return session.get("messages", [])

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions_db:
        del sessions_db[session_id]
        save_sessions(sessions_db)
    return {"status": "success"}

@app.post("/api/v1/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document in background."""
    try:
        # Save file locally
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Add background task for processing
        background_tasks.add_task(ingestion_pipeline.process_upload, file_path)
        
        return {"status": "success", "message": f"File {file.filename} uploaded and queued for processing."}
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Chat with RAG: Retrieve context and stream response."""
    
    # Initialize session if not exists
    if request.session_id not in sessions_db:
        sessions_db[request.session_id] = {
            "title": request.query[:30] + "...",
            "timestamp": datetime.now().timestamp(),
            "messages": []
        }
    
    # Update timestamp
    sessions_db[request.session_id]["timestamp"] = datetime.now().timestamp()
    
    # Save User Message
    sessions_db[request.session_id]["messages"].append({"role": "user", "content": request.query})
    save_sessions(sessions_db)

    # 1. Retrieve Context
    logger.info(f"Retrieving for query: {request.query}")
    print(f"DEBUG: Starting retrieval for {request.query}")
    results = retriever.retrieve(request.query)
    print(f"DEBUG: Retrieval complete. Found {len(results)} results.")
    
    # Format context
    context_str = "\n\n".join([f"source: {r['metadata'].get('source', 'unknown')}\ncontent: {r['text']}" for r in results])
    print(f"DEBUG: Context prepared. Length: {len(context_str)}")
    
    # 2. Generator Stream
    async def event_generator():
        print("DEBUG: Starting event generator")
        # Send sources first
        sources = [{"source": r["metadata"].get("source"), "score": r.get("score", 0)} for r in results]
        yield json.dumps({"type": "sources", "data": sources}) + "\n"
        
        full_response = ""
        # Stream content
        print("DEBUG: Calling generator.generate_stream")
        try:
            async for chunk in generator.generate_stream(request.query, context_str):
                print(f"DEBUG: Received chunk: {chunk[:20]}...")
                full_response += chunk
                yield json.dumps({"type": "content", "data": chunk}) + "\n"
        except Exception as e:
            print(f"DEBUG: Generator error: {e}")
            logger.error(f"Generator error: {e}")
            yield json.dumps({"type": "content", "data": f"Error: {str(e)}"}) + "\n"
        
        print("DEBUG: Generation complete")
        
        # Save Assistant Message
        if request.session_id in sessions_db:
            sessions_db[request.session_id]["messages"].append({"role": "assistant", "content": full_response})
            save_sessions(sessions_db)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

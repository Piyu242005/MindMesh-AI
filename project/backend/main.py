import logging
import uuid
import json
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Body
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

# In-memory history storage
# Map session_id -> List[Message]
chat_history: Dict[str, List[Dict[str, str]]] = {}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up RAG API...")
    # Initialize engine
    RAGPipeline.get_engine()

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    # Initialize history if new session
    if session_id not in chat_history:
        chat_history[session_id] = []
    
    # Add user message to history
    chat_history[session_id].append({"role": "user", "content": request.query})
    
    async def event_generator():
        combined_response = ""
        # The pipeline yields JSON strings:
        # {"type": "sources", "data": [...]}
        # {"type": "content", "data": "chunk"}
        
        try:
            async for chunk_str in RAGPipeline.chat_stream(
                query=request.query,
                model=request.model,
                use_reranker=request.use_reranker
            ):
                # Clean up the yield
                chunk_str = chunk_str.strip()
                if not chunk_str:
                    continue
                    
                chunk_data = json.loads(chunk_str)
                event_type = chunk_data.get("type")
                
                if event_type == "content":
                    text_chunk = chunk_data.get("data", "")
                    combined_response += text_chunk
                    # SSE format: data: ... \n\n
                    yield f"data: {json.dumps({'type': 'content', 'content': text_chunk})}\n\n"
                    
                elif event_type == "sources":
                    sources = chunk_data.get("data", [])
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            # Save assistant response to history
            chat_history[session_id].append({"role": "assistant", "content": combined_response})
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/history")
async def get_history(session_id: str):
    if session_id not in chat_history:
        return {"history": []}
    return {"history": chat_history[session_id]}

@app.post("/clear")
async def clear_history(session_id: str = Body(..., embed=True)):
    if session_id in chat_history:
        del chat_history[session_id]
        return {"status": "cleared"}
    return {"status": "session not found"}

@app.get("/health")
async def health():
    return {"status": "ok"}

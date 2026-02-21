from pydantic import BaseModel
from typing import List, Optional, Any, Literal

class Source(BaseModel):
    title: str = "Unknown"
    number: int
    start: float
    end: float
    text: str
    score: float

class ChatRequest(BaseModel):
    query: str
    model: Optional[str] = "llama3.2"
    session_id: Optional[str] = None
    use_reranker: Optional[bool] = True
    mode: Optional[Literal["chat", "qa", "coding"]] = "chat"

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]

class Message(BaseModel):
    role: str
    content: str

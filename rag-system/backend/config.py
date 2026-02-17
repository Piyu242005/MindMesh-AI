from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "RAG Production System"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # LLM & Embedding Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.2"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    OPENAI_API_KEY: Optional[str] = None
    
    # Vector DB Settings
    CHROMA_DB_DIR: str = "data/chroma_db"
    COLLECTION_NAME: str = "rag_documents"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    RERANK_TOP_N: int = 20
    
    # Paths
    UPLOAD_DIR: str = "data/uploads"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create singleton instance
settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

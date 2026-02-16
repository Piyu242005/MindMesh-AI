"""Centralized configuration for the RAG pipeline."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables with defaults."""

    # Ollama
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Models
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v2")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "hi")
    WHISPER_TASK = os.getenv("WHISPER_TASK", "translate")

    # Retrieval
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "20"))

    # Chunking
    CHUNK_WINDOW_SECONDS = int(os.getenv("CHUNK_WINDOW_SECONDS", "30"))
    CHUNK_OVERLAP_SECONDS = int(os.getenv("CHUNK_OVERLAP_SECONDS", "10"))

    # Paths
    VIDEOS_DIR = os.getenv("VIDEOS_DIR", "videos")
    AUDIOS_DIR = os.getenv("AUDIOS_DIR", "Audios")
    JSONS_DIR = os.getenv("JSONS_DIR", "jsons")
    CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "chroma_db")
    EMBEDDINGS_FILE = os.getenv("EMBEDDINGS_FILE", "embeddings.joblib")

    # Server
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

    @classmethod
    def ollama_embed_url(cls):
        return f"{cls.OLLAMA_BASE_URL}/api/embed"

    @classmethod
    def ollama_generate_url(cls):
        return f"{cls.OLLAMA_BASE_URL}/api/generate"

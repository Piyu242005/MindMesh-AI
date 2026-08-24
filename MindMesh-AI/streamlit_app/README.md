# MindMesh AI — Streamlit Edition

A lightweight Streamlit interface for the MindMesh AI RAG pipeline.

## Features

- PDF, TXT, Markdown and CSV ingestion
- Audio/video transcription with Faster-Whisper + FFmpeg
- Semantic chunking and embeddings with `BAAI/bge-small-en-v1.5`
- Qdrant Cloud vector search
- Grounded chat with Groq or Gemini
- Source-aware answers
- Simple knowledge-base and pipeline health views

## Run locally

```bash
cd MindMesh-AI/streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

FFmpeg must be installed and available on `PATH` for audio/video processing.

## Streamlit secrets

Create `.streamlit/secrets.toml` locally:

```toml
QDRANT_URL = "https://YOUR-QDRANT-ENDPOINT"
QDRANT_API_KEY = "YOUR-QDRANT-KEY"
GROQ_API_KEY = "YOUR-GROQ-KEY"
# GEMINI_API_KEY = "YOUR-GEMINI-KEY"
```

Do not commit secrets. The app also accepts these values as environment variables.

## Architecture

`Upload → Extract/Transcribe → Chunk → BGE Embeddings → Qdrant → Retrieval → Groq/Gemini → Answer + Sources`

This Streamlit edition is intentionally separate from the existing FastAPI application so both interfaces can evolve independently.

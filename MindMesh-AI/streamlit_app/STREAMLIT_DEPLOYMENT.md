# MindMesh AI — Streamlit + Supabase

## Architecture

`Streamlit → Supabase REST/RPC → PostgreSQL + pgvector → RAG → Groq/Gemini`

Qdrant is not used by the Streamlit application.

## Streamlit Cloud

Set the app entrypoint to:

`MindMesh-AI/streamlit_app/app.py`

Add these secrets in Streamlit Cloud:

```toml
SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_PUBLISHABLE_KEY"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RAG_TOP_K = "5"
WHISPER_MODEL = "base"
```

Gemini can be used instead of Groq with `GEMINI_API_KEY` and `GEMINI_MODEL`.

## Media support

`packages.txt` installs FFmpeg. Faster-Whisper handles transcription for audio/video.

## Supabase

The MindMesh project uses the `vector` extension, `mindmesh_documents`, `mindmesh_chunks`, and RPC functions for ingestion and cosine-similarity retrieval.

Do not commit production secrets. Use Streamlit Cloud Secrets.

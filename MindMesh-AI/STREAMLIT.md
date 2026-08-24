# MindMesh AI — Streamlit Edition

This is a separate Streamlit interface for MindMesh AI. The existing FastAPI/HTMX application is unchanged.

## Run locally

From the repository's `MindMesh-AI` application directory:

```bash
pip install -r streamlit_requirements.txt
streamlit run streamlit_app.py
```

Make sure the existing environment variables are configured for Gemini/Groq and Qdrant. FFmpeg must also be available on PATH for media processing.

## Pages

- Home — simple overview
- Upload & Process — add video/audio and index it
- Ask MindMesh — RAG chat with source details
- Knowledge Library — browse processed lessons
- Analytics — local knowledge-base metrics

The Streamlit UI reuses the existing `backend/` transcription, embedding, Qdrant and retrieval modules rather than creating a second RAG implementation.

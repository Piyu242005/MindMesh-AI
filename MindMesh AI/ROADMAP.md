# MindMesh AI Roadmap

Welcome to the MindMesh AI Roadmap! This document outlines our current capabilities and the direction we are heading.

## 🟢 Current Features (v1.0)

* **Video Processing**: Automated extraction of audio from video files (`.mp4`, `.mkv`, etc.) using FFmpeg.
* **Transcription**: Local, high-speed speech-to-text powered by `faster-whisper`.
* **RAG Search**: Fast, accurate vector retrieval using `BAAI/bge-small-en-v1.5` sentence embeddings.
* **Qdrant Cloud**: Scalable vector database for robust chunk management.
* **AI Chat**: Conversational interface with smart LLM routing between Gemini and Groq, grounded exclusively in your course data.
* **Streamlit Dashboard**: Easy-to-use GUI for uploading videos, tweaking settings, and monitoring system health.

## 🚀 Future Features

We are actively working on expanding the MindMesh AI platform. Here's what's coming next:

* **Multi-User Support**: User accounts and isolated workspaces for personal course libraries.
* **GraphRAG**: Implementing Knowledge Graphs alongside vector search for deeper, multi-hop reasoning across lectures.
* **Analytics Dashboard**: Detailed insights into learning progress, popular query topics, and LLM token usage.
* **Course Recommendations**: AI-driven suggestions for related lectures based on chat history.
* **Enterprise Authentication**: SSO integration (OAuth2, SAML) for corporate learning environments.

*Have a feature in mind? [Open an issue](https://github.com/Piyu242005/MindMesh-AI/issues) and let us know!*

"""MindMesh AI - Streamlit edition.

A lightweight UI over the MindMesh RAG pipeline for PDF, text, audio and video
knowledge bases. Secrets are read from Streamlit secrets or environment vars.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).resolve().parent
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
COLLECTION = os.getenv("QDRANT_COLLECTION", "mindmesh_streamlit")
TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


@st.cache_resource(show_spinner=False)
def get_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL)


@st.cache_resource(show_spinner=False)
def get_qdrant():
    from qdrant_client import QdrantClient

    url = secret("QDRANT_URL")
    api_key = secret("QDRANT_API_KEY")
    if not url or not api_key:
        return None
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client) -> None:
    from qdrant_client.models import Distance, VectorParams

    collections = {c.name for c in client.get_collections().collections}
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    finally:
        Path(path).unlink(missing_ok=True)


def transcribe_media(data: bytes, suffix: str) -> str:
    from faster_whisper import WhisperModel

    with tempfile.TemporaryDirectory() as td:
        media = Path(td) / f"input{suffix}"
        audio = Path(td) / "audio.wav"
        media.write_bytes(data)
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(audio)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio), vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments)


def extract_content(upload) -> tuple[str, str]:
    suffix = Path(upload.name).suffix.lower()
    data = upload.getvalue()
    if suffix == ".pdf":
        return extract_pdf(data), "PDF"
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="ignore"), "Text"
    if suffix in {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".mkv", ".webm"}:
        return transcribe_media(data, suffix), "Audio/Video"
    raise ValueError(f"Unsupported file type: {suffix}")


def index_document(name: str, text: str) -> int:
    client = get_qdrant()
    if client is None:
        raise RuntimeError("Qdrant credentials are not configured.")
    ensure_collection(client)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    from qdrant_client.models import PointStruct

    embedder = get_embedder()
    vectors = embedder.encode(chunks, normalize_embeddings=True).tolist()
    doc_id = hashlib.sha256(f"{name}:{text[:1000]}".encode()).hexdigest()[:16]
    points = [
        PointStruct(
            id=hashlib.sha256(f"{doc_id}:{i}".encode()).hexdigest()[:16],
            vector=vector,
            payload={"document": name, "document_id": doc_id, "chunk": i, "text": chunk},
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def search_context(question: str) -> list[dict]:
    client = get_qdrant()
    if client is None:
        return []
    ensure_collection(client)
    vector = get_embedder().encode([question], normalize_embeddings=True)[0].tolist()
    hits = client.query_points(collection_name=COLLECTION, query=vector, limit=TOP_K).points
    return [h.payload for h in hits if h.payload and h.payload.get("text")]


def call_llm(question: str, context: Iterable[dict], history: list[dict]) -> str:
    context_text = "\n\n".join(
        f"[{item.get('document', 'source')} · chunk {item.get('chunk', '?')}]\n{item['text']}"
        for item in context
    )
    system = (
        "You are MindMesh AI, a grounded knowledge assistant. Answer only from the supplied context "
        "when possible. If the context is insufficient, clearly say so. Cite sources inline using the "
        "document name and chunk number. Keep answers concise and useful."
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": f"Context:\n{context_text or '(no indexed context)'}\n\nQuestion: {question}"})

    groq_key = secret("GROQ_API_KEY")
    if groq_key:
        model = secret("GROQ_MODEL", "llama-3.3-70b-versatile")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}"},
            json={"model": model, "messages": messages, "temperature": 0.2},
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    gemini_key = secret("GEMINI_API_KEY")
    if gemini_key:
        from google import genai

        client = genai.Client(api_key=gemini_key)
        prompt = system + "\n\n" + "\n\n".join(m["content"] for m in messages[1:])
        return client.models.generate_content(model=secret("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt).text

    raise RuntimeError("Configure GROQ_API_KEY or GEMINI_API_KEY.")


def main() -> None:
    st.set_page_config(page_title="MindMesh AI · Streamlit", page_icon="🧠", layout="wide")
    st.markdown(
        """
        <style>
        .block-container {max-width: 1200px; padding-top: 2rem;}
        .hero {padding: 1.5rem 1.7rem; border: 1px solid rgba(255,255,255,.12); border-radius: 18px; margin-bottom: 1rem;}
        .muted {opacity: .7;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🧠 MindMesh AI")
    st.caption("Streamlit knowledge workspace · RAG over documents, audio and video")

    client = get_qdrant()
    if client is None:
        st.warning("Add QDRANT_URL and QDRANT_API_KEY to Streamlit secrets to enable indexing and search.")

    with st.sidebar:
        st.header("Knowledge Base")
        upload = st.file_uploader(
            "Add content",
            type=["pdf", "txt", "md", "csv", "mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
        )
        if upload and st.button("⚡ Process & Index", use_container_width=True):
            with st.spinner("Processing content…"):
                try:
                    text, kind = extract_content(upload)
                    count = index_document(upload.name, text)
                    st.session_state["last_ingest"] = {"name": upload.name, "kind": kind, "chunks": count}
                    st.success(f"Indexed {count} chunks from {upload.name}")
                except Exception as exc:
                    st.error(f"Processing failed: {exc}")

        st.divider()
        st.subheader("Runtime")
        st.write(f"Embedding: `{EMBED_MODEL}`")
        st.write(f"Top-K: `{TOP_K}`")
        st.write(f"LLM: `{('Groq' if secret('GROQ_API_KEY') else 'Gemini' if secret('GEMINI_API_KEY') else 'Not configured')}`")

    tabs = st.tabs(["💬 Ask MindMesh", "📚 Knowledge", "📊 Analytics"])

    with tabs[0]:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Ask a question about your knowledge base…")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                with st.spinner("Retrieving knowledge…"):
                    try:
                        context = search_context(question)
                        answer = call_llm(question, context, st.session_state.messages[:-1])
                        st.markdown(answer)
                        if context:
                            with st.expander("Sources"):
                                for item in context:
                                    st.caption(f"{item.get('document')} · chunk {item.get('chunk')}")
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as exc:
                        st.error(str(exc))

    with tabs[1]:
        st.subheader("Knowledge workspace")
        if client:
            try:
                info = client.get_collection(COLLECTION)
                st.metric("Indexed vectors", info.points_count or 0)
            except Exception:
                st.info("The collection will be created when your first document is indexed.")
        else:
            st.info("Connect Qdrant to view indexed content.")
        if st.session_state.get("last_ingest"):
            st.json(st.session_state["last_ingest"])

    with tabs[2]:
        st.subheader("Pipeline health")
        cols = st.columns(3)
        cols[0].metric("Vector DB", "Connected" if client else "Missing")
        cols[1].metric("LLM", "Ready" if (secret("GROQ_API_KEY") or secret("GEMINI_API_KEY")) else "Missing")
        cols[2].metric("Embedding", "Ready")


if __name__ == "__main__":
    main()

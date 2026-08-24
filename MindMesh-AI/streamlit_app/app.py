"""MindMesh AI Streamlit app backed by Supabase pgvector."""
from __future__ import annotations
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
TOP_K = int(os.getenv("RAG_TOP_K", "5"))

def secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)

def sb_url() -> str:
    return secret("SUPABASE_URL").rstrip("/")

def sb_key() -> str:
    return secret("SUPABASE_KEY") or secret("SUPABASE_ANON_KEY")

def sb_headers() -> dict[str, str]:
    key = sb_key()
    if not sb_url() or not key:
        raise RuntimeError("Configure SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def rpc(name: str, payload: dict):
    r = requests.post(f"{sb_url()}/rest/v1/rpc/{name}", headers=sb_headers(), json=payload, timeout=90)
    r.raise_for_status()
    return r.json()

def table(name: str, params: dict | None = None):
    r = requests.get(f"{sb_url()}/rest/v1/{name}", headers=sb_headers(), params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

@st.cache_resource(show_spinner=False)
def embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)

def chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = " ".join(text.split())
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        out.append(text[start:end])
        if end == len(text): break
        start = max(end - overlap, start + 1)
    return [x for x in out if x]

def pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data); path = f.name
    try: return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    finally: Path(path).unlink(missing_ok=True)

def media_text(data: bytes, suffix: str) -> str:
    from faster_whisper import WhisperModel
    with tempfile.TemporaryDirectory() as td:
        media, audio = Path(td) / f"input{suffix}", Path(td) / "audio.wav"
        media.write_bytes(data)
        subprocess.run(["ffmpeg","-y","-i",str(media),"-vn","-ac","1","-ar","16000",str(audio)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio), vad_filter=True)
        return " ".join(s.text.strip() for s in segments)

def extract(upload) -> tuple[str, str]:
    suffix, data = Path(upload.name).suffix.lower(), upload.getvalue()
    if suffix == ".pdf": return pdf_text(data), "PDF"
    if suffix in {".txt", ".md", ".csv"}: return data.decode("utf-8", errors="ignore"), "Text"
    if suffix in {".mp3",".wav",".m4a",".mp4",".mov",".mkv",".webm"}: return media_text(data, suffix), "Audio/Video"
    raise ValueError(f"Unsupported file type: {suffix}")

def index_document(name: str, kind: str, text: str) -> int:
    parts = chunks(text)
    if not parts: return 0
    doc_hash = hashlib.sha256(text.encode()).hexdigest()
    doc_id = rpc("upsert_mindmesh_document", {"p_name": name, "p_kind": kind, "p_content_hash": doc_hash})
    vectors = embedder().encode(parts, normalize_embeddings=True).tolist()
    rows = [{"chunk_index": i, "text": t, "embedding": v} for i, (t, v) in enumerate(zip(parts, vectors))]
    return int(rpc("insert_mindmesh_chunks", {"p_document_id": doc_id, "p_chunks": rows}) or 0)

def search(question: str) -> list[dict]:
    vector = embedder().encode([question], normalize_embeddings=True)[0].tolist()
    result = rpc("match_mindmesh_chunks", {"query_embedding": vector, "match_count": TOP_K})
    return result if isinstance(result, list) else []

def llm(question: str, context: list[dict], history: list[dict]) -> str:
    context_text = "\n\n".join(f"[{x.get('document')} · chunk {x.get('chunk_index')}]\n{x['text']}" for x in context)
    system = "You are MindMesh AI. Answer from the supplied context. If it is insufficient, say so. Cite document name and chunk number."
    messages = [{"role":"system","content":system}, *history[-6:], {"role":"user","content":f"Context:\n{context_text or '(none)'}\n\nQuestion: {question}"}]
    key = secret("GROQ_API_KEY")
    if key:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization":f"Bearer {key}"}, json={"model":secret("GROQ_MODEL","llama-3.3-70b-versatile"),"messages":messages,"temperature":0.2}, timeout=90)
        r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
    key = secret("GEMINI_API_KEY")
    if key:
        from google import genai
        client = genai.Client(api_key=key)
        return client.models.generate_content(model=secret("GEMINI_MODEL","gemini-2.5-flash"), contents=system+"\n\n"+"\n\n".join(m["content"] for m in messages[1:])).text
    raise RuntimeError("Configure GROQ_API_KEY or GEMINI_API_KEY.")

def main():
    st.set_page_config(page_title="MindMesh AI", page_icon="🧠", layout="wide")
    st.title("🧠 MindMesh AI")
    st.caption("AI knowledge workspace powered by Supabase pgvector")
    connected = bool(sb_url() and sb_key())
    if not connected: st.warning("Configure SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
    with st.sidebar:
        st.header("Knowledge Base")
        upload = st.file_uploader("Add content", type=["pdf","txt","md","csv","mp3","wav","m4a","mp4","mov","mkv","webm"])
        if upload and st.button("⚡ Process & Index", disabled=not connected, use_container_width=True):
            try:
                with st.spinner("Processing and indexing…"):
                    text, kind = extract(upload); count = index_document(upload.name, kind, text)
                st.success(f"Indexed {count} chunks")
            except Exception as e: st.error(f"Processing failed: {e}")
        st.divider(); st.write("Database: `Supabase`" if connected else "Database: `Not configured`"); st.write(f"Embedding: `{EMBED_MODEL}`"); st.write(f"Top-K: `{TOP_K}`")
    ask, knowledge, analytics = st.tabs(["💬 Ask MindMesh","📚 Knowledge","📊 Analytics"])
    with ask:
        if "messages" not in st.session_state: st.session_state.messages=[]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        q = st.chat_input("Ask about your knowledge base…")
        if q:
            st.session_state.messages.append({"role":"user","content":q})
            with st.chat_message("user"): st.markdown(q)
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Searching knowledge…"): ctx=search(q); answer=llm(q,ctx,st.session_state.messages[:-1])
                    st.markdown(answer)
                    if ctx:
                        with st.expander("Sources"):
                            for x in ctx: st.caption(f"{x.get('document')} · chunk {x.get('chunk_index')} · {float(x.get('similarity',0)):.3f}")
                    st.session_state.messages.append({"role":"assistant","content":answer})
                except Exception as e: st.error(str(e))
    with knowledge:
        st.subheader("Knowledge workspace")
        if connected:
            try:
                docs=table("mindmesh_documents", {"select":"id,name,kind,created_at","order":"created_at.desc"})
                st.metric("Documents",len(docs)); st.dataframe(docs,use_container_width=True,hide_index=True)
            except Exception as e: st.error(f"Could not load knowledge base: {e}")
    with analytics:
        cols=st.columns(4); cols[0].metric("Supabase","Ready" if connected else "Missing"); cols[1].metric("Embeddings","Ready"); cols[2].metric("LLM","Ready" if secret("GROQ_API_KEY") or secret("GEMINI_API_KEY") else "Missing"); cols[3].metric("Media","FFmpeg")

if __name__ == "__main__": main()

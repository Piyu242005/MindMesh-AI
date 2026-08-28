import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.transcription import get_whisper_model, process_video
from backend.embeddings import get_embedding_model, get_qdrant_client, index_json_file

st.title("📤 Upload & Process")
st.caption("Add a video or audio lesson to your MindMesh knowledge base.")

uploaded = st.file_uploader("Choose media", type=["mp3", "mp4", "m4a", "mov", "mkv", "wav", "webm"])
col1, col2 = st.columns(2)
with col1:
    number = st.text_input("Lesson number", placeholder="01")
with col2:
    title = st.text_input("Lesson title", placeholder="Introduction to HTML")

if uploaded:
    st.audio(uploaded) if uploaded.type.startswith("audio") else st.video(uploaded)

if st.button("🚀 Process content", type="primary", disabled=uploaded is None):
    if not number or not title:
        st.warning("Please enter the lesson number and title.")
        st.stop()

    videos = ROOT / "videos"
    audios = ROOT / "audios"
    jsons = ROOT / "jsons"
    for folder in (videos, audios, jsons):
        folder.mkdir(parents=True, exist_ok=True)

    suffix = Path(uploaded.name).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}_{Path(uploaded.name).name.replace(' ', '_')}"
    target = videos / safe_name
    target.write_bytes(uploaded.getbuffer())

    progress = st.progress(0, text="Starting transcription...")
    try:
        whisper = get_whisper_model()
        progress.progress(35, text="Transcribing with Faster-Whisper...")
        result = process_video(target, number, title, whisper, videos, audios, jsons, language="hi", task="translate")
        json_path = result.get("json_path") if isinstance(result, dict) else None
        progress.progress(70, text="Creating semantic embeddings...")

        client, err = get_qdrant_client()
        if client and json_path:
            index_result = index_json_file(Path(json_path), client, get_embedding_model())
        else:
            index_result = {"chunks": 0, "error": err or "No Qdrant client"}

        progress.progress(100, text="Completed")
        st.success(f"'{title}' is ready. Indexed {index_result.get('chunks', 0)} chunks.")
        if index_result.get("error"):
            st.warning(f"Transcript created, but vector indexing needs attention: {index_result['error']}")
    except Exception as exc:
        st.error(f"Processing failed: {exc}")

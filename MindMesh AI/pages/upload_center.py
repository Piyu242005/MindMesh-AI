"""
pages/upload_center.py — MindMesh AI
Full video upload pipeline: Upload → Extract Audio → Transcribe → Embed → Qdrant.
Supports single and batch video uploads.
"""

import sys
import time
import tempfile
import json
from pathlib import Path
from datetime import datetime

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend import transcription as tx
from backend import embeddings as emb
from backend.embeddings import get_qdrant_client, get_embedding_model
import qdrant_helper as qh

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-page-header">
  <p class="mm-page-title">📤 Upload Center</p>
  <p class="mm-page-subtitle">Upload course videos → automatic transcription and indexing</p>
</div>
""", unsafe_allow_html=True)

# ── Load resources ────────────────────────────────────────────────────────────
qdrant_client, qdrant_err = get_qdrant_client()
qdrant_ok = qdrant_client is not None

# ── Availability warnings ─────────────────────────────────────────────────────
col_ff, col_wh, col_qd = st.columns(3)
with col_ff:
    if tx.is_ffmpeg_available():
        st.markdown('<span class="mm-badge mm-badge-ok">● FFmpeg Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mm-badge mm-badge-err">● FFmpeg Missing</span>', unsafe_allow_html=True)
with col_wh:
    if tx.is_whisper_available():
        st.markdown('<span class="mm-badge mm-badge-ok">● Whisper Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mm-badge mm-badge-err">● Whisper Missing</span>', unsafe_allow_html=True)
with col_qd:
    if qdrant_ok:
        st.markdown('<span class="mm-badge mm-badge-ok">● Qdrant Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mm-badge mm-badge-warn">● Qdrant Offline (embed only)</span>', unsafe_allow_html=True)

st.divider()

# ── Upload form ───────────────────────────────────────────────────────────────
st.subheader("📁 Upload Videos")

with st.form("upload_form"):
    uploaded_files = st.file_uploader(
        "Drop your course videos here",
        type=["mp4", "mkv", "mov", "avi", "webm"],
        accept_multiple_files=True,
        help="Multiple files supported — each is processed sequentially",
    )

    c1, c2 = st.columns(2)
    with c1:
        video_number = st.text_input(
            "Video Number",
            placeholder="e.g. 42",
            help="Unique lecture/video number for this batch",
        )
    with c2:
        video_title = st.text_input(
            "Video Title",
            placeholder="e.g. CSS Flexbox Deep Dive",
            help="Used as the lecture title in search results",
        )

    lang_col, task_col = st.columns(2)
    with lang_col:
        language = st.selectbox(
            "Source Language",
            ["hi", "en", "auto"],
            index=0,
            help="Language spoken in the video",
        )
    with task_col:
        task = st.selectbox(
            "Whisper Task",
            ["translate", "transcribe"],
            index=0,
            help="'translate' → English | 'transcribe' → keep original language",
        )

    submit = st.form_submit_button("🚀 Start Processing", use_container_width=True)

# ── Batch Reindex All ─────────────────────────────────────────────────────────
st.divider()
st.subheader("🔄 Reindex All Videos")
st.caption("Re-embed all existing JSON files and upload to Qdrant Cloud.")

rc1, rc2 = st.columns([1, 3])
with rc1:
    do_reindex = st.button("🔄 Reindex All Videos", use_container_width=True, type="primary")
with rc2:
    jsons_dir    = _ROOT / "jsons"
    json_count   = len(list(jsons_dir.glob("*.json"))) if jsons_dir.exists() else 0
    st.info(f"**{json_count}** JSON files ready · Collection: `{qh.QDRANT_COLLECTION}`")

# ── Handle Reindex ─────────────────────────────────────────────────────────────
if do_reindex:
    if not qdrant_ok:
        st.error("Qdrant is offline. Fill in `.env` credentials and restart.")
    elif json_count == 0:
        st.warning("No JSON files in `jsons/`. Upload and process videos first.")
    else:
        st.divider()
        st.subheader("📡 Reindex Progress")

        model       = get_embedding_model()
        overall_bar = st.progress(0.0, text="Starting…")
        file_log    = st.empty()
        upload_bar  = st.progress(0.0, text="Waiting for upload…")

        _processed_files = []

        def _on_file(name, idx, total):
            overall_bar.progress((idx + 1) / total, text=f"Encoding {idx+1}/{total}: {name}")
            file_log.success(f"✓ `{name}`")
            _processed_files.append(name)

        def _on_upload(done, total):
            upload_bar.progress(done / total, text=f"Uploading {done:,}/{total:,} vectors…")

        result = emb.reindex_all(
            jsons_dir      = jsons_dir,
            qdrant_client  = qdrant_client,
            model          = model,
            batch_size     = st.session_state.embed_batch_size,
            on_file        = _on_file,
            on_upload      = _on_upload,
        )

        overall_bar.progress(1.0, text="Complete ✓")
        upload_bar.progress(1.0, text="Upload complete ✓")

        if result.get("error"):
            st.error(f"Error: {result['error']}")
        else:
            st.success(f"""
✅ **Reindex Complete!**

| | |
|---|---|
| Files processed | {result['files']} |
| Vectors uploaded | {result['uploaded']:,} |
| Collection | `{qh.QDRANT_COLLECTION}` |
            """)
            st.cache_resource.clear()

# ── Handle video upload + pipeline ────────────────────────────────────────────
if submit and uploaded_files:
    if not video_number.strip() or not video_title.strip():
        st.error("Please fill in Video Number and Video Title before processing.")
        st.stop()

    if not tx.is_ffmpeg_available():
        st.error("FFmpeg is not installed. Cannot extract audio from videos.")
        st.stop()

    if not tx.is_whisper_available():
        st.error("Faster-Whisper is not installed. Run: `pip install faster-whisper`")
        st.stop()

    st.divider()
    st.subheader(f"🎬 Processing {len(uploaded_files)} video(s)")

    videos_dir = _ROOT / "videos"
    audios_dir = _ROOT / "audios"
    jsons_dir  = _ROOT / "jsons"

    embed_model     = get_embedding_model()
    whisper_model   = tx.get_whisper_model(st.session_state.whisper_model_size)

    for file_idx, uploaded in enumerate(uploaded_files):
        video_stem = Path(uploaded.name).stem
        num_label  = f"{video_number}_{file_idx}" if len(uploaded_files) > 1 else video_number

        with st.container():
            st.markdown(f"**📹 {uploaded.name}** ({uploaded.size / 1024 / 1024:.1f} MB)")

            # Step display
            step_area = st.empty()

            steps = {
                "💾 Save Video":      ("pending", ""),
                "🎵 Extract Audio":   ("pending", ""),
                "🗣️ Transcribe":      ("pending", ""),
                "💡 Generate Embeds": ("pending", ""),
                "☁️ Upload to Qdrant":("pending", ""),
            }

            def _render_steps(steps_dict):
                html = ""
                for name, (st_val, detail) in steps_dict.items():
                    css = {
                        "pending": "mm-step-pending",
                        "active":  "mm-step-active",
                        "done":    "mm-step-done",
                        "error":   "mm-step-error",
                    }.get(st_val, "")
                    icon = {"pending":"○","active":"⟳","done":"✓","error":"✗"}.get(st_val,"○")
                    step_area.markdown(
                        html + f'<div class="mm-step {css}"><span class="mm-step-icon">{icon}</span>'
                               f'<span class="mm-step-text">{name}</span>'
                               f'<span class="mm-step-detail">{detail}</span></div>',
                        unsafe_allow_html=True,
                    )

            def _set_step(name, status, detail=""):
                steps[name] = (status, detail)
                _render_steps(steps)

            try:
                # 1. Save uploaded file to disk
                _set_step("💾 Save Video", "active", uploaded.name)
                video_path = videos_dir / uploaded.name
                video_path.write_bytes(uploaded.read())
                _set_step("💾 Save Video", "done", f"{video_path.stat().st_size / 1024 / 1024:.1f} MB saved")

                # 2–3. Extract audio + transcribe via process_video
                result = tx.process_video(
                    video_path     = video_path,
                    video_number   = num_label,
                    video_title    = video_title,
                    whisper_model  = whisper_model,
                    videos_dir     = videos_dir,
                    audios_dir     = audios_dir,
                    jsons_dir      = jsons_dir,
                    language       = language,
                    task           = task,
                    on_step        = lambda n, s, d: (
                        _set_step("🎵 Extract Audio", s, d) if "Extract" in n
                        else _set_step("🗣️ Transcribe", s, d) if "Transcribe" in n or "Save" not in n and "Embed" not in n and "Qdrant" not in n
                        else _set_step("💾 Save Video", s, d)
                    ),
                )
                chunks    = result["chunks"]
                json_path = result["json_path"]
                _set_step("🗣️ Transcribe",      "done", f"{len(chunks)} chunks")

                # 4. Generate embeddings
                _set_step("💡 Generate Embeds", "active", f"Encoding {len(chunks)} chunks…")
                points = emb.build_points_from_json(json_path, embed_model)
                _set_step("💡 Generate Embeds", "done", f"{len(points)} vectors (dim=384)")

                # 5. Upload to Qdrant
                if qdrant_ok and points:
                    _set_step("☁️ Upload to Qdrant", "active", f"Uploading {len(points)} points…")
                    uploaded_count = qh.upload_points_batch(qdrant_client, points)
                    _set_step("☁️ Upload to Qdrant", "done", f"{uploaded_count} vectors stored")
                else:
                    _set_step("☁️ Upload to Qdrant", "pending", "Skipped (Qdrant offline)")

                st.success(f"✅ `{uploaded.name}` processed successfully · {len(chunks)} chunks indexed")

            except Exception as e:
                # Mark current active step as error
                for name, (sv, _) in steps.items():
                    if sv == "active":
                        _set_step(name, "error", str(e)[:120])
                        break
                st.error(f"Pipeline failed on `{uploaded.name}`: {e}")

        st.divider()

elif submit and not uploaded_files:
    st.warning("Please select at least one video file.")

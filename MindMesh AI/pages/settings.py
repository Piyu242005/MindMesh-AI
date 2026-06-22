"""
pages/settings.py — MindMesh AI
Configure LLM model, retrieval parameters, embeddings, and Qdrant connection.
"""

import sys
import os
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qdrant_helper as qh
from backend.embeddings import get_qdrant_client
from backend.retrieval import get_ollama_models, is_ollama_running

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-page-header">
  <p class="mm-page-title">⚙️ Settings</p>
  <p class="mm-page-subtitle">Configure LLM, retrieval, embeddings, and connections</p>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1])

# ══════════════════════════════════════════════════════
# LEFT COLUMN
# ══════════════════════════════════════════════════════

with left:

    # ── LLM Configuration ──────────────────────────────
    st.subheader("🤖 LLM Configuration")

    ollama_up     = is_ollama_running()
    pulled_models = get_ollama_models()

    # Status
    if ollama_up:
        st.markdown(f'<span class="mm-badge mm-badge-ok">● Ollama Running · {len(pulled_models)} model(s)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mm-badge mm-badge-err">● Ollama Offline — run `ollama serve`</span>', unsafe_allow_html=True)

    st.write("")

    # Model selector — prefer pulled models, fallback to common list
    common_models = ["llama3.2", "llama3.1", "gemma3:4b", "deepseek-r1", "mistral", "phi3", "qwen2.5"]
    all_models    = list(dict.fromkeys(pulled_models + common_models))  # deduplicate, pulled first

    cur = st.session_state.selected_model
    idx = all_models.index(cur) if cur in all_models else 0

    st.session_state.selected_model = st.selectbox(
        "Ollama Model",
        all_models,
        index=idx,
        help="Pulled models appear first. Others can be pulled: `ollama pull <name>`",
    )

    if st.session_state.selected_model in pulled_models:
        st.caption(f"✓ `{st.session_state.selected_model}` is available locally")
    else:
        st.caption(f"⚠️ Run: `ollama pull {st.session_state.selected_model}`")

    st.divider()

    # ── Retrieval Configuration ─────────────────────────
    st.subheader("🔍 Retrieval Configuration")

    st.session_state.top_k = st.slider(
        "Top-K Chunks",
        min_value=1, max_value=20,
        value=st.session_state.top_k,
        help="Number of chunks retrieved from Qdrant per query. Higher = more context.",
    )

    st.session_state.score_threshold = st.slider(
        "Similarity Threshold",
        min_value=0.0, max_value=1.0,
        value=float(st.session_state.score_threshold),
        step=0.05,
        format="%.2f",
        help="Minimum cosine similarity score (0 = no filter, 1 = exact match only).",
    )

    st.caption(f"Current: Top-{st.session_state.top_k} · threshold ≥ {st.session_state.score_threshold:.2f}")

    st.divider()

    # ── Whisper Configuration ───────────────────────────
    st.subheader("🗣️ Whisper Configuration")

    st.session_state.whisper_model_size = st.selectbox(
        "Whisper Model",
        ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        index=["tiny","base","small","medium","large","large-v2","large-v3"].index(
            st.session_state.whisper_model_size
        ),
        help="Larger = more accurate, slower. large-v2 recommended.",
    )

    st.session_state.whisper_language = st.selectbox(
        "Source Language",
        ["hi", "en", "auto", "ta", "te", "mr", "bn", "gu"],
        index=["hi","en","auto","ta","te","mr","bn","gu"].index(
            st.session_state.get("whisper_language", "hi")
        ),
        help="Language spoken in the videos",
    )

    st.session_state.whisper_task = st.selectbox(
        "Task",
        ["translate", "transcribe"],
        index=["translate","transcribe"].index(
            st.session_state.get("whisper_task", "translate")
        ),
        help="'translate' → always outputs English | 'transcribe' → keeps source language",
    )


# ══════════════════════════════════════════════════════
# RIGHT COLUMN
# ══════════════════════════════════════════════════════

with right:

    # ── Embeddings Configuration ────────────────────────
    st.subheader("🧠 Embeddings Configuration")

    model_name_display = "BAAI/bge-small-en-v1.5"
    st.text_input("Embedding Model", value=model_name_display, disabled=True,
                  help="Model is fixed. Change requires re-embedding all data.")
    st.caption("Dimension: 384 · Distance: Cosine · Normalised: Yes")

    st.session_state.embed_batch_size = st.slider(
        "Embedding Batch Size",
        min_value=8, max_value=256,
        value=st.session_state.embed_batch_size,
        step=8,
        help="Number of texts encoded per batch. Higher = faster, more RAM.",
    )

    st.divider()

    # ── Qdrant Configuration ────────────────────────────
    st.subheader("🌐 Qdrant Configuration")

    qdrant_client, qdrant_err = get_qdrant_client()
    qdrant_ok = qdrant_client is not None

    if qdrant_ok:
        st.markdown('<span class="mm-badge mm-badge-ok">● Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mm-badge mm-badge-err">● Offline</span>', unsafe_allow_html=True)

    st.write("")

    qdrant_url = os.getenv("QDRANT_URL", "Not set")
    qdrant_col = os.getenv("QDRANT_COLLECTION", "mindmesh_courses")
    api_set    = bool(os.getenv("QDRANT_API_KEY", "").strip())

    st.text_input("QDRANT_URL",        value=qdrant_url, disabled=True)
    st.text_input("QDRANT_COLLECTION", value=qdrant_col, disabled=True)

    if api_set:
        st.success("🔑 QDRANT_API_KEY is set (hidden)")
    else:
        st.error("🔑 QDRANT_API_KEY not set — add to `.env`")

    if qdrant_ok:
        info = qh.collection_info(qdrant_client)
        st.markdown(f"""
<div class="mm-stat-strip">
  <span class="mm-stat-chip">Vectors: {info.get('vector_count',0):,}</span>
  <span class="mm-stat-chip">Status: {info.get('status','?')}</span>
  <span class="mm-stat-chip">Dim: {info.get('vector_size',384)}</span>
</div>
""", unsafe_allow_html=True)

    # Health check button
    st.write("")
    if st.button("🏥 Run Qdrant Health Check", use_container_width=True):
        if qdrant_ok:
            ok, msg = qh.health_check(qdrant_client)
            if ok:
                st.success(f"✓ {msg}")
            else:
                st.error(f"✗ {msg}")
        else:
            st.error(f"Cannot connect: {qdrant_err}")

    st.divider()

    # ── Reset / Reconnect ────────────────────────────────
    st.subheader("🔧 Maintenance")

    ma, mb = st.columns(2)
    with ma:
        if st.button("🔄 Reconnect All", use_container_width=True):
            st.cache_resource.clear()
            st.success("Cache cleared — resources will reload.")
            st.rerun()
    with mb:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.query_count  = 0
            st.session_state.response_times = []
            st.session_state.query_timestamps = []
            st.session_state.popular_topics = {}
            st.success("Chat history and analytics reset.")

    st.divider()

    # ── Migration phase tracker ──────────────────────────
    st.subheader("📋 Migration Phase")
    st.markdown("""
| Phase | Description | Status |
|---|---|---|
| **Phase 1** | Qdrant primary + joblib fallback | 🟢 Current |
| **Phase 2** | `python validate_qdrant.py` | ⬜ Run when ready |
| **Phase 3** | Remove joblib imports | ⬜ After Phase 2 |
    """)

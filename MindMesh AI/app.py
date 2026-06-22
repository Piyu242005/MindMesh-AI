"""
app.py — MindMesh AI
Main Streamlit entry point.
Run: streamlit run app.py

Registers all pages, injects CSS, initialises session state,
and renders the sidebar branding + status strip.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# ── Ensure root on sys.path (so backend/ and qdrant_helper import) ────────────
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Ensure required directories exist ────────────────────────────────────────
for _d in ["videos", "audios", "jsons"]:
    (ROOT / _d).mkdir(exist_ok=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MindMesh AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
_css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    # Settings — LLM
    "selected_model":        os.getenv("OLLAMA_MODEL", "llama3.2"),
    # Settings — Retrieval
    "top_k":                 5,
    "score_threshold":       0.0,
    # Settings — Embeddings
    "embed_batch_size":      64,
    "whisper_model_size":    "large-v2",
    "whisper_language":      "hi",
    "whisper_task":          "translate",
    # Chat
    "chat_history":          [],   # [{role, content, sources, ts}]
    # Analytics counters
    "query_count":           0,
    "response_times":        [],   # list of float seconds
    "query_timestamps":      [],   # list of ISO timestamp strings
    "popular_topics":        {},   # word → count
    # Misc
    "last_system_check":     None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Navigation ────────────────────────────────────────────────────────────────
_pg = st.navigation(
    {
        "🏠 Overview": [
            st.Page("pages/dashboard.py",      title="Dashboard",      icon="📊", default=True),
        ],
        "📚 Content": [
            st.Page("pages/upload_center.py",  title="Upload Center",  icon="📤"),
            st.Page("pages/course_library.py", title="Course Library", icon="📚"),
        ],
        "🤖 Intelligence": [
            st.Page("pages/ai_chat.py",        title="AI Chat",        icon="💬"),
            st.Page("pages/analytics.py",      title="Analytics",      icon="📈"),
        ],
        "⚙️ Config": [
            st.Page("pages/settings.py",       title="Settings",       icon="⚙️"),
        ],
    }
)

# ── Sidebar branding (shown on every page) ────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p class="mm-logo">Mind<span>Mesh</span> AI</p>',
        unsafe_allow_html=True,
    )
    st.caption("RAG · Qdrant · Ollama · Whisper")
    st.divider()

# ── Run selected page ─────────────────────────────────────────────────────────
_pg.run()

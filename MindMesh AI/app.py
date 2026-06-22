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
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ────────────────────────────────────────────────────────────────
_css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
_defaults = {
    # Settings — LLM
    "llm_provider":          os.getenv("LLM_PROVIDER", "gemini"),
    "gemini_model":          os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "groq_model":            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "selected_model":        os.getenv("OLLAMA_MODEL", "llama3.2"),
    
    # LLM Cost/Token Tracking
    "llm_metrics":           {
        "total_requests": 0,
        "total_tokens": 0,
        "response_times": []
    },
    # Settings — Retrieval
    "top_k":                 5,
    "score_threshold":       0.0,
    # Settings — Embeddings
    "embed_batch_size":      64,
    "whisper_model_size":    "medium",
    "whisper_language":      "hi",
    "whisper_task":          "translate",
    # Chat
    "chat_history":          [],   # [{role, content, sources, ts}]
    # Analytics counters
    "query_count":           0,
    "response_times":        [],   # list of float seconds
    "query_timestamps":      [],   # list of ISO timestamp strings
    "popular_topics":        {},   # word → count
    # Onboarding
    "onboarding_completed":  False,
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
            st.Page("pages/getting_started.py",title="Getting Started",icon="📚"),
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
    st.logo("assets/logo.png", icon_image="assets/logo.png")
    st.markdown(
        '<p class="mm-logo" style="margin-bottom:0;">🧠 Mind<span>Mesh</span> AI</p>',
        unsafe_allow_html=True,
    )
    st.caption("Transform Video Courses into Knowledge")
    st.divider()
    
    st.markdown(
        """<div style="font-size:0.75rem; color:rgba(255,255,255,0.4); text-align:center;">
        MindMesh AI v1.0<br/>
        AI-Powered Learning Intelligence<br/>
        Built by Piyush Ramteke
        </div>""", unsafe_allow_html=True
    )
    
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("❓ How It Works", use_container_width=True):
        st.session_state["onboarding_completed"] = False
        st.rerun()

# ── Trigger Onboarding Modal ──────────────────────────────────────────────────
if not st.session_state.get("onboarding_completed", False):
    from components.onboarding_modal import show_onboarding
    show_onboarding()

# ── Run selected page ─────────────────────────────────────────────────────────
_pg.run()

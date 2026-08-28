import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="MindMesh AI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: #080808; color: #f5f5f5; }
[data-testid="stSidebar"] { background: #0d0d0d; border-right: 1px solid #2a2a2a; }
.block-container { padding-top: 2rem; max-width: 1400px; }
.mm-card { background:#111; border:1px solid #292929; border-radius:16px; padding:22px; margin-bottom:16px; }
.mm-red { color:#ff3b30; }
.mm-muted { color:#999; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 🧠 MindMesh AI")
    st.caption("Streamlit Edition")
    st.divider()
    st.success("System ready")
    st.markdown("### Quick Start")
    st.markdown("1. Upload a course\n2. Process it\n3. Ask questions\n4. Explore your knowledge")
    st.divider()
    st.caption("Powered by Faster-Whisper · Qdrant · Multi-LLM")

st.markdown("# Turn courses into knowledge")
st.markdown("Ask questions about your videos and audio instead of searching through hours of content.")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="mm-card"><h3>🎙️ Transcribe</h3><p class="mm-muted">Convert video and audio into searchable text.</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="mm-card"><h3>🔎 Understand</h3><p class="mm-muted">Find the most relevant course sections with semantic search.</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="mm-card"><h3>🤖 Ask</h3><p class="mm-muted">Get simple answers with source timestamps.</p></div>', unsafe_allow_html=True)

st.info("Use the pages in the left sidebar to upload content, chat with your knowledge base, and view analytics.")

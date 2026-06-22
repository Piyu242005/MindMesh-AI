"""
pages/dashboard.py — MindMesh AI
System status overview, live Qdrant metrics, and quick-action buttons.
"""

import sys
import time
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qdrant_helper as qh
from backend import verify_system
from backend.embeddings import get_qdrant_client

col_logo, col_text = st.columns([1, 6])
with col_logo:
    st.image("assets/logo.png", width=100)
with col_text:
    st.markdown("""
    <h1 style="margin-bottom:0;">MindMesh AI</h1>
    <h3 style="margin-top:0; color:var(--text-2);">Transform Video Courses Into Intelligent Knowledge Networks</h3>
    <div style="color:var(--text-3); font-size:0.9rem;">
      <b>Powered by:</b> Faster-Whisper • Qdrant Cloud • Gemini
    </div>
    """, unsafe_allow_html=True)
st.divider()

# ── Live Qdrant metrics ───────────────────────────────────────────────────────
qdrant_client, qdrant_err = get_qdrant_client()
qdrant_ok = qdrant_client is not None

if qdrant_ok:
    info       = qh.collection_info(qdrant_client)
    vec_count  = info.get("vector_count", 0)
    col_status = info.get("status", "unknown").title()
else:
    vec_count  = 0
    col_status = "Offline"

# Count courses (JSON files)
jsons_dir   = _ROOT / "jsons"
json_files  = list(jsons_dir.glob("*.json")) if jsons_dir.exists() else []
total_chunks = 0
for jf in json_files:
    try:
        import json
        d = json.loads(jf.read_text(encoding="utf-8"))
        total_chunks += len(d.get("chunks", []))
    except Exception:
        pass

# Count metrics from session state
metrics = st.session_state.get("llm_metrics", {"total_requests": 0, "total_tokens": 0, "response_times": []})
total_requests = metrics["total_requests"]
avg_latency = sum(metrics["response_times"]) / len(metrics["response_times"]) if metrics["response_times"] else 0.0

# ── Metric row ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: st.metric("📚 Courses",        len(json_files))
with c2: st.metric("📄 Chunks",         f"{total_chunks:,}")
with c3: st.metric("🗄️ Vectors",        f"{vec_count:,}")
with c4: st.metric("💬 LLM Requests",   total_requests)
with c5: st.metric("📦 Collection",     col_status)
with c6: st.metric("⏱️ Avg Latency",   f"{avg_latency:.2f}s")

st.divider()

# ── System status ─────────────────────────────────────────────────────────────
col_sys, col_qdrant = st.columns([1, 1])

with col_sys:
    st.subheader("🔧 System Status")

    with st.spinner("Running checks…"):
        checks = verify_system()

    _BADGE = {
        "ok":    ("mm-badge-ok",   "●"),
        "warn":  ("mm-badge-warn", "●"),
        "error": ("mm-badge-err",  "●"),
    }

    # Show only the core service checks (not folders/env) in the summary
    service_keys = ["FFmpeg", "Whisper", "SentenceTransformers", "Qdrant"]

    for key in service_keys:
        if key not in checks:
            continue
        status, label, detail = checks[key]
        cls, dot = _BADGE.get(status, ("mm-badge-off", "○"))
        st.markdown(f"""
<div class="mm-check-row">
  <span class="mm-check-label">{key}</span>
  <span class="mm-badge {cls}">{dot} {label}</span>
</div>
<div style="padding:0 0 4px 2px;font-size:0.75rem;color:rgba(255,255,255,0.32)">{detail}</div>
""", unsafe_allow_html=True)
        
    from backend.llm_manager import check_providers
    llm_status = check_providers()
    provider = st.session_state.get("llm_provider", "gemini")
    
    # Select the correct model based on provider
    if provider == "gemini":
        model_name = st.session_state.get("gemini_model", "gemini-2.5-flash")
    elif provider == "groq":
        model_name = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
    else:
        model_name = st.session_state.get("selected_model", "llama3.2")
        
    st.markdown(f"""
<div class="mm-card" style="margin-top: 15px">
  <div class="mm-card-title">LLM Gateway</div>
  <div style="margin-top:12px">
    <div class="mm-check-row">
      <span class="mm-check-label">Active Provider</span>
      <span class="mm-badge mm-badge-ok">● {provider.capitalize()}</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Active Model</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">{model_name}</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Estimated Tokens</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">{metrics['total_tokens']:,}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

with col_qdrant:
    st.subheader("🌐 Qdrant Cloud")

    if qdrant_ok:
        status_lower = col_status.lower()
        if "error" in status_lower or "not found" in status_lower:
            badge_cls = "mm-badge-err"
            display_status = "Not Created"
        elif "yellow" in status_lower:
            badge_cls = "mm-badge-warn"
            display_status = "Degraded"
        elif "green" in status_lower or "ok" in status_lower:
            badge_cls = "mm-badge-ok"
            display_status = "Ready"
        else:
            badge_cls = "mm-badge-warn"
            display_status = col_status

        st.markdown(f"""
<div class="mm-card">
  <div class="mm-card-title">Collection: <code>{qh.QDRANT_COLLECTION}</code></div>
  <div style="margin-top:12px">
    <div class="mm-check-row">
      <span class="mm-check-label">Status</span>
      <span class="mm-badge {badge_cls}">● {display_status}</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Vector Count</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">{vec_count:,}</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Embedding Dim</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">384</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Distance</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">Cosine</span>
    </div>
    <div class="mm-check-row">
      <span class="mm-check-label">Model</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:white">bge-small-en-v1.5</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.error(f"""
**⚠️ Qdrant Offline**

{qdrant_err or 'Connection failed'}

**Fix:** Add credentials to `MindMesh AI/.env`:
```
QDRANT_URL=https://xxxx.qdrant.io
QDRANT_API_KEY=your-key
QDRANT_COLLECTION=mindmesh_courses
```
""")

st.divider()

# ── Environment / folder checks ───────────────────────────────────────────────
with st.expander("📋 Environment & Folder Checks", expanded=False):
    other_keys = [k for k in checks if k not in service_keys]
    for key in other_keys:
        status, label, detail = checks[key]
        cls, dot = _BADGE.get(status, ("mm-badge-off", "○"))
        st.markdown(f"""
<div class="mm-check-row">
  <span class="mm-check-label">{key}</span>
  <span class="mm-badge {cls}">{dot} {label}</span>
</div>
<div style="padding:0 0 6px 2px;font-size:0.75rem;color:rgba(255,255,255,0.32)">{detail}</div>
""", unsafe_allow_html=True)

st.divider()

# ── Quick actions ─────────────────────────────────────────────────────────────
st.subheader("⚡ Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)

with qa1:
    if st.button("🔄 Refresh Stats", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

with qa2:
    if st.button("✅ Re-run Checks", use_container_width=True):
        st.session_state.pop("last_system_check", None)
        st.rerun()

with qa3:
    if st.button("📤 Upload Videos", use_container_width=True):
        st.switch_page("pages/upload_center.py")

with qa4:
    if st.button("💬 Open AI Chat", use_container_width=True):
        st.switch_page("pages/ai_chat.py")

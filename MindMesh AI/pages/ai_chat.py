"""
pages/ai_chat.py — MindMesh AI
ChatGPT-style RAG chat with streaming responses, source citations, and session memory.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.embeddings import get_qdrant_client, get_embedding_model
from backend import retrieval as ret
import qdrant_helper as qh

# ── Page header ───────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("assets/logo.png", width=60)
with col_title:
    st.markdown("""
    <div class="mm-page-header" style="border-bottom:none; margin-bottom:0; padding-bottom:0;">
      <p class="mm-page-title" style="font-size:1.5rem;">AI Chat</p>
      <p class="mm-page-subtitle">Ask anything about your course — powered by Qdrant + RAG</p>
    </div>
    """, unsafe_allow_html=True)

# ── Load cached resources ─────────────────────────────────────────────────────
qdrant_client, qdrant_err = get_qdrant_client()
embed_model  = get_embedding_model()
qdrant_ok    = qdrant_client is not None

# ── Status bar ────────────────────────────────────────────────────────────────
col_ret, col_llm, col_topk = st.columns(3)
with col_ret:
    src = "Qdrant Cloud" if qdrant_ok else "Local (joblib)"
    st.markdown(f'<span class="mm-badge {"mm-badge-ok" if qdrant_ok else "mm-badge-warn"}">● Retrieval: {src}</span>', unsafe_allow_html=True)
with col_llm:
    from backend.llm_manager import check_providers
    llm_status = check_providers()
    provider = st.session_state.get("llm_provider", "gemini")
    
    if provider == "gemini":
        active_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
    elif provider == "groq":
        active_model = st.session_state.get("groq_model", "llama-3.3-70b-versatile")
    else:
        active_model = st.session_state.get("selected_model", "llama3.2")
        
    is_up = llm_status.get(provider, (False,))[0]
    st.markdown(f'<span class="mm-badge {"mm-badge-ok" if is_up else "mm-badge-err"}">● {provider.capitalize()}: {active_model}</span>', unsafe_allow_html=True)
with col_topk:
    st.markdown(f'<span class="mm-badge mm-badge-off">○ Top-K: {st.session_state.top_k}</span>', unsafe_allow_html=True)

st.divider()

# ── Data availability guard ───────────────────────────────────────────────────
joblib_path = _ROOT / "embeddings.joblib"
has_data = (qdrant_ok and qh.collection_info(qdrant_client).get("vector_count", 0) > 0) \
           or joblib_path.exists()

if not has_data:
    st.error("""
**No indexed data found.**

1. Go to **📤 Upload Center** → upload videos and process them, or
2. Run `python preprocess_json.py` in the terminal.
    """)
    st.stop()

if not is_up:
    st.warning(f"⚠️ {provider.capitalize()} is offline or missing API key. Responses will fail.")

# ── Chat history ──────────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image("assets/logo.png", width=120)
        st.markdown("### Welcome to MindMesh AI")
        st.caption("Ask anything about your courses.")
    st.markdown("<br><br>", unsafe_allow_html=True)

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "assets/logo.png"):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📚 {len(msg['sources'])} source chunk(s) · via {msg.get('retrieval_source','Qdrant')}", expanded=False):
                for hit in msg["sources"]:
                    ts_start = ret.fmt_ts(hit.get("start", 0))
                    ts_end   = ret.fmt_ts(hit.get("end",   0))
                    score    = hit.get("score", 0)
                    st.markdown(f"""
<div class="mm-source">
  <span class="mm-source-score">{score:.3f}</span>
  <strong>Video {hit.get('number','?')}: {hit.get('title','?')}</strong>
  <span class="mm-source-ts"> · {ts_start} – {ts_end}</span><br>
  <span style="color:rgba(255,255,255,0.55);font-size:0.82rem;line-height:1.5">{hit.get('text','')[:250]}…</span>
</div>
""", unsafe_allow_html=True)
        if msg.get("ts"):
            st.caption(f"⏱ {msg['ts']}")

# ── Chat input ────────────────────────────────────────────────────────────────
user_query = st.chat_input("Ask about your course…  e.g. 'Where is CSS Box Model taught?'")

if user_query:
    query = user_query.strip()

    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(query)
    st.session_state.chat_history.append({"role": "user", "content": query, "sources": [], "ts": ""})

    # Retrieve context
    with st.spinner("🔍 Searching course knowledge base…"):
        t0   = time.time()
        hits, ret_source = ret.retrieve(
            embed_model   = embed_model,
            query         = query,
            qdrant_client = qdrant_client,
            top_k         = st.session_state.top_k,
            score_threshold = st.session_state.score_threshold,
        )
        retrieve_time = time.time() - t0

    if not hits:
        answer = ("I couldn't find relevant content for that question. "
                  "Try rephrasing it, or make sure the course videos have been indexed.")
        with st.chat_message("assistant", avatar="assets/logo.png"):
            st.markdown(answer)
        st.session_state.chat_history.append({
            "role": "assistant", "content": answer,
            "sources": [], "retrieval_source": ret_source, "ts": ""
        })
    else:
        prompt = ret.build_rag_prompt(query, hits)
        ret.save_artifacts(prompt, "", _ROOT)

        # Stream response
        with st.chat_message("assistant", avatar="assets/logo.png"):
            t1 = time.time()
            full_response = st.write_stream(
                ret.stream_response(prompt, model_name=active_model, provider=provider)
            )
            llm_time = time.time() - t1
            total_time = time.time() - t0

        # Save artifacts
        ret.save_artifacts(prompt, full_response, _ROOT)

        # Update analytics
        st.session_state.query_count += 1
        st.session_state.response_times.append(round(total_time, 2))
        st.session_state.query_timestamps.append(datetime.now().isoformat())

        # Simple topic extraction (top words from query)
        stop = {"what","where","how","is","the","a","in","of","and","to","does","do","can","my","i","for"}
        for word in query.lower().split():
            if len(word) > 3 and word not in stop:
                st.session_state.popular_topics[word] = st.session_state.popular_topics.get(word, 0) + 1

        ts_label = f"Retrieve: {retrieve_time:.1f}s | LLM: {llm_time:.1f}s | Total: {total_time:.1f}s"

        st.session_state.chat_history.append({
            "role":             "assistant",
            "content":         full_response,
            "sources":         hits,
            "retrieval_source": ret_source,
            "ts":              ts_label,
        })
        st.rerun()

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("Chat Controls")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    st.caption(f"Messages: {len(st.session_state.chat_history)}")
    if st.session_state.response_times:
        avg_time = sum(st.session_state.response_times) / len(st.session_state.response_times)
        st.caption(f"Avg response: {avg_time:.1f}s")

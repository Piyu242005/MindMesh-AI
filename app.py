"""Streamlit web UI for the RAG Course Assistant."""

import streamlit as st
import logging
from config import Config
from utils import check_ollama_availability, inference, seconds_to_timestamp
from search import HybridSearchEngine
from prompts import build_query_prompt, build_summary_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG.app")

# ──────────────────────────── Page Config ────────────────────────────
st.set_page_config(
    page_title="RAG Course Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────── Session State ────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "engine" not in st.session_state:
    st.session_state.engine = None


# ──────────────────────────── Sidebar ────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    model = st.selectbox(
        "LLM Model",
        ["llama3.2", "llama3.1", "deepseek-r1", "mistral", "gemma2"],
        index=0,
    )
    top_k = st.slider("Number of results", 1, 15, Config.TOP_K_RESULTS)
    use_reranker = st.checkbox("Enable Reranking", value=True)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)

    st.divider()
    st.markdown("### 📊 System Status")

    # Check Ollama
    ollama_ok = check_ollama_availability()
    if ollama_ok:
        st.success("✅ Ollama is running")
    else:
        st.error("❌ Ollama is not running")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(
        "**RAG Course Assistant**  \n"
        "Ask questions about the  \n"
        "Sigma Web Development Course"
    )


# ──────────────────────────── Initialize Engine ────────────────────────────
@st.cache_resource
def load_engine(use_reranker: bool):
    """Load the search engine (cached across reruns)."""
    try:
        return HybridSearchEngine(use_reranker=use_reranker)
    except Exception as e:
        st.error(f"Failed to load search engine: {e}")
        return None


engine = load_engine(use_reranker)

# ──────────────────────────── Main UI ────────────────────────────
st.title("🎓 RAG Course Assistant")
st.caption("Ask anything about the Sigma Web Development Course — get answers with video timestamps!")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📎 Source Chunks"):
                for src in msg["sources"]:
                    start_ts = seconds_to_timestamp(src["start"])
                    end_ts = seconds_to_timestamp(src["end"])
                    st.markdown(
                        f"**Video {src['number']}: {src['title']}** "
                        f"({start_ts} - {end_ts})"
                    )
                    st.text(src["text"][:200] + "..." if len(src["text"]) > 200 else src["text"])
                    st.divider()

# Chat input
if prompt := st.chat_input("Ask a question about the course..."):
    if not engine:
        st.error("Search engine not loaded. Check that embeddings exist.")
    elif not ollama_ok:
        st.error("Ollama is not running. Please start it first.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching and generating response..."):
                # Build enhanced query with conversation context
                if len(st.session_state.messages) > 2:
                    last_exchange = st.session_state.messages[-3:-1]
                    context_str = " ".join(
                        m["content"][:100] for m in last_exchange
                    )
                    enhanced_query = f"Context: {context_str}. Question: {prompt}"
                else:
                    enhanced_query = prompt

                # Search
                results = engine.search(enhanced_query, top_k=top_k)

                if not results:
                    response = (
                        "I couldn't find relevant content for your question. "
                        "Try asking about HTML, CSS, or other web development topics covered in the course."
                    )
                    sources = []
                else:
                    # Build prompt and get response
                    llm_prompt = build_query_prompt(prompt, results)
                    response = inference(llm_prompt, model=model, temperature=temperature)
                    sources = results

                st.markdown(response)

                if sources:
                    with st.expander("📎 Source Chunks"):
                        for src in sources:
                            start_ts = seconds_to_timestamp(src["start"])
                            end_ts = seconds_to_timestamp(src["end"])
                            st.markdown(
                                f"**Video {src['number']}: {src['title']}** "
                                f"({start_ts} - {end_ts})"
                            )
                            st.text(
                                src["text"][:200] + "..."
                                if len(src["text"]) > 200
                                else src["text"]
                            )
                            st.divider()

        # Save assistant message
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "sources": sources if sources else []}
        )

# ──────────────────────────── Suggested Questions ────────────────────────────
if not st.session_state.messages:
    st.markdown("### 💡 Try asking:")
    cols = st.columns(3)
    suggestions = [
        "Where is HTML concluded in this course?",
        "How do I create forms in HTML?",
        "What is the CSS Box Model?",
        "How to add images in HTML?",
        "What are semantic tags?",
        "How does inline vs block elements work?",
    ]
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(suggestion, key=f"suggest_{i}"):
                st.session_state.messages.append(
                    {"role": "user", "content": suggestion}
                )
                st.rerun()

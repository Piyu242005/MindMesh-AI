import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.embeddings import get_embedding_model, get_qdrant_client
from backend.retrieval import retrieve, build_rag_prompt, stream_response

st.title("🤖 Ask MindMesh")
st.caption("Ask questions about the indexed course knowledge base.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("What would you like to learn?")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Searching your knowledge base..."):
            try:
                model = get_embedding_model()
                client, err = get_qdrant_client()
                result = retrieve(model, query, client, top_k=5)
                history = st.session_state.messages[-7:-1]
                prompt = build_rag_prompt(query, result, history)
                provider = "gemini"
                model_name = "gemini-2.5-flash"
                answer = st.write_stream(stream_response(prompt, model_name, provider=provider))
                st.session_state.messages.append({"role": "assistant", "content": answer})

                with st.expander("Sources & retrieval details"):
                    st.write(f"Knowledge: {result.get('label', 'Unknown')}")
                    st.write(f"Confidence: {result.get('confidence', 'Unknown')}")
                    for hit in result.get("course_hits", []):
                        st.markdown(f"**{hit.get('title', 'Course')}** · {hit.get('start', 0):.0f}s")
                        st.caption(hit.get("text", "")[:500])
            except Exception as exc:
                st.error(f"Unable to answer right now: {exc}")

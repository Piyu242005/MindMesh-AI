import streamlit as st

st.markdown("""
<div class="mm-page-header">
    <h1 style="margin-bottom:0;">📚 Getting Started</h1>
    <h3 style="margin-top:0; color:var(--text-2);">Your guide to mastering MindMesh AI</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

st.header("How MindMesh Works")
st.markdown("""
MindMesh AI is a powerful Retrieval-Augmented Generation (RAG) platform. It allows you to chat directly with your video courses!
Instead of manually searching through hours of video, you simply ask a question, and the AI finds the exact moment the topic was discussed.
""")

st.header("Supported File Types")
st.markdown("""
You can upload the following video formats:
* `.mp4`
* `.mkv`
* `.mov`
* `.avi`
""")

st.header("Processing Flow")
st.markdown("""
1. **Video Upload**: Your video is saved locally.
2. **Audio Extraction**: `FFmpeg` strips away the video data to save processing power and memory.
3. **Transcription**: `Faster-Whisper` transcribes the audio locally, generating high-accuracy text with timestamps.
4. **Chunking & Embedding**: The transcript is split into logical chunks and embedded into 384-dimensional vectors using `BAAI/bge-small-en-v1.5`.
5. **Vector Database**: These vectors are uploaded to **Qdrant Cloud** for lightning-fast retrieval.
""")

st.header("Example Prompts")
st.markdown("""
Try asking these types of questions in the **AI Chat**:

* *"What is web development?"*
* *"Explain Python lists like I'm 5."*
* *"Where did the instructor explain APIs?"*
* *"Summarize Lecture 5."*
* *"Show me the timestamp where CSS Flexbox was discussed."*
""")

st.header("FAQ")
with st.expander("Why does initial processing take a few minutes?"):
    st.write("MindMesh AI runs a highly optimized AI model locally on your machine to transcribe the audio. This process is intensive but ensures your data stays private and is accurately indexed with precise timestamps.")

with st.expander("Can I use different LLM providers?"):
    st.write("Yes! Head over to the **Settings** page. You can switch between Google Gemini, Groq, or even local Ollama models instantly.")

with st.expander("What if Qdrant Cloud is unreachable?"):
    st.write("MindMesh AI has a built-in failover. If Qdrant Cloud is unreachable, it will gracefully fall back to a local `embeddings.joblib` file and use in-memory cosine similarity search to ensure you can always query your courses.")

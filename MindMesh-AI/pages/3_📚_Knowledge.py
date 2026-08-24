from pathlib import Path
import json
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
JSON_DIR = ROOT / "jsons"

st.title("📚 Knowledge Library")
st.caption("Browse transcripts already processed by MindMesh AI.")

files = sorted(JSON_DIR.glob("*.json")) if JSON_DIR.exists() else []
if not files:
    st.info("No processed lessons yet. Upload a course first.")
    st.stop()

search = st.text_input("Search lessons", placeholder="HTML, CSS, forms...")
matched = [f for f in files if not search or search.lower() in f.name.lower()]

st.metric("Indexed lessons", len(matched))
for path in matched:
    with st.expander(path.stem):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            chunks = data.get("chunks", [])
            st.write(f"**Chunks:** {len(chunks)}")
            if chunks:
                st.markdown("**Transcript preview**")
                st.write(chunks[0].get("text", "")[:1200])
        except Exception as exc:
            st.error(f"Could not read file: {exc}")

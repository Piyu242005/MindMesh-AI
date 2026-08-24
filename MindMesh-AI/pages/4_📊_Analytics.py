from pathlib import Path
import json
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
json_dir = ROOT / "jsons"
video_dir = ROOT / "videos"
audio_dir = ROOT / "audios"

st.title("📊 Analytics")
st.caption("A simple view of your local MindMesh knowledge base.")

json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []
video_files = list(video_dir.iterdir()) if video_dir.exists() else []
audio_files = list(audio_dir.iterdir()) if audio_dir.exists() else []
chunks = 0
for path in json_files:
    try:
        chunks += len(json.loads(path.read_text(encoding="utf-8")).get("chunks", []))
    except Exception:
        pass

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lessons", len(json_files))
c2.metric("Knowledge chunks", chunks)
c3.metric("Videos", len(video_files))
c4.metric("Audio files", len(audio_files))

st.subheader("Knowledge growth")
if json_files:
    st.bar_chart({"Lessons": [len(json_files)], "Chunks": [chunks]})
else:
    st.info("Analytics will appear after your first processed lesson.")

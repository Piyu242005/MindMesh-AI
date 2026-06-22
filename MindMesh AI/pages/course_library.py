"""
pages/course_library.py — MindMesh AI
Browse all indexed courses with search, filter, sort, and per-course actions.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qdrant_helper as qh
from backend.embeddings import get_qdrant_client, get_embedding_model, build_points_from_json

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-page-header">
  <p class="mm-page-title">📚 Course Library</p>
  <p class="mm-page-subtitle">Browse, search, and manage indexed course content</p>
</div>
""", unsafe_allow_html=True)

# ── Load data from jsons/ ─────────────────────────────────────────────────────
jsons_dir  = _ROOT / "jsons"
json_files = sorted(jsons_dir.glob("*.json")) if jsons_dir.exists() else []

if not json_files:
    st.warning("No courses indexed yet. Go to **📤 Upload Center** to add videos.")
    st.stop()

courses = []
for jf in json_files:
    try:
        data   = json.loads(jf.read_text(encoding="utf-8"))
        chunks = data.get("chunks", [])
        if not chunks:
            continue

        # Extract metadata from first chunk
        first = chunks[0]
        courses.append({
            "filename":   jf.name,
            "path":       jf,
            "number":     first.get("number", "?"),
            "title":      first.get("title",  jf.stem),
            "chunks":     len(chunks),
            "duration":   max((c.get("end", 0) for c in chunks), default=0),
            "modified":   datetime.fromtimestamp(jf.stat().st_mtime),
            "size_kb":    jf.stat().st_size // 1024,
            "text_preview": (chunks[0].get("text","")[:120] + "…") if chunks else "",
        })
    except Exception:
        pass

# ── Top stats ─────────────────────────────────────────────────────────────────
total_chunks   = sum(c["chunks"]   for c in courses)
total_duration = sum(c["duration"] for c in courses)

sc1, sc2, sc3 = st.columns(3)
with sc1: st.metric("📚 Total Courses",     len(courses))
with sc2: st.metric("📄 Total Chunks",      f"{total_chunks:,}")
with sc3:
    hrs = int(total_duration // 3600)
    mins = int((total_duration % 3600) // 60)
    st.metric("⏱️ Total Duration", f"{hrs}h {mins}m" if hrs else f"{mins}m")

st.divider()

# ── Search + Filter + Sort bar ────────────────────────────────────────────────
sb1, sb2, sb3 = st.columns([3, 2, 2])
with sb1:
    search_query = st.text_input("🔍 Search courses", placeholder="CSS, JavaScript, React…", label_visibility="collapsed")
with sb2:
    sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Title A–Z", "Chunks ↓", "Chunks ↑"], label_visibility="collapsed")
with sb3:
    min_chunks = st.number_input("Min chunks", min_value=0, value=0, step=10, label_visibility="collapsed")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = courses

if search_query.strip():
    q = search_query.lower()
    filtered = [c for c in filtered if q in c["title"].lower() or q in c["filename"].lower()]

if min_chunks > 0:
    filtered = [c for c in filtered if c["chunks"] >= min_chunks]

# Sort
_sort_map = {
    "Date (newest)": (lambda c: c["modified"],   True),
    "Date (oldest)": (lambda c: c["modified"],   False),
    "Title A–Z":     (lambda c: c["title"].lower(), False),
    "Chunks ↓":      (lambda c: c["chunks"],     True),
    "Chunks ↑":      (lambda c: c["chunks"],     False),
}
_key, _rev = _sort_map[sort_by]
filtered.sort(key=_key, reverse=_rev)

st.caption(f"Showing {len(filtered)} of {len(courses)} courses")
st.divider()

# ── Course cards ──────────────────────────────────────────────────────────────
qdrant_client, _ = get_qdrant_client()

for course in filtered:
    # Duration format
    dur_m = int(course["duration"] // 60)
    dur_s = int(course["duration"] % 60)
    dur_str = f"{dur_m}:{dur_s:02d}"

    st.markdown(f"""
<div class="mm-course-card">
  <div class="mm-course-num">VIDEO {course['number']}</div>
  <div class="mm-course-title">{course['title']}</div>
  <div class="mm-course-meta">
    <span>📄 {course['chunks']} chunks</span>
    <span>⏱️ {dur_str}</span>
    <span>📁 {course['filename']}</span>
    <span>📅 {course['modified'].strftime('%b %d, %Y')}</span>
  </div>
  <div style="margin-top:10px;font-size:0.78rem;color:rgba(255,255,255,0.35);line-height:1.5;font-style:italic">
    {course['text_preview']}
  </div>
</div>
""", unsafe_allow_html=True)

    # Action buttons
    ba1, ba2, ba3, _ = st.columns([1, 1, 1, 4])
    with ba1:
        if st.button("👁️ View", key=f"view_{course['filename']}", use_container_width=True):
            st.session_state[f"expand_{course['filename']}"] = not st.session_state.get(f"expand_{course['filename']}", False)

    with ba2:
        reindex_key = f"reindex_{course['filename']}"
        if st.button("🔄 Reindex", key=reindex_key, use_container_width=True):
            if qdrant_client:
                with st.spinner(f"Reindexing {course['filename']}…"):
                    try:
                        model  = get_embedding_model()
                        points = build_points_from_json(course["path"], model)
                        qh.upload_points_batch(qdrant_client, points)
                        st.success(f"✅ {course['filename']} reindexed — {len(points)} vectors")
                        st.cache_resource.clear()
                    except Exception as e:
                        st.error(f"Reindex failed: {e}")
            else:
                st.error("Qdrant offline — cannot reindex")

    with ba3:
        del_key = f"del_{course['filename']}"
        if st.button("🗑️ Delete", key=del_key, use_container_width=True):
            st.session_state[f"confirm_del_{course['filename']}"] = True

    # Confirm delete
    if st.session_state.get(f"confirm_del_{course['filename']}", False):
        st.warning(f"Delete `{course['filename']}`? This cannot be undone.")
        cd1, cd2 = st.columns([1, 5])
        with cd1:
            if st.button("Yes, delete", key=f"confirmyes_{course['filename']}"):
                try:
                    course["path"].unlink()
                    st.session_state.pop(f"confirm_del_{course['filename']}", None)
                    st.success(f"Deleted `{course['filename']}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not delete: {e}")
        with cd2:
            if st.button("Cancel", key=f"confirmno_{course['filename']}"):
                st.session_state.pop(f"confirm_del_{course['filename']}", None)
                st.rerun()

    # Expandable chunk viewer
    if st.session_state.get(f"expand_{course['filename']}", False):
        with st.expander(f"📄 All chunks in {course['filename']}", expanded=True):
            try:
                data = json.loads(course["path"].read_text(encoding="utf-8"))
                for i, chunk in enumerate(data.get("chunks", [])[:50], 1):
                    m, s = divmod(int(chunk.get("start", 0)), 60)
                    st.markdown(f"""
<div class="mm-source">
  <span class="mm-source-score">#{i}</span>
  <span class="mm-source-ts">{m}:{s:02d} – </span>
  {chunk.get('text','')}
</div>
""", unsafe_allow_html=True)
                if len(data.get("chunks", [])) > 50:
                    st.caption(f"Showing first 50 of {len(data['chunks'])} chunks")
            except Exception as e:
                st.error(f"Could not load chunks: {e}")

    st.write("")  # spacing

"""
pages/analytics.py — MindMesh AI
Usage metrics, knowledge base stats, and Plotly visualisations.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

import streamlit as st

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qdrant_helper as qh
from backend.embeddings import get_qdrant_client

try:
    import plotly.graph_objects as go
    import plotly.express as px
    _PLOTLY = True
except ImportError:
    _PLOTLY = False

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-page-header">
  <p class="mm-page-title">📈 Analytics</p>
  <p class="mm-page-subtitle">Usage metrics · knowledge base stats · performance</p>
</div>
""", unsafe_allow_html=True)

if not _PLOTLY:
    st.warning("Install plotly for charts: `pip install plotly`")

# ── Load real data ────────────────────────────────────────────────────────────
qdrant_client, _ = get_qdrant_client()
qdrant_ok = qdrant_client is not None

jsons_dir  = _ROOT / "jsons"
json_files = list(jsons_dir.glob("*.json")) if jsons_dir.exists() else []

courses       = []
total_chunks  = 0
for jf in json_files:
    try:
        data   = json.loads(jf.read_text(encoding="utf-8"))
        chunks = data.get("chunks", [])
        first  = chunks[0] if chunks else {}
        courses.append({
            "title":    first.get("title",  jf.stem)[:40],
            "number":   first.get("number", "?"),
            "chunks":   len(chunks),
            "duration": max((c.get("end", 0) for c in chunks), default=0),
        })
        total_chunks += len(chunks)
    except Exception:
        pass

qdrant_info  = qh.collection_info(qdrant_client) if qdrant_ok else {}
vec_count    = qdrant_info.get("vector_count", 0)
query_count  = st.session_state.get("query_count", 0)
resp_times   = st.session_state.get("response_times", [])
avg_resp     = round(sum(resp_times) / len(resp_times), 2) if resp_times else 0.0
topics       = st.session_state.get("popular_topics", {})

# ── Top stats ─────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("💬 Total Questions",    query_count)
with m2: st.metric("⚡ Avg Response (s)",   f"{avg_resp:.1f}s" if avg_resp else "—")
with m3: st.metric("🗄️ Qdrant Vectors",    f"{vec_count:,}")
with m4: st.metric("📄 Total Chunks",       f"{total_chunks:,}")

st.divider()

# ── Charts row 1 ─────────────────────────────────────────────────────────────
if _PLOTLY:
    ch1, ch2 = st.columns([3, 2])

    # Chunks per video bar chart
    with ch1:
        st.subheader("📊 Chunks per Course")
        if courses:
            labels = [f"V{c['number']}: {c['title'][:25]}" for c in courses]
            values = [c["chunks"] for c in courses]

            fig = go.Figure(go.Bar(
                x=values, y=labels,
                orientation="h",
                marker=dict(
                    color=values,
                    colorscale=[[0, "#1C1C1C"], [0.5, "#FF4B4B"], [1, "#FF6363"]],
                    showscale=False,
                ),
                text=values,
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.6)", size=11),
            ))
            fig.update_layout(
                plot_bgcolor="#111111",
                paper_bgcolor="#111111",
                font=dict(color="rgba(255,255,255,0.7)", family="Inter"),
                xaxis=dict(showgrid=False, color="rgba(255,255,255,0.3)"),
                yaxis=dict(showgrid=False, color="rgba(255,255,255,0.6)"),
                margin=dict(l=0, r=30, t=10, b=10),
                height=max(300, len(courses) * 28),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No course data — upload videos first.")

    # Content distribution pie
    with ch2:
        st.subheader("🥧 Content Distribution")
        if courses:
            fig2 = go.Figure(go.Pie(
                labels=[c["title"][:20] for c in courses],
                values=[c["chunks"] for c in courses],
                hole=0.55,
                marker=dict(colors=px.colors.sequential.Reds[::-1][:len(courses)] or ["#FF4B4B"]),
                textinfo="percent",
                textfont=dict(size=11, color="white"),
            ))
            fig2.update_layout(
                plot_bgcolor="#111111",
                paper_bgcolor="#111111",
                font=dict(color="rgba(255,255,255,0.65)", family="Inter"),
                showlegend=True,
                legend=dict(font=dict(size=9, color="rgba(255,255,255,0.5)")),
                margin=dict(l=0, r=0, t=10, b=10),
                height=350,
                annotations=[dict(
                    text=f"{len(courses)}<br>courses",
                    x=0.5, y=0.5, font_size=14, showarrow=False,
                    font=dict(color="white"),
                )],
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No data yet.")

    st.divider()

    # Charts row 2
    ch3, ch4 = st.columns([2, 2])

    # Response time history
    with ch3:
        st.subheader("⚡ Response Times")
        if resp_times:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=list(range(1, len(resp_times) + 1)),
                y=resp_times,
                mode="lines+markers",
                line=dict(color="#FF4B4B", width=2),
                marker=dict(color="#FF4B4B", size=6),
                fill="tozeroy",
                fillcolor="rgba(255,75,75,0.08)",
            ))
            fig3.add_hline(
                y=avg_resp, line_dash="dot",
                line_color="rgba(255,255,255,0.3)",
                annotation_text=f"avg {avg_resp:.1f}s",
                annotation_font_color="rgba(255,255,255,0.4)",
            )
            fig3.update_layout(
                plot_bgcolor="#111111", paper_bgcolor="#111111",
                font=dict(color="rgba(255,255,255,0.6)", family="Inter"),
                xaxis=dict(title="Query #", showgrid=False, color="rgba(255,255,255,0.3)"),
                yaxis=dict(title="Seconds", showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="rgba(255,255,255,0.3)"),
                margin=dict(l=0, r=10, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No queries yet — start chatting to see response times.")

    # Popular topics
    with ch4:
        st.subheader("🔥 Popular Topics")
        if topics:
            top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:12]
            words, counts = zip(*top_topics)
            fig4 = go.Figure(go.Bar(
                x=list(counts),
                y=list(words),
                orientation="h",
                marker=dict(color="#FF4B4B", opacity=0.8),
                text=list(counts),
                textposition="outside",
                textfont=dict(color="rgba(255,255,255,0.5)", size=11),
            ))
            fig4.update_layout(
                plot_bgcolor="#111111", paper_bgcolor="#111111",
                font=dict(color="rgba(255,255,255,0.6)", family="Inter"),
                xaxis=dict(showgrid=False, color="rgba(255,255,255,0.3)"),
                yaxis=dict(showgrid=False, color="rgba(255,255,255,0.6)"),
                margin=dict(l=0, r=30, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No topics tracked yet — start chatting to see popular questions.")

# ── Knowledge base table ──────────────────────────────────────────────────────
st.divider()
st.subheader("📚 Knowledge Base Details")

if courses:
    import pandas as pd
    df = pd.DataFrame([
        {
            "Video #":  c["number"],
            "Title":    c["title"],
            "Chunks":   c["chunks"],
            "Duration": f"{int(c['duration']//60)}:{int(c['duration']%60):02d}",
        }
        for c in courses
    ])
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Chunks": st.column_config.ProgressColumn(
                "Chunks", min_value=0, max_value=max(c["chunks"] for c in courses)
            )
        },
    )
else:
    st.info("No course data found.")

# ── Qdrant details ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🌐 Qdrant Collection Stats")
if qdrant_ok and qdrant_info:
    qi1, qi2, qi3, qi4 = st.columns(4)
    with qi1: st.metric("Collection",  qh.QDRANT_COLLECTION)
    with qi2: st.metric("Status",      qdrant_info.get("status","?").title())
    with qi3: st.metric("Vector Size", str(qdrant_info.get("vector_size","384")) + "d")
    with qi4: st.metric("Distance",    qdrant_info.get("distance","Cosine"))
else:
    st.warning("Qdrant offline — connect to see collection stats.")

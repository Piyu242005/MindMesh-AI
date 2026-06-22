"""
backend/retrieval.py — MindMesh AI
Handles: Qdrant semantic search, RAG prompt construction,
         Ollama inference (sync + streaming), Phase 1 joblib fallback.
Wraps logic from process_incoming.py into callable functions.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional, Tuple

# Ensure root on sys.path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend import qdrant_helper as qh

OLLAMA_BASE = os.getenv("OLLAMA_URL", "http://localhost:11434")


# ── LLM availability (via LLM Manager) ────────────────────────────────────────

def is_ollama_running() -> bool:
    """Check if any LLM provider is available."""
    from backend.llm_manager import check_providers
    status = check_providers()
    # Return true if any provider is ready
    return any(s[0] for s in status.values())


def get_ollama_models() -> List[str]:
    """Legacy helper: returns available models for the local Ollama provider."""
    from backend.llm_manager import check_providers
    import requests
    status = check_providers()
    if status.get("ollama", (False,))[0]:
        try:
            r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
    return []

# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_from_qdrant(
    client,
    query_vector: List[float],
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """Semantic search via Qdrant. Returns list of hit dicts with score."""
    hits = qh.search(client, query_vector, top_k=top_k)
    if score_threshold > 0:
        hits = [h for h in hits if h.get("score", 0) >= score_threshold]
    return hits


def retrieve_from_joblib(
    query_vector: List[float],
    top_k: int = 5,
    joblib_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Phase 1 fallback: in-memory cosine similarity over embeddings.joblib.
    Returns (hits, success).
    """
    if joblib_path is None:
        joblib_path = _ROOT / "embeddings.joblib"

    if not joblib_path.exists():
        return [], False

    try:
        import numpy as np
        import joblib
        from sklearn.metrics.pairwise import cosine_similarity

        df   = joblib.load(str(joblib_path))
        sims = cosine_similarity(
            np.vstack(df["embedding"].values), [query_vector]
        ).flatten()
        top_idx = sims.argsort()[::-1][:top_k]

        hits = []
        for idx in top_idx:
            row = df.iloc[idx]
            hits.append({
                "number": str(row.get("number", "")),
                "title":  str(row.get("title",  "")),
                "start":  float(row.get("start", 0.0)),
                "end":    float(row.get("end",   0.0)),
                "text":   str(row.get("text",   "")),
                "score":  float(sims[idx]),
            })
        return hits, True
    except Exception:
        return [], False


import functools

@functools.lru_cache(maxsize=1)
def get_cross_encoder():
    from sentence_transformers import CrossEncoder
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rewrite_query(query: str) -> str:
    """Rewrite query for optimal semantic search."""
    prompt = f"""You are an educational search assistant.
Rewrite the following user query to be highly descriptive and optimized for a semantic vector search across a web development course transcript. 
Do not add introductory phrases. Just output the rewritten query.
Original Query: {query}"""
    
    provider = os.getenv("LLM_PROVIDER", "gemini")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if provider == "gemini" else os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    try:
        rewritten = generate_sync(prompt, model_name, provider=provider)
        return rewritten.strip()
    except Exception:
        return query

def is_current_event(query: str) -> bool:
    keywords = ["today", "latest", "recent", "news", "current", "2026", "2025", "now"]
    q_lower = query.lower()
    return any(k in q_lower for k in keywords)

def retrieve(
    embed_model,
    query: str,
    qdrant_client,
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> dict:
    """
    Primary retrieval: try Qdrant, fall back to joblib.
    Uses CrossEncoder reranking and Smart Web Search Mode.
    Returns: {"course_hits": [], "web_hits": [], "confidence": str, "label": str}
    """
    from backend.embeddings import embed_single
    from backend.web_search import search_web

    # Read Web Search Mode (smart, course, hybrid, web)
    mode = os.getenv("WEB_SEARCH_MODE", "smart").lower()
    
    course_hits = []
    web_hits = []
    confidence = "Low"
    label = "📚 Course Knowledge"
    
    # 1. Course Retrieval
    if mode in ["smart", "course", "hybrid"]:
        vec = embed_single(query, embed_model)
        initial_k = 20

        if qdrant_client is not None:
            try:
                course_hits = retrieve_from_qdrant(qdrant_client, vec, initial_k, score_threshold)
            except Exception:
                course_hits, _ = retrieve_from_joblib(vec, initial_k)
        else:
            course_hits, _ = retrieve_from_joblib(vec, initial_k)

        # Reranking using CrossEncoder
        if course_hits:
            try:
                cross_encoder = get_cross_encoder()
                pairs = [[query, h.get("text", "")] for h in course_hits]
                scores = cross_encoder.predict(pairs)
                
                for idx, score in enumerate(scores):
                    course_hits[idx]["cross_score"] = float(score)
                    
                course_hits = sorted(course_hits, key=lambda x: x["cross_score"], reverse=True)
                course_hits = course_hits[:top_k]
                
                avg_score = sum(h["cross_score"] for h in course_hits) / len(course_hits)
                # Adjusted empirical thresholds for Confidence
                if avg_score >= 0.80:
                    confidence = "High"
                elif avg_score >= 0.60:
                    confidence = "Medium"
                else:
                    confidence = "Low"
            except Exception:
                course_hits = course_hits[:top_k]
                confidence = "Medium"
        else:
            confidence = "Low"

    # 2. Smart Mode Routing
    force_web = is_current_event(query)
    
    do_web_search = False
    
    if mode == "web":
        do_web_search = True
        course_hits = []
        confidence = "High" # Native web knowledge
    elif mode == "hybrid":
        do_web_search = True
    elif mode == "smart":
        if force_web or confidence == "Low":
            do_web_search = True
            course_hits = [] # Discard low-confidence course hits to focus on web
        elif confidence == "Medium":
            do_web_search = True

    if do_web_search:
        web_hits = search_web(query)
    
    # 3. Knowledge Labeling
    if course_hits and not web_hits:
        label = "📚 Course Knowledge"
    elif web_hits and not course_hits:
        label = "🌐 Web Knowledge"
        if mode == "smart" and not course_hits:
            confidence = "High" # Because we've defaulted to DDG directly
    elif course_hits and web_hits:
        label = "🔀 Hybrid Knowledge"

    # Update analytics
    from backend.telegram.analytics import AnalyticsStore
    if "Course" in label:
        AnalyticsStore.add_course_search()
    elif "Web" in label:
        AnalyticsStore.add_web_search()
    elif "Hybrid" in label:
        AnalyticsStore.add_hybrid_search()

    return {
        "course_hits": course_hits,
        "web_hits": web_hits,
        "confidence": confidence,
        "label": label
    }

# ── Prompt builder ────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, result_dict: dict) -> str:
    """Build the new educational RAG prompt incorporating course and web hits."""
    course_hits = result_dict.get("course_hits", [])
    web_hits = result_dict.get("web_hits", [])
    label = result_dict.get("label", "")
    confidence = result_dict.get("confidence", "Medium")
    
    course_json = json.dumps(
        [
            {
                "title":  h.get("title",  ""),
                "number": h.get("number", ""),
                "start":  h.get("start",  0.0),
                "text":   h.get("text",   ""),
            }
            for h in course_hits
        ], indent=2
    ) if course_hits else "[]"
    
    web_json = json.dumps(
        [
            {
                "title": w.get("title", ""),
                "href": w.get("href", ""),
                "body": w.get("body", "")
            }
            for w in web_hits
        ], indent=2
    ) if web_hits else "[]"

    return f'''You are MindMesh AI, an educational AI assistant.

Your job is to answer the user's question using the provided context (Course Chunks and/or Web Search Results).

Rules:
1. Always start your response with the label provided: {label}
2. Explain concepts in simple, human language.
3. Provide a direct answer first.
4. If the label is "🔀 Hybrid Knowledge", seamlessly combine knowledge from both sources.
5. Key Points should be bulleted.
6. Only show sources after the answer.
7. Format Course Sources like: "📚 [Video Name] (Video [number])"
8. Format Web Sources like: "🌐 [Article Title](URL)"
9. Always output the exact Confidence score before Sources.
10. Format exactly as:

{label}

[Detailed explanation]

Key Points:
• Point 1
• Point 2

Confidence:
🟢 High / 🟡 Medium / 🔴 Low (Match exactly: {confidence})

Sources:
[List course and web sources here]

---------------------------------
Course Context:
{course_json}

Web Context:
{web_json}

User Question: "{query}"'''


# ── LLM inference (via LLM Manager) ──────────────────────────────────────────

def generate_sync(prompt: str, model_name: str, provider: str = "gemini") -> str:
    """Send prompt to LLM Manager, wait for full response. Returns string."""
    from backend.llm_manager import generate_response
    return generate_response(prompt, provider=provider, model_name=model_name, stream=False)


def stream_response(prompt: str, model_name: str, provider: str = "gemini") -> Generator[str, None, None]:
    """
    Generator that yields string tokens from the LLM Manager.
    Compatible with st.write_stream().
    """
    from backend.llm_manager import generate_response
    return generate_response(prompt, provider=provider, model_name=model_name, stream=True)



# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_ts(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def save_artifacts(prompt: str, response: str, root: Path) -> None:
    """Write prompt.txt and response.txt — matches existing CLI behaviour."""
    (root / "prompt.txt").write_text(prompt, encoding="utf-8")
    (root / "response.txt").write_text(response, encoding="utf-8")

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


def retrieve(
    embed_model,
    query: str,
    qdrant_client,
    top_k: int = 5,
    score_threshold: float = 0.0,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Primary retrieval: try Qdrant, fall back to joblib.
    Returns (hits, source_label).
    """
    from backend.embeddings import embed_single

    vec = embed_single(query, embed_model)

    if qdrant_client is not None:
        try:
            hits = retrieve_from_qdrant(qdrant_client, vec, top_k, score_threshold)
            return hits, "Qdrant Cloud"
        except Exception:
            pass

    hits, ok = retrieve_from_joblib(vec, top_k)
    return hits, ("Local (joblib)" if ok else "No data source")


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, hits: List[Dict[str, Any]]) -> str:
    """Build the RAG prompt — identical template to process_incoming.py."""
    chunks_json = json.dumps(
        [
            {
                "title":  h.get("title",  ""),
                "number": h.get("number", ""),
                "start":  h.get("start",  0.0),
                "end":    h.get("end",    0.0),
                "text":   h.get("text",   ""),
            }
            for h in hits
        ],
        indent=2,
    )
    return f'''I am teaching web development in my Sigma Web Development course. Here are video subtitle chunks containing video title, video number, start time in seconds, end time in seconds, the text at that time:

{chunks_json}
---------------------------------
"{query}"
User asked this question related to the video chunks, you have to answer in a human way (dont mention the above format, its just for you) where and how much content is taught in which video (in which video and at what timestamp) and guide the user to go to that particular video. If user asks unrelated question, tell him that you can only answer questions related to the course
'''


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

"""
process_incoming.py — MindMesh AI
Query pipeline: User question → Embedding → Qdrant search → LLM answer

PHASE 1 (current):
  Primary  : Qdrant Cloud semantic search
  Fallback : embeddings.joblib cosine similarity if Qdrant is unreachable

PHASE 3 (after verifying Qdrant):
  Remove the "Phase 1 fallback" block (marked clearly below)
  and remove pandas/sklearn/joblib from requirements.txt
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from backend import qdrant_helper as qh

# ── Phase 1 fallback — remove in Phase 3 ─────────────────────────────────────
import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

TOP_K = 5
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

if LLM_PROVIDER == "gemini":
    LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
elif LLM_PROVIDER == "groq":
    LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
else:
    LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


# ── Load embedding model (once) ───────────────────────────────────────────────
_model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def create_embedding(text: str) -> list:
    """Encode a single query string into a 384-dim float list."""
    return _model.encode(
        [text],
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()[0]


# ── Retrieval helpers ─────────────────────────────────────────────────────────

def retrieve_from_qdrant(client, query_vector: list) -> list:
    """
    Primary path: Qdrant Cloud semantic search.
    Returns list of hit dicts with text/title/number/start/end/score.
    """
    return qh.search(client, query_vector, top_k=TOP_K)


def retrieve_from_joblib(query_vector: list) -> list:
    """
    Phase 1 fallback: in-memory cosine similarity over embeddings.joblib.
    REMOVE THIS FUNCTION IN PHASE 3.
    """
    joblib_path = Path("embeddings.joblib")
    if not joblib_path.exists():
        return []

    df = joblib.load(str(joblib_path))
    all_vecs = np.vstack(df["embedding"].values)
    sims = cosine_similarity(all_vecs, [query_vector]).flatten()
    top_idx = sims.argsort()[::-1][:TOP_K]

    hits = []
    for idx in top_idx:
        row = df.iloc[idx]
        hits.append({
            "number": row.get("number", ""),
            "title":  row.get("title",  ""),
            "start":  row.get("start",  0.0),
            "end":    row.get("end",    0.0),
            "text":   row.get("text",   ""),
            "score":  float(sims[idx]),
        })
    return hits


# ── LLM inference ─────────────────────────────────────────────────────────────

def inference(prompt: str) -> dict:
    """Call LLM Manager. Returns the full JSON response dict structure for legacy compatibility."""
    from backend.llm_manager import generate_response
    
    text = generate_response(prompt, provider=LLM_PROVIDER, model_name=LLM_MODEL, stream=False)
    
    response = {"response": text}
    print(response)
    return response


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, hits: list) -> str:
    """
    Constructs the RAG prompt — identical template to the original script.
    Chunks are serialised as JSON for the LLM.
    """
    chunks_json = json.dumps(
        [
            {
                "title":  h["title"],
                "number": h["number"],
                "start":  h["start"],
                "end":    h["end"],
                "text":   h["text"],
            }
            for h in hits
        ],
        indent=2,
    )

    return f'''I am teaching web development in my Sigma web development course. Here are video subtitle chunks containing video title, video number, start time in seconds, end time in seconds, the text at that time:

{chunks_json}
---------------------------------
"{query}"
User asked this question related to the video chunks, you have to answer in a human way (dont mention the above format, its just for you) where and how much content is taught in which video (in which video and at what timestamp) and guide the user to go to that particular video. If user asks unrelated question, tell him that you can only answer questions related to the course
'''


# ── Connect to Qdrant (best-effort) ──────────────────────────────────────────
qdrant_client = None
try:
    qdrant_client = qh.get_client()
    print(f"[Qdrant] Connected to '{qh.QDRANT_COLLECTION}' [OK]")
except Exception as e:
    print(f"[Qdrant] Unavailable ({e}) — using joblib fallback.")


if __name__ == "__main__":
    # ── Main query loop ───────────────────────────────────────────────────────────
    incoming_query = input("\nAsk a Question: ")

    query_vector = create_embedding(incoming_query)

    # ── Retrieval: Qdrant primary, joblib fallback ────────────────────────────────
    if qdrant_client is not None:
        hits = retrieve_from_qdrant(qdrant_client, query_vector)
        retrieval_source = "Qdrant Cloud"
    else:
        hits = retrieve_from_joblib(query_vector)
        retrieval_source = "joblib (Phase 1 fallback)"

    print(f"[Retrieval] Source: {retrieval_source} | Chunks returned: {len(hits)}")

    if not hits:
        print("\n[WARN] No chunks retrieved. Is the collection populated? Run preprocess_json.py first.")
        exit(0)

    # ── Print top hit summary ──────────────────────────────────────────────────────
    print("\nTop results:")
    for i, h in enumerate(hits, 1):
        mins, secs = divmod(int(h["start"]), 60)
        print(f"  {i}. [Score {h['score']:.3f}] Video {h['number']}: {h['title']} @ {mins}:{secs:02d}")

    # ── Build and send prompt ──────────────────────────────────────────────────────
    prompt = build_rag_prompt(incoming_query, hits)

    with open("prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    response = inference(prompt)["response"]
    print(f"\n{response}")

    with open("response.txt", "w", encoding="utf-8") as f:
        f.write(response)
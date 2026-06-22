"""
backend/embeddings.py — MindMesh AI
Handles: SentenceTransformer model loading, embedding generation,
         JSON chunk processing, and Qdrant upload orchestration.
Wraps logic from preprocess_json.py into callable functions.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

import functools

# Ensure root on sys.path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend import qdrant_helper as qh

EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_BATCH_SIZE = 64


# ── Model (cached globally) ───────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def get_embedding_model():
    """Load and cache the SentenceTransformer model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL_NAME)


# ── Qdrant client (cached globally) ───────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def get_qdrant_client():
    """
    Returns (client, error_str). client is None if connection fails.
    Cached so the TCP connection is reused across all pages.
    """
    try:
        c = qh.get_client()
        qh.ensure_collection(c)
        return c, None
    except Exception as e:
        return None, str(e)


# ── Embedding functions ───────────────────────────────────────────────────────

def embed_texts(
    texts: List[str],
    model,
    batch_size: int = EMBED_BATCH_SIZE,
) -> List[List[float]]:
    """
    Encode a list of texts into 384-dim normalised vectors.
    Returns list of float lists.
    """
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return vecs.tolist()


def embed_single(text: str, model) -> List[float]:
    """Encode a single query string. Used in retrieval."""
    return model.encode(
        [text],
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()[0]


# ── JSON → Qdrant points ──────────────────────────────────────────────────────

def build_points_from_json(
    json_path: Path,
    model,
    chunk_id_start: int = 0,
    batch_size: int = EMBED_BATCH_SIZE,
) -> List[Dict[str, Any]]:
    """
    Parse one JSON file, encode all chunks, and return a list of point dicts.
    Each dict: {id, vector, payload}.
    """
    with open(json_path, encoding="utf-8") as f:
        content = json.load(f)

    chunks  = content.get("chunks", [])
    texts   = [c["text"] for c in chunks]
    vectors = embed_texts(texts, model, batch_size)

    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        chunk_id = chunk_id_start + i
        points.append({
            "id": chunk_id,
            "vector": vec,
            "payload": {
                "chunk_id":    chunk_id,
                "number":      chunk.get("number", ""),
                "title":       chunk.get("title",  ""),
                "start":       chunk.get("start",  0.0),
                "end":         chunk.get("end",    0.0),
                "text":        chunk["text"],
                "source_file": json_path.name,
            },
        })
    return points


def reindex_all(
    jsons_dir: Path,
    qdrant_client,
    model,
    batch_size: int = EMBED_BATCH_SIZE,
    on_file: Optional[Callable[[str, int, int], None]] = None,
    on_upload: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Embed and upload all JSON files in jsons_dir to Qdrant.

    Callbacks:
        on_file(filename, file_index, total_files)   — called per file
        on_upload(uploaded, total)                   — called per batch

    Returns summary dict.
    """
    json_files = sorted(jsons_dir.glob("*.json"))
    if not json_files:
        return {"files": 0, "chunks": 0, "uploaded": 0, "error": "No JSON files found"}

    all_points: List[Dict[str, Any]] = []
    chunk_id = 0

    for idx, jf in enumerate(json_files):
        if on_file:
            on_file(jf.name, idx, len(json_files))
        pts = build_points_from_json(jf, model, chunk_id_start=chunk_id, batch_size=batch_size)
        all_points.extend(pts)
        chunk_id += len(pts)

    # Upload to Qdrant in batches
    total_uploaded = qh.upload_points_batch(qdrant_client, all_points, on_progress=on_upload)

    return {
        "files":    len(json_files),
        "chunks":   len(all_points),
        "uploaded": total_uploaded,
        "error":    None,
    }


# ── Phase 1 joblib fallback ───────────────────────────────────────────────────

def save_joblib_fallback(all_points: List[Dict[str, Any]], output_path: Path) -> None:
    """Phase 1: persist embeddings as joblib for rollback safety."""
    try:
        import pandas as pd
        import joblib
        rows = []
        for p in all_points:
            r = dict(p["payload"])
            r["embedding"] = p["vector"]
            rows.append(r)
        df = pd.DataFrame.from_records(rows)
        joblib.dump(df, str(output_path))
    except ImportError:
        pass  # pandas/joblib not required in Phase 3

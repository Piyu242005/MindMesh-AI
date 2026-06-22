"""
qdrant_helper.py — MindMesh AI
Central Qdrant Cloud integration: connect, create collection, upload, search.
All other scripts import from here — never duplicate client logic.
"""

import os
from typing import List, Dict, Any, Tuple, Optional, Callable
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL        = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY    = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "mindmesh_courses")

# Must match BAAI/bge-small-en-v1.5 output dimension
VECTOR_SIZE = 384
# Points per upsert call — balances memory and network overhead
BATCH_SIZE = 100


# ── Connection ────────────────────────────────────────────────────────────────

def get_client():
    """
    Create and return a validated QdrantClient connected to Qdrant Cloud.
    Raises ValueError if env vars are missing.
    Raises QdrantException if the server is unreachable.
    """
    from qdrant_client import QdrantClient

    if not QDRANT_URL:
        raise ValueError(
            "QDRANT_URL is not set.\n"
            "Copy .env.example → .env and fill in your cluster URL."
        )
    if not QDRANT_API_KEY:
        raise ValueError(
            "QDRANT_API_KEY is not set.\n"
            "Copy .env.example → .env and fill in your API key."
        )

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)
    client.get_collections()   # validates the connection immediately
    return client


def health_check(client) -> Tuple[bool, str]:
    """
    Ping Qdrant. Returns (ok: bool, message: str).
    Safe to call on every startup.
    """
    try:
        client.get_collections()
        return True, f"Connected → {QDRANT_URL}"
    except Exception as e:
        return False, str(e)


# ── Collection management ─────────────────────────────────────────────────────

def ensure_collection(client) -> bool:
    """
    Create the collection if it does not already exist.
    Returns True if it was just created, False if it already existed.
    Configured for 384-dim cosine similarity (bge-small-en-v1.5).
    """
    from qdrant_client.models import Distance, VectorParams

    existing = {c.name for c in client.get_collections().collections}
    if QDRANT_COLLECTION in existing:
        return False  # already exists — no action needed

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    return True  # freshly created


def collection_info(client) -> Dict[str, Any]:
    """
    Return live collection stats: vector count, status, config.
    Returns an error-safe dict if the collection doesn't exist yet.
    """
    try:
        info = client.get_collection(QDRANT_COLLECTION)
        return {
            "collection_name": QDRANT_COLLECTION,
            "status":          str(info.status),
            "vector_count":    getattr(info, "points_count", getattr(info, "vectors_count", 0)),
            "segments_count":  getattr(info, "segments_count", 0),
            "vector_size":     VECTOR_SIZE,
            "distance":        "Cosine",
        }
    except Exception as e:
        return {
            "collection_name": QDRANT_COLLECTION,
            "status":          "error",
            "vector_count":    0,
            "segments_count":  0,
            "error":           str(e),
        }


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_points_batch(
    client,
    points: List[Dict[str, Any]],
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> int:
    """
    Batch-upsert points to Qdrant.

    Each point dict must have:
        id      : int           — unique point ID (chunk_id)
        vector  : list[float]   — 384-dim embedding
        payload : dict          — arbitrary metadata (text, title, start, end…)

    Calls on_progress(uploaded_so_far, total) after each batch.
    Returns total number of points uploaded.
    """
    from qdrant_client.models import PointStruct

    total = len(points)
    uploaded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        structs = [
            PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in batch
        ]
        client.upsert(collection_name=QDRANT_COLLECTION, points=structs, wait=True)
        uploaded += len(batch)
        if on_progress:
            on_progress(uploaded, total)

    return uploaded


# ── Search ────────────────────────────────────────────────────────────────────

def search(
    client,
    query_vector: List[float],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run semantic search against the Qdrant collection.

    Returns a list of hit dicts, each containing:
        All payload fields (text, title, number, start, end, source_file, …)
        score    : float  — cosine similarity score (0–1)
        point_id : int    — Qdrant point ID
    """
    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    hits = []
    for r in getattr(results, "points", results):
        hit = dict(r.payload)          # copy all metadata from payload
        hit["score"]    = round(r.score, 4)
        hit["point_id"] = r.id
        hits.append(hit)
    return hits

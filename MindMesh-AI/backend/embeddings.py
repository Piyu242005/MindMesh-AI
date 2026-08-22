"""Embedding generation and incremental Qdrant indexing for MindMesh AI."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import functools
from backend import qdrant_helper as qh

EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_BATCH_SIZE = 64

@functools.lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL_NAME)

@functools.lru_cache(maxsize=1)
def get_qdrant_client():
    try:
        c = qh.get_client()
        qh.ensure_collection(c)
        return c, None
    except Exception as e:
        return None, str(e)

def embed_texts(texts: List[str], model, batch_size: int = EMBED_BATCH_SIZE) -> List[List[float]]:
    if not texts:
        return []
    return model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True).tolist()

def embed_single(text: str, model) -> List[float]:
    return model.encode([text], show_progress_bar=False, normalize_embeddings=True).tolist()[0]

def build_points_from_json(json_path: Path, model, chunk_id_start: int = 0, batch_size: int = EMBED_BATCH_SIZE) -> List[Dict[str, Any]]:
    with open(json_path, encoding="utf-8") as f:
        content = json.load(f)
    chunks = content.get("chunks", [])
    texts = [c.get("text", "") for c in chunks if c.get("text")]
    vectors = embed_texts(texts, model, batch_size)
    points = []
    for i, (chunk, vec) in enumerate(zip([c for c in chunks if c.get("text")], vectors)):
        chunk_id = chunk_id_start + i
        points.append({"id": chunk_id, "vector": vec, "payload": {"chunk_id": chunk_id, "number": chunk.get("number", ""), "title": chunk.get("title", ""), "start": chunk.get("start", 0.0), "end": chunk.get("end", 0.0), "text": chunk["text"], "source_file": json_path.name}})
    return points

def index_json_file(json_path: Path, qdrant_client, model, chunk_id_start: int = 0, batch_size: int = EMBED_BATCH_SIZE) -> Dict[str, Any]:
    """Index only one newly-created JSON file instead of rebuilding the whole corpus."""
    points = build_points_from_json(json_path, model, chunk_id_start, batch_size)
    uploaded = qh.upload_points_batch(qdrant_client, points)
    return {"file": json_path.name, "chunks": len(points), "uploaded": uploaded, "error": None}

def reindex_all(jsons_dir: Path, qdrant_client, model, batch_size: int = EMBED_BATCH_SIZE, on_file: Optional[Callable[[str, int, int], None]] = None, on_upload: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
    """Full rebuild retained for explicit maintenance/recovery operations."""
    json_files = sorted(jsons_dir.glob("*.json"))
    if not json_files:
        return {"files": 0, "chunks": 0, "uploaded": 0, "error": "No JSON files found"}
    all_points = []
    chunk_id = 0
    for idx, jf in enumerate(json_files):
        if on_file:
            on_file(jf.name, idx, len(json_files))
        pts = build_points_from_json(jf, model, chunk_id, batch_size)
        all_points.extend(pts)
        chunk_id += len(pts)
    total_uploaded = qh.upload_points_batch(qdrant_client, all_points, on_progress=on_upload)
    return {"files": len(json_files), "chunks": len(all_points), "uploaded": total_uploaded, "error": None}

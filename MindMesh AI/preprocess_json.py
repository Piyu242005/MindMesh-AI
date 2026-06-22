"""
preprocess_json.py — MindMesh AI
Ingestion pipeline: JSON chunks → Embeddings → Qdrant Cloud

PHASE 1 (current):
  Primary  : Upload all vectors to Qdrant Cloud
  Fallback : Also write embeddings.joblib for rollback safety

PHASE 3 (after verifying Qdrant):
  Remove the "Phase 1 fallback" block (marked clearly below)
  and remove pandas/joblib imports from requirements.txt
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import qdrant_helper as qh

# ── Phase 1 fallback — remove in Phase 3 ─────────────────────────────────────
import pandas as pd
import joblib
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

EMBED_BATCH_SIZE = 64    # texts per encode() call
JSON_DIR         = Path("jsons")


# ── Load embedding model ──────────────────────────────────────────────────────
print("=" * 55)
print("  MindMesh AI — Preprocessing Pipeline")
print("=" * 55)
print("\n[1/4] Loading embedding model (BAAI/bge-small-en-v1.5)…")
_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
print("      Model loaded ✓")


# ── Connect to Qdrant ─────────────────────────────────────────────────────────
print("\n[2/4] Connecting to Qdrant Cloud…")
qdrant_client = None
try:
    qdrant_client = qh.get_client()
    created = qh.ensure_collection(qdrant_client)
    if created:
        print(f"      Collection '{qh.QDRANT_COLLECTION}' created ✓")
    else:
        print(f"      Collection '{qh.QDRANT_COLLECTION}' already exists ✓")
except Exception as e:
    print(f"      [WARN] Qdrant unavailable: {e}")
    print("      Continuing in joblib-only mode (Phase 1 fallback).")


# ── Parse all JSON files into flat chunk list ─────────────────────────────────
print(f"\n[3/4] Reading chunks from '{JSON_DIR}/'…")

json_files = sorted(JSON_DIR.glob("*.json"))
if not json_files:
    raise FileNotFoundError(f"No JSON files found in '{JSON_DIR}/'. Run mp3_to_json.py first.")

all_texts: list[str]             = []
all_metas: list[dict]            = []
chunk_id  : int                  = 0

for json_file in json_files:
    with open(json_file, encoding="utf-8") as f:
        content = json.load(f)

    for chunk in content["chunks"]:
        all_texts.append(chunk["text"])
        all_metas.append({
            "chunk_id":    chunk_id,
            "number":      chunk.get("number", ""),
            "title":       chunk.get("title", ""),
            "start":       chunk.get("start", 0.0),
            "end":         chunk.get("end", 0.0),
            "text":        chunk["text"],
            "source_file": json_file.name,
        })
        chunk_id += 1

print(f"      {len(all_texts)} chunks across {len(json_files)} files ✓")


# ── Generate embeddings in batches ────────────────────────────────────────────
print(f"\n[4/4] Generating embeddings (batch_size={EMBED_BATCH_SIZE})…")
raw_embeddings = _model.encode(
    all_texts,
    batch_size=EMBED_BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True,   # ensures cosine sim = dot product
)
embeddings: list[list[float]] = raw_embeddings.tolist()
print(f"      {len(embeddings)} embeddings generated (dim={len(embeddings[0])}) ✓")


# ── Upload to Qdrant ──────────────────────────────────────────────────────────
if qdrant_client is not None:
    print(f"\n[Qdrant] Uploading {len(embeddings)} vectors…")

    points = [
        {
            "id":      meta["chunk_id"],
            "vector":  emb,
            "payload": meta,
        }
        for meta, emb in zip(all_metas, embeddings)
    ]

    def _progress(done: int, total: int) -> None:
        pct = int(done / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"  [{bar}] {done}/{total} ({pct}%)", end="\r", flush=True)

    total_uploaded = qh.upload_points_batch(qdrant_client, points, on_progress=_progress)
    print(f"\n  ✓ {total_uploaded} vectors uploaded to '{qh.QDRANT_COLLECTION}'")
else:
    print("\n[Qdrant] Skipped — client unavailable.")


# ── Phase 1 fallback: write embeddings.joblib ─────────────────────────────────
# REMOVE THIS ENTIRE BLOCK IN PHASE 3 (after Qdrant is verified)
print("\n[Fallback] Writing embeddings.joblib for rollback safety…")
records = []
for meta, emb in zip(all_metas, embeddings):
    row = dict(meta)
    row["embedding"] = emb
    records.append(row)

df = pd.DataFrame.from_records(records)
joblib.dump(df, "embeddings.joblib")
print(f"  ✓ embeddings.joblib saved ({len(df)} rows)")
# ── End Phase 1 fallback ──────────────────────────────────────────────────────


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Preprocessing Complete")
print("=" * 55)
print(f"  Chunks indexed   : {len(all_texts)}")
print(f"  Files processed  : {len(json_files)}")
print(f"  Qdrant upload    : {'✓ done' if qdrant_client else '✗ skipped (offline)'}")
print(f"  Joblib fallback  : ✓ saved")
print("=" * 55)

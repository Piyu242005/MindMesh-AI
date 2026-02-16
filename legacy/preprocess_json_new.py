"""Stage 3: Generate embeddings, store in ChromaDB, and build BM25 index."""

import json
import os
import sys
import argparse
import logging
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from config import Config
from utils import create_embedding, check_ollama_availability, logger
from chunking import process_all_jsons

try:
    import chromadb
    HAS_CHROMADB = True
except (ImportError, Exception) as e:
    HAS_CHROMADB = False
    logger.warning("chromadb not available (%s). Falling back to joblib storage.", type(e).__name__)

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    logger.warning("rank_bm25 not installed. BM25 hybrid search disabled.")


def build_embeddings_joblib(
    chunks: List[Dict[str, Any]], output_file: str
) -> pd.DataFrame:
    """Build embeddings and save to joblib (legacy/fallback mode)."""
    logger.info("Creating embeddings for %d chunks...", len(chunks))

    texts = [c["text"] for c in chunks]
    embeddings = create_embedding(texts)

    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = i
        chunk["embedding"] = embeddings[i]

    df = pd.DataFrame.from_records(chunks)
    joblib.dump(df, output_file)
    logger.info("Saved embeddings to '%s' (%d chunks)", output_file, len(df))
    return df


def build_chromadb(chunks: List[Dict[str, Any]], db_dir: str) -> None:
    """Build ChromaDB vector store from chunks."""
    client = chromadb.PersistentClient(path=db_dir)

    # Delete existing collection if it exists
    try:
        client.delete_collection("course_chunks")
    except Exception:
        pass

    collection = client.create_collection(
        name="course_chunks",
        metadata={"hnsw:space": "cosine"},
    )

    logger.info("Creating embeddings for %d chunks...", len(chunks))
    texts = [c["text"] for c in chunks]
    embeddings = create_embedding(texts)

    # Prepare data for ChromaDB
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "title": c["title"],
            "number": str(c["number"]),
            "start": float(c["start"]),
            "end": float(c["end"]),
            "segment_count": int(c.get("segment_count", 1)),
        }
        for c in chunks
    ]

    # Add in batches (ChromaDB batch limit)
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )
        logger.info("Added batch %d-%d to ChromaDB", i, end)

    logger.info("ChromaDB collection created with %d chunks at '%s'", len(chunks), db_dir)


def build_bm25_index(chunks: List[Dict[str, Any]], output_file: str = "bm25_index.joblib") -> None:
    """Build and save a BM25 index for keyword-based hybrid search."""
    tokenized = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)

    # Save BM25 index and chunk metadata together
    bm25_data = {
        "bm25": bm25,
        "chunks": chunks,
        "tokenized": tokenized,
    }
    joblib.dump(bm25_data, output_file)
    logger.info("BM25 index saved to '%s'", output_file)


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings from transcriptions.")
    parser.add_argument(
        "--jsons-dir", default=Config.JSONS_DIR, help="Directory with JSON transcriptions"
    )
    parser.add_argument(
        "--use-chromadb", action="store_true", default=HAS_CHROMADB,
        help="Use ChromaDB for vector storage (default if installed)"
    )
    parser.add_argument(
        "--use-sliding-window", action="store_true", default=True,
        help="Use sliding window chunking (default: True)"
    )
    parser.add_argument(
        "--window", type=int, default=Config.CHUNK_WINDOW_SECONDS,
        help="Sliding window size in seconds"
    )
    parser.add_argument(
        "--overlap", type=int, default=Config.CHUNK_OVERLAP_SECONDS,
        help="Overlap between windows in seconds"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not check_ollama_availability():
        sys.exit(1)

    # Step 1: Load and chunk transcriptions
    if args.use_sliding_window:
        chunks = process_all_jsons(args.jsons_dir, args.window, args.overlap)
    else:
        # Legacy: use raw Whisper segments
        chunks = []
        for jf in sorted(os.listdir(args.jsons_dir)):
            if not jf.endswith(".json"):
                continue
            with open(os.path.join(args.jsons_dir, jf), "r", encoding="utf-8") as f:
                content = json.load(f)
            chunks.extend(content.get("chunks", []))

    if not chunks:
        logger.error("No chunks found. Ensure JSON files exist in '%s'.", args.jsons_dir)
        sys.exit(1)

    logger.info("Total chunks to process: %d", len(chunks))

    # Step 2: Build vector store
    if args.use_chromadb and HAS_CHROMADB:
        build_chromadb(chunks, Config.CHROMA_DB_DIR)
    else:
        build_embeddings_joblib(chunks, Config.EMBEDDINGS_FILE)

    # Step 3: Build BM25 index for hybrid search
    if HAS_BM25:
        build_bm25_index(chunks, "bm25_index.joblib")

    # Always save joblib as fallback
    if args.use_chromadb and HAS_CHROMADB:
        build_embeddings_joblib(chunks, Config.EMBEDDINGS_FILE)

    logger.info("Preprocessing complete!")


if __name__ == "__main__":
    main()

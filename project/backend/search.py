"""Hybrid search (semantic + BM25) with optional cross-encoder reranking."""

import logging
import numpy as np
import joblib
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from utils import create_embedding
import uuid

logger = logging.getLogger("RAG.search")

try:
    import chromadb
    HAS_CHROMADB = True
except (ImportError, Exception) as e:
    HAS_CHROMADB = False
    logger.warning("chromadb not available (%s). Using joblib fallback.", type(e).__name__)

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

try:
    from sentence_transformers import CrossEncoder
    HAS_RERANKER = True
except ImportError:
    HAS_RERANKER = False
    logger.info("sentence-transformers not installed. Reranking disabled.")


class HybridSearchEngine:
    """
    Hybrid search combining:
    1. Semantic search (cosine similarity on embeddings)
    2. BM25 keyword search
    3. Reciprocal Rank Fusion (RRF) to merge results
    4. Optional cross-encoder reranking
    """

    def __init__(
        self,
        use_chromadb: bool = True,
        use_reranker: bool = True,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.df = None
        self.chroma_collection = None
        self.bm25_data = None
        self.reranker = None

        # Load vector store
        if use_chromadb and HAS_CHROMADB and _chromadb_exists():
            self._load_chromadb()
        else:
            self._load_joblib()

        # Load BM25 index
        if HAS_BM25:
            self._load_bm25()

        # Load reranker
        if use_reranker and HAS_RERANKER:
            try:
                logger.info("Loading reranker model '%s'...", reranker_model)
                self.reranker = CrossEncoder(reranker_model)
                logger.info("Reranker loaded successfully.")
            except Exception as e:
                logger.warning("Failed to load reranker: %s", e)

    def _load_chromadb(self):
        """Load ChromaDB collection."""
        client = chromadb.PersistentClient(path=Config.CHROMA_DB_DIR)
        self.chroma_collection = client.get_collection("course_chunks")
        logger.info(
            "Loaded ChromaDB collection with %d chunks",
            self.chroma_collection.count(),
        )

    def _load_joblib(self):
        """Load embeddings from joblib file."""
        try:
            self.df = joblib.load(Config.EMBEDDINGS_FILE)
            logger.info("Loaded joblib embeddings: %d chunks", len(self.df))
        except FileNotFoundError:
            logger.error("No embeddings found. Run preprocess_json.py first.")
            raise

    def _load_bm25(self):
        """Load BM25 index."""
        try:
            self.bm25_data = joblib.load("bm25_index.joblib")
            logger.info("Loaded BM25 index with %d chunks", len(self.bm25_data["chunks"]))
        except FileNotFoundError:
            logger.info("No BM25 index found. Keyword search disabled.")

    def semantic_search(
        self, query: str, top_k: int = 20
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve top-k results using semantic (embedding) search."""
        query_embedding = create_embedding([query])[0]

        if self.chroma_collection is not None:
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            items = []
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                score = 1 - results["distances"][0][i]  # ChromaDB returns distance
                items.append(
                    (
                        {
                            "title": meta["title"],
                            "number": meta["number"],
                            "start": meta["start"],
                            "end": meta["end"],
                            "text": results["documents"][0][i],
                        },
                        score,
                    )
                )
            return items

        else:
            # Fallback to joblib + sklearn
            similarities = cosine_similarity(
                np.vstack(self.df["embedding"].values), [query_embedding]
            ).flatten()

            top_indices = similarities.argsort()[::-1][:top_k]
            items = []
            for idx in top_indices:
                row = self.df.iloc[idx]
                items.append(
                    (
                        {
                            "title": row["title"],
                            "number": row["number"],
                            "start": row["start"],
                            "end": row["end"],
                            "text": row["text"],
                        },
                        float(similarities[idx]),
                    )
                )
            return items

    def bm25_search(
        self, query: str, top_k: int = 20
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve top-k results using BM25 keyword search."""
        if self.bm25_data is None:
            return []

        bm25 = self.bm25_data["bm25"]
        chunks = self.bm25_data["chunks"]
        tokenized_query = query.lower().split()

        scores = bm25.get_scores(tokenized_query)
        top_indices = scores.argsort()[::-1][:top_k]

        items = []
        for idx in top_indices:
            if scores[idx] > 0:
                items.append((chunks[idx], float(scores[idx])))
        return items

    def reciprocal_rank_fusion(
        self,
        result_lists: List[List[Tuple[Dict[str, Any], float]]],
        k: int = 60,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Merge multiple ranked result lists using Reciprocal Rank Fusion.
        Higher k = more weight to lower-ranked results.
        """
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        for result_list in result_lists:
            for rank, (chunk, _score) in enumerate(result_list):
                # Create a unique key for each chunk
                key = f"{chunk['number']}_{chunk['start']}_{chunk['end']}"
                if key not in chunk_map:
                    chunk_map[key] = chunk
                    scores[key] = 0
                scores[key] += 1.0 / (k + rank + 1)

        # Sort by fused score
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [(chunk_map[key], scores[key]) for key in sorted_keys]

    def rerank(
        self,
        query: str,
        results: List[Tuple[Dict[str, Any], float]],
        top_k: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Rerank results using a cross-encoder model."""
        if self.reranker is None or not results:
            return results[:top_k]

        pairs = [(query, r[0]["text"]) for r in results]
        scores = self.reranker.predict(pairs)

        # Sort by reranker score
        reranked = sorted(
            zip(results, scores), key=lambda x: x[1], reverse=True
        )
        return [(r[0], float(s)) for r, s in reranked[:top_k]]

    def search(
        self,
        query: str,
        top_k: int = None,
        similarity_threshold: float = None,
    ) -> List[Dict[str, Any]]:
        """
        Full hybrid search pipeline:
        1. Semantic search (top-N candidates)
        2. BM25 keyword search (top-N candidates)
        3. Reciprocal Rank Fusion
        4. Cross-encoder reranking
        5. Filter by similarity threshold
        """
        top_k = top_k or Config.TOP_K_RESULTS
        similarity_threshold = similarity_threshold or Config.SIMILARITY_THRESHOLD
        candidate_k = Config.RERANK_TOP_N

        # Step 1 & 2: Get candidates from both search methods
        semantic_results = self.semantic_search(query, top_k=candidate_k)
        bm25_results = self.bm25_search(query, top_k=candidate_k)

        # Step 3: Fuse results
        if bm25_results:
            fused = self.reciprocal_rank_fusion([semantic_results, bm25_results])
            logger.info(
                "Hybrid search: %d semantic + %d BM25 -> %d fused",
                len(semantic_results),
                len(bm25_results),
                len(fused),
            )
        else:
            fused = semantic_results
            logger.info("Semantic-only search: %d results", len(fused))

        # Step 4: Rerank
        final = self.rerank(query, fused, top_k=top_k)

        # Step 5: Filter by threshold
        filtered = [
            chunk
            for chunk, score in final
            if score >= similarity_threshold or self.reranker is not None
        ]

        # If reranker filtered everything, keep top results anyway
        if not filtered and final:
            filtered = [chunk for chunk, _ in final[:top_k]]

        logger.info("Returning %d results for query: '%s'", len(filtered), query[:50])
        return filtered

        return filtered


    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add new documents to the vector store and BM25 index."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = create_embedding(texts)
        
        # Add to ChromaDB
        if self.chroma_collection:
            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [
                {
                    "title": c.get("title", "Uploaded Doc"),
                    "number": i,
                    "start": 0.0,
                    "end": 0.0
                } for i, c in enumerate(chunks)
            ]
            self.chroma_collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks to ChromaDB")
            
        # Add to BM25 (Rebuild index - inefficient but functional for small updates)
        # Note: If BM25 is loaded from disk, we might need to append to the existing corpus
        # Ideally, we should persist this change. For now, in-memory update.
        if self.bm25_data:
            current_chunks = self.bm25_data["chunks"]
            current_chunks.extend(chunks)
            
            # Rebuild BM25
            tokenized_corpus = [doc["text"].lower().split() for doc in current_chunks]
            self.bm25_data["bm25"] = BM25Okapi(tokenized_corpus)
            self.bm25_data["chunks"] = current_chunks
            
            # Save updating index
            # joblib.dump(self.bm25_data, "bm25_index.joblib") # Uncomment to persist
            logger.info(f"Updated BM25 index with {len(chunks)} new chunks")


def _chromadb_exists() -> bool:
    """Check if ChromaDB directory exists."""
    import os
    return os.path.exists(Config.CHROMA_DB_DIR)

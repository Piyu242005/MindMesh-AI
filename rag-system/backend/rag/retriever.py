from typing import List, Dict, Any
from .vectorstore import vector_store
from config import settings
import logging

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        # Initialize reranker if configured
        try:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Loaded CrossEncoder for reranking")
        except:
            self.reranker = None
            logger.warning("CrossEncoder not loaded (optional).")

    def retrieve(self, query: str, top_k: int = settings.TOP_K) -> List[Dict[str, Any]]:
        """Retrieve documents using vector search."""
        # TODO: Implement BM25 for hybrid search if needed. For now, pure vector + rerank.
        
        # 1. Get candidate chunks
        initial_k = settings.RERANK_TOP_N if self.reranker else top_k
        results = vector_store.similarity_search(query, k=initial_k)
        
        if not results:
            return []

        # 2. Rerank
        if self.reranker:
            pairs = [(query, r["text"]) for r in results]
            scores = self.reranker.predict(pairs)
            
            # Combine result with new score
            for i, res in enumerate(results):
                res["rerank_score"] = float(scores[i])
            
            # Sort by rerank score
            results.sort(key=lambda x: x["rerank_score"], reverse=True)
            results = results[:top_k]
            
        return results

retriever = Retriever()

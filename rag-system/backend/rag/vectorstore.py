import numpy as np
import json
import os
import uuid
from typing import List, Dict, Any
import logging
from config import settings
from .embeddings import get_embeddings_model

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedding_model = get_embeddings_model()
        self.persist_path = os.path.join(settings.CHROMA_DB_DIR, "simple_vectors.json")
        self.documents = []
        self.embeddings = []
        self._load()

    def _load(self):
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, "r") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    # Convert list back to numpy array if exists
                    if data.get("embeddings"):
                        self.embeddings = np.array(data["embeddings"], dtype=np.float32)
                    else:
                        self.embeddings = np.empty((0, 0))
                logger.info(f"Loaded {len(self.documents)} documents from simple vector store.")
            except Exception as e:
                logger.error(f"Error loading vector store: {e}")
                self.documents = []
                self.embeddings = []
        else:
            self.documents = []
            self.embeddings = []

    def _save(self):
        try:
            data = {
                "documents": self.documents,
                "embeddings": self.embeddings.tolist() if len(self.embeddings) > 0 else []
            }
            with open(self.persist_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]):
        """Add documents to the vector store."""
        if not texts:
            return
            
        new_embeddings = self.embedding_model.embed_documents(texts)
        new_embeddings_np = np.array(new_embeddings, dtype=np.float32)
        
        # Add to local storage
        start_idx = len(self.documents)
        for i, text in enumerate(texts):
            doc = {
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": metadatas[i]
            }
            self.documents.append(doc)
            
        if len(self.embeddings) == 0:
            self.embeddings = new_embeddings_np
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings_np])
            
        self._save()
        logger.info(f"Added {len(texts)} documents to vector store.")

    def similarity_search(self, query: str, k: int = settings.TOP_K) -> List[Dict[str, Any]]:
        """Search for similar documents using cosine similarity."""
        if len(self.embeddings) == 0:
            return []

        query_embedding = self.embedding_model.embed_query(query)
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        # Calculate cosine similarity: (A . B) / (|A| * |B|)
        # Assuming embeddings are normalized? If not, we should normalize.
        # Sentence transformers usually return normalized embeddings.
        
        scores = np.dot(self.embeddings, query_vec)
        # Normalize if needed (skipped for speed if model is normalized)
        
        # Get top K indices
        top_k_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for idx in top_k_indices:
            doc = self.documents[idx]
            # Copy to avoid mutation
            res = doc.copy()
            res["score"] = float(scores[idx])
            results.append(res)
            
        return results

    def delete_collection(self):
        self.documents = []
        self.embeddings = []
        if os.path.exists(self.persist_path):
            os.remove(self.persist_path)
        
# Singleton instance
vector_store = VectorStore()

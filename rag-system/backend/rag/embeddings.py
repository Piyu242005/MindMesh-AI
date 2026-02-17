from abc import ABC, abstractmethod
from typing import List
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

class BaseEmbeddings(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

class OllamaEmbeddings(BaseEmbeddings):
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, base_url: str = settings.OLLAMA_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        logger.info(f"Initialized OllamaEmbeddings with model: {model_name}")

    def _get_embedding(self, text: str) -> List[float]:
        try:
            response = httpx.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Error getting embedding from Ollama: {e}")
            return []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embeddings.append(self._get_embedding(text))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._get_embedding(text)

def get_embeddings_model():
    """Factory to get the configured embedding model."""
    # Return Ollama embeddings to avoid Torch/Python 3.14 issues
    return OllamaEmbeddings()

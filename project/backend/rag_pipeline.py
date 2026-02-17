import logging
import asyncio
from typing import List, Dict, Any, AsyncGenerator

from .search import HybridSearchEngine
from .utils import async_inference_stream
from .prompts import build_query_prompt
from .config import Config

logger = logging.getLogger("RAG.pipeline")

class RAGPipeline:
    _instance = None
    _engine = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            logger.info("Initializing HybridSearchEngine...")
            cls._engine = HybridSearchEngine(use_reranker=True)
        return cls._engine

    @staticmethod
    def search(query: str, top_k: int = Config.TOP_K_RESULTS) -> List[Dict[str, Any]]:
        engine = RAGPipeline.get_engine()
        return engine.search(query, top_k=top_k)

    @staticmethod
    def add_documents(chunks: List[Dict[str, Any]]):
        engine = RAGPipeline.get_engine()
        engine.add_documents(chunks)


    @staticmethod
    async def chat_stream(
        query: str, 
        model: str = Config.LLM_MODEL, 
        use_reranker: bool = True
    ) -> AsyncGenerator[str, None]:
        
        # 1. Search
        # Note: HybridSearchEngine is synchronous (uses pandas/joblib).
        # We run it in a thread to not block the async event loop if it takes time.
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, RAGPipeline.search, query)
        
        # 2. Build Prompt (pass results list directly)
        prompt = build_query_prompt(query, results)
        
        # 3. Prepare sources data and stream response
        # Return JSON chunks: {"type": "sources"} followed by {"type": "content"}
        import json
        sources_data = [
            {
                "title": r.get("title", "Unknown"),
                "number": r.get("number"),
                "start": r.get("start"),
                "end": r.get("end"),
                "text": r.get("text"),
                "score": 0.0 # Calculate or pass through if available
            }
            for r in results
        ]
        
        yield json.dumps({"type": "sources", "data": sources_data}) + "\n"
        
        async for chunk in async_inference_stream(prompt, model=model):
            yield json.dumps({"type": "content", "data": chunk}) + "\n"

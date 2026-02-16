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
        
        # 2. Build Context
        context_str = "\n\n".join(
            [f"Source {i+1}:\n{chunk['text']}" for i, chunk in enumerate(results)]
        )
        
        # 3. Build Prompt
        prompt = build_query_prompt(query, context_str)
        
        # 4. Yield Sources first (as a special event or just log them? 
        # API usually sends sources at the end or in a separate field.
        # But for streaming, we strictly yield text chunks. 
        # We will yield a special JSON marker for sources at the end or beginning?
        # Standard approach: Stream text, then maybe a final data chunk.
        # Or, we return a response that contains the sources AND a stream connection.
        # But FastAPI streaming response is one body.
        # I'll convert everything to Server-Sent Events (SSE) format to support structured data.
        # Or, simpler: Yield metadata as a JSON line first, then text?
        # Let's stick to yielding text for now, and maybe send sources as the first chunk in JSON format?
        # No, that mixes formatting.
        # Better: The API returns the sources in the response headers? No, headers are small.
        # Valid strategy: Return JSON chunks.
        # Chunk 1: {"type": "sources", "data": [...]}
        # Chunk N: {"type": "content", "data": "..."}
        
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

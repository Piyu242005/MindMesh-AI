from typing import List, AsyncGenerator
import json
import logging
from config import settings
import httpx

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_stream(self, prompt: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response from LLM."""
        full_prompt = f"""Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {prompt}

Answer:"""

        payload = {
            "model": settings.LLM_MODEL,
            "prompt": full_prompt,
            "stream": True,
            "options": {"temperature": 0.7}
        }

        try:
            async with self.client.stream("POST", f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line: continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            yield f"Error generating response: {str(e)}"

generator = Generator()

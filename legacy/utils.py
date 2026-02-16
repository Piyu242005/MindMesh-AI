"""Shared utilities: embedding, LLM inference, error handling, formatting."""

import logging
import time
import requests
import numpy as np
from typing import List, Optional, Dict, Any
from config import Config

# ──────────────────────────── Logging Setup ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("RAG")


# ──────────────────────────── Ollama Health Check ────────────────────────────
def check_ollama_availability() -> bool:
    """Check if the Ollama server is running and reachable."""
    try:
        r = requests.get(Config.OLLAMA_BASE_URL, timeout=5)
        if r.status_code == 200:
            logger.info("Ollama server is reachable at %s", Config.OLLAMA_BASE_URL)
            return True
    except requests.ConnectionError:
        pass
    logger.error(
        "Ollama server is NOT reachable at %s. "
        "Please start Ollama with: ollama serve",
        Config.OLLAMA_BASE_URL,
    )
    return False


# ──────────────────────────── Embedding ────────────────────────────
def create_embedding(
    text_list: List[str],
    model: Optional[str] = None,
    max_retries: int = 3,
    batch_size: int = 64,
) -> List[List[float]]:
    """
    Create embeddings for a list of texts using Ollama API.
    Supports batching and retries with exponential backoff.
    """
    model = model or Config.EMBEDDING_MODEL
    all_embeddings: List[List[float]] = []

    for i in range(0, len(text_list), batch_size):
        batch = text_list[i : i + batch_size]
        embedding = _embed_with_retry(batch, model, max_retries)
        all_embeddings.extend(embedding)
        if len(text_list) > batch_size:
            logger.info(
                "Embedded batch %d/%d",
                i // batch_size + 1,
                (len(text_list) + batch_size - 1) // batch_size,
            )

    return all_embeddings


def _embed_with_retry(
    texts: List[str], model: str, max_retries: int
) -> List[List[float]]:
    """Call the embedding API with exponential backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(
                Config.ollama_embed_url(),
                json={"model": model, "input": texts},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()

            if "embeddings" not in data:
                raise ValueError(f"Unexpected API response: {list(data.keys())}")

            embeddings = data["embeddings"]
            if len(embeddings) != len(texts):
                raise ValueError(
                    f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                )
            return embeddings

        except (requests.RequestException, ValueError) as e:
            wait = 2**attempt
            logger.warning(
                "Embedding attempt %d/%d failed: %s. Retrying in %ds...",
                attempt,
                max_retries,
                e,
                wait,
            )
            if attempt == max_retries:
                logger.error("All embedding attempts failed.")
                raise
            time.sleep(wait)
    return []  # unreachable


# ──────────────────────────── LLM Inference ────────────────────────────
def inference(
    prompt: str,
    model: Optional[str] = None,
    max_retries: int = 3,
    temperature: float = 0.7,
) -> str:
    """
    Generate a response from the LLM via Ollama with retry logic.
    Returns the response text.
    """
    model = model or Config.LLM_MODEL

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(
                Config.ollama_generate_url(),
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
                timeout=300,
            )
            r.raise_for_status()
            data = r.json()

            if "response" not in data:
                raise ValueError(f"No 'response' key in LLM output: {list(data.keys())}")

            return data["response"]

        except (requests.RequestException, ValueError) as e:
            wait = 2**attempt
            logger.warning(
                "Inference attempt %d/%d failed: %s. Retrying in %ds...",
                attempt,
                max_retries,
                e,
                wait,
            )
            if attempt == max_retries:
                logger.error("All inference attempts failed.")
                raise
            time.sleep(wait)
    return ""  # unreachable


# ──────────────────────────── Time Formatting ────────────────────────────
def seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to human-readable HH:MM:SS or MM:SS format."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ──────────────────────────── Deduplication ────────────────────────────
def deduplicate_chunks(chunks: List[Dict[str, Any]], threshold: float = 0.9) -> List[Dict[str, Any]]:
    """
    Remove near-duplicate chunks based on text overlap ratio.
    Uses simple Jaccard similarity on word sets.
    """
    if not chunks:
        return chunks

    unique = [chunks[0]]
    for chunk in chunks[1:]:
        is_dup = False
        words_new = set(chunk["text"].lower().split())
        for existing in unique:
            words_existing = set(existing["text"].lower().split())
            if not words_new or not words_existing:
                continue
            intersection = words_new & words_existing
            union = words_new | words_existing
            jaccard = len(intersection) / len(union) if union else 0
            if jaccard >= threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(chunk)

    removed = len(chunks) - len(unique)
    if removed > 0:
        logger.info("Removed %d near-duplicate chunks", removed)
    return unique


# ──────────────────────────── Text Cleaning ────────────────────────────
FILLER_WORDS = {
    "um", "uh", "uhm", "hmm", "hm", "ah", "oh", "er", "erm",
    "like", "you know", "basically", "actually", "literally",
    "so yeah", "right", "okay so",
}


def clean_text(text: str) -> str:
    """Clean transcription text: remove fillers, normalize whitespace."""
    import re

    text = text.strip()
    # Remove standalone filler words (whole word match)
    for filler in FILLER_WORDS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

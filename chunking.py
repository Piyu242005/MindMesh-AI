"""Advanced chunking with sliding window and overlap for better retrieval."""

import json
import os
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger("RAG.chunking")


def sliding_window_chunks(
    raw_chunks: List[Dict[str, Any]],
    window_seconds: int = None,
    overlap_seconds: int = None,
) -> List[Dict[str, Any]]:
    """
    Merge small Whisper segments into larger overlapping windows.

    Args:
        raw_chunks: Original Whisper segments with start, end, text, number, title.
        window_seconds: Target window size in seconds (default from config).
        overlap_seconds: Overlap between consecutive windows (default from config).

    Returns:
        List of merged chunks with combined text and adjusted timestamps.
    """
    window_seconds = window_seconds or Config.CHUNK_WINDOW_SECONDS
    overlap_seconds = overlap_seconds or Config.CHUNK_OVERLAP_SECONDS

    if not raw_chunks:
        return []

    merged = []
    i = 0

    while i < len(raw_chunks):
        window_start = raw_chunks[i]["start"]
        window_end = window_start + window_seconds
        texts = []
        actual_end = window_start
        j = i

        # Collect segments within the window
        while j < len(raw_chunks) and raw_chunks[j]["start"] < window_end:
            texts.append(raw_chunks[j]["text"].strip())
            actual_end = raw_chunks[j]["end"]
            j += 1

        merged_text = " ".join(texts)

        if merged_text.strip():
            merged.append(
                {
                    "number": raw_chunks[i]["number"],
                    "title": raw_chunks[i]["title"],
                    "start": round(raw_chunks[i]["start"], 2),
                    "end": round(actual_end, 2),
                    "text": merged_text,
                    "segment_count": j - i,
                }
            )

        # Advance by (window - overlap) worth of segments
        step_end = window_start + (window_seconds - overlap_seconds)
        while i < len(raw_chunks) and raw_chunks[i]["start"] < step_end:
            i += 1

        # Safety: always advance at least one segment
        if i == merged[-1].get("_start_idx", -1) if merged else False:
            i += 1

    logger.info(
        "Merged %d raw segments into %d windowed chunks (window=%ds, overlap=%ds)",
        len(raw_chunks),
        len(merged),
        window_seconds,
        overlap_seconds,
    )
    return merged


def process_all_jsons(
    jsons_dir: str = None,
    window_seconds: int = None,
    overlap_seconds: int = None,
) -> List[Dict[str, Any]]:
    """
    Load all JSON transcription files and apply sliding window chunking.
    Returns a flat list of all windowed chunks across all videos.
    """
    jsons_dir = jsons_dir or Config.JSONS_DIR
    all_chunks = []

    json_files = sorted(
        [f for f in os.listdir(jsons_dir) if f.endswith(".json")]
    )

    logger.info("Processing %d JSON files from '%s'", len(json_files), jsons_dir)

    for json_file in json_files:
        filepath = os.path.join(jsons_dir, json_file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)

            raw_chunks = content.get("chunks", [])
            windowed = sliding_window_chunks(
                raw_chunks, window_seconds, overlap_seconds
            )
            all_chunks.extend(windowed)
            logger.info("  %s: %d -> %d chunks", json_file, len(raw_chunks), len(windowed))

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to process '%s': %s", json_file, e)

    logger.info("Total windowed chunks: %d", len(all_chunks))
    return all_chunks

"""
backend/__init__.py — MindMesh AI
System verification utilities shared across all pages.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, Tuple

# Ensure root (MindMesh AI/) is on path so pages can import qdrant_helper
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def verify_system() -> Dict[str, Tuple[str, str, str]]:
    """
    Run all dependency and environment checks.

    Returns dict of:
        check_name → (status, label, detail)
        status: "ok" | "warn" | "error"
    """
    results: Dict[str, Tuple[str, str, str]] = {}

    # ── FFmpeg ──────────────────────────────────────────────────────────────
    try:
        out = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        ver = out.stdout.splitlines()[0] if out.stdout else "Unknown"
        results["FFmpeg"] = ("ok", "Online", ver[:60])
    except FileNotFoundError:
        results["FFmpeg"] = ("error", "Not Found",
                             "Install from https://ffmpeg.org/download.html")
    except Exception as e:
        results["FFmpeg"] = ("error", "Error", str(e)[:80])

    # ── Ollama ──────────────────────────────────────────────────────────────
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            names  = ", ".join(m["name"] for m in models[:3])
            results["Ollama"] = ("ok", "Running",
                                 f"{len(models)} model(s): {names}" if names else "No models pulled")
        else:
            results["Ollama"] = ("warn", "HTTP Error", f"Status {r.status_code}")
    except requests.exceptions.ConnectionError:
        results["Ollama"] = ("error", "Offline", "Run: ollama serve")
    except Exception as e:
        results["Ollama"] = ("error", "Error", str(e)[:80])

    # ── Whisper ─────────────────────────────────────────────────────────────
    try:
        import whisper          # noqa: F401
        results["Whisper"] = ("ok", "Available", "openai-whisper installed")
    except ImportError:
        results["Whisper"] = ("error", "Missing",
                              "pip install openai-whisper")

    # ── SentenceTransformers ────────────────────────────────────────────────
    try:
        from sentence_transformers import SentenceTransformer   # noqa: F401
        results["SentenceTransformers"] = ("ok", "Available",
                                           "BAAI/bge-small-en-v1.5 (384-dim)")
    except ImportError:
        results["SentenceTransformers"] = ("error", "Missing",
                                           "pip install sentence-transformers")

    # ── Qdrant ──────────────────────────────────────────────────────────────
    try:
        import qdrant_helper as qh
        client = qh.get_client()
        info   = qh.collection_info(client)
        vcount = info.get("vector_count", 0)
        results["Qdrant"] = (
            "ok" if vcount > 0 else "warn",
            "Connected",
            f"{vcount:,} vectors in '{qh.QDRANT_COLLECTION}'" if vcount > 0
            else f"Collection empty — run preprocess_json.py",
        )
    except ValueError as e:
        results["Qdrant"] = ("error", "Config Missing", str(e).split("\n")[0])
    except Exception as e:
        results["Qdrant"] = ("error", "Offline", str(e)[:100])

    # ── Required folders ────────────────────────────────────────────────────
    for folder in ["videos", "audios", "jsons"]:
        path = _ROOT / folder
        if path.exists():
            count = len(list(path.iterdir()))
            results[f"Folder: {folder}/"] = ("ok", "Exists", f"{count} file(s)")
        else:
            path.mkdir(parents=True, exist_ok=True)
            results[f"Folder: {folder}/"] = ("warn", "Created", "Was missing — created automatically")

    # ── Environment variables ────────────────────────────────────────────────
    for var in ["QDRANT_URL", "QDRANT_API_KEY", "QDRANT_COLLECTION"]:
        val = os.getenv(var, "").strip()
        if val:
            preview = val[:30] + "…" if len(val) > 30 else val
            if "KEY" in var:
                preview = val[:6] + "•" * 8
            results[f"Env: {var}"] = ("ok", "Set", preview)
        else:
            results[f"Env: {var}"] = ("error", "Missing",
                                      "Add to .env file (see .env.example)")

    return results

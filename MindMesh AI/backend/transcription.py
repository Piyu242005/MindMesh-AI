"""
backend/transcription.py — MindMesh AI
Handles: video → MP3 extraction, Whisper transcription, JSON chunk saving.
Wraps logic from video_to_mp3.py and mp3_to_json.py into callable functions.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional

import streamlit as st

# Ensure root on sys.path so qdrant_helper is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── Whisper model (cached — loaded once per Streamlit session) ────────────────

@st.cache_resource(show_spinner="Loading Whisper model…")
def get_whisper_model(model_size: str = "large-v2"):
    """Load and cache a Whisper model. First call downloads if needed (~3GB for large-v2)."""
    try:
        import whisper
        return whisper.load_model(model_size)
    except ImportError:
        raise ImportError("openai-whisper is not installed. Run: pip install openai-whisper")


# ── System checks ─────────────────────────────────────────────────────────────

def is_ffmpeg_available() -> bool:
    """Return True if ffmpeg is on PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        return True
    except Exception:
        return False


def is_whisper_available() -> bool:
    """Return True if openai-whisper is installed."""
    try:
        import whisper  # noqa: F401
        return True
    except ImportError:
        return False


# ── Video → MP3 ───────────────────────────────────────────────────────────────

def extract_audio(
    video_path: Path,
    output_dir: Path,
    video_number: str,
    video_title: str,
) -> Path:
    """
    Extract audio from a video file using ffmpeg.
    Output filename: {video_number}_{video_title}.mp3

    Raises:
        FileNotFoundError: if ffmpeg is not installed
        subprocess.CalledProcessError: if ffmpeg fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise title for filesystem
    safe_title = "".join(c for c in video_title if c.isalnum() or c in " _-").strip()
    out_name   = f"{video_number}_{safe_title}.mp3"
    out_path   = output_dir / out_name

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vn", "-acodec", "libmp3lame", "-q:a", "2",
         str(out_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-500:]}")

    return out_path


# ── MP3 → JSON chunks ─────────────────────────────────────────────────────────

def transcribe_audio(
    audio_path: Path,
    whisper_model,
    video_number: str,
    video_title: str,
    language: str = "hi",
    task: str = "translate",
) -> Dict[str, Any]:
    """
    Transcribe an audio file using Whisper.

    Returns the full Whisper result dict:
        {"text": "...", "segments": [{start, end, text, ...}, ...]}
    """
    result = whisper_model.transcribe(
        audio=str(audio_path),
        language=language,
        task=task,
        word_timestamps=False,
        verbose=False,
    )
    return result


def build_chunks(
    whisper_result: Dict[str, Any],
    video_number: str,
    video_title: str,
) -> List[Dict[str, Any]]:
    """Convert Whisper segment list into MindMesh chunk format."""
    chunks = []
    for seg in whisper_result.get("segments", []):
        chunks.append({
            "number": video_number,
            "title":  video_title,
            "start":  seg["start"],
            "end":    seg["end"],
            "text":   seg["text"].strip(),
        })
    return chunks


def save_json(
    chunks: List[Dict[str, Any]],
    full_text: str,
    json_dir: Path,
    audio_filename: str,
) -> Path:
    """
    Save chunks to jsons/{audio_filename}.json
    Matches the format produced by mp3_to_json.py.
    """
    json_dir.mkdir(parents=True, exist_ok=True)
    out_path = json_dir / f"{audio_filename}.json"

    payload = {"chunks": chunks, "text": full_text}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return out_path


# ── Full pipeline for a single video ─────────────────────────────────────────

def process_video(
    video_path: Path,
    video_number: str,
    video_title: str,
    whisper_model,
    videos_dir: Path,
    audios_dir: Path,
    jsons_dir:  Path,
    language:   str = "hi",
    task:       str = "translate",
    on_step: Optional[callable] = None,  # on_step(step_name, status, detail)
) -> Dict[str, Any]:
    """
    Run the complete transcription pipeline for one video:
        video → MP3 → Whisper → JSON chunks

    Returns {"chunks": [...], "json_path": Path, "audio_path": Path}
    """

    def _step(name, status, detail=""):
        if on_step:
            on_step(name, status, detail)

    # Step 1: Extract audio
    _step("Extract Audio", "active", str(video_path.name))
    try:
        audio_path = extract_audio(video_path, audios_dir, video_number, video_title)
        _step("Extract Audio", "done", str(audio_path.name))
    except Exception as e:
        _step("Extract Audio", "error", str(e))
        raise

    # Step 2: Transcribe
    _step("Transcribe", "active", f"Whisper ({language} → {task})")
    try:
        whisper_result = transcribe_audio(
            audio_path, whisper_model, video_number, video_title, language, task
        )
        chunks    = build_chunks(whisper_result, video_number, video_title)
        full_text = whisper_result.get("text", "")
        _step("Transcribe", "done", f"{len(chunks)} segments")
    except Exception as e:
        _step("Transcribe", "error", str(e))
        raise

    # Step 3: Save JSON
    _step("Save Chunks", "active", "Writing JSON…")
    try:
        json_path = save_json(chunks, full_text, jsons_dir, audio_path.name)
        _step("Save Chunks", "done", str(json_path.name))
    except Exception as e:
        _step("Save Chunks", "error", str(e))
        raise

    return {
        "chunks":     chunks,
        "json_path":  json_path,
        "audio_path": audio_path,
    }

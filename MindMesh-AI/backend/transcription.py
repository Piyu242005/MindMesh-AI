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

import functools

# Ensure root on sys.path so qdrant_helper is importable
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── Whisper model (cached — loaded once per Streamlit session) ────────────────

@functools.lru_cache(maxsize=1)
def get_whisper_model(model_size: str = "medium"):
    """Load and cache a Faster-Whisper model with auto hardware detection."""
    try:
        from faster_whisper import WhisperModel
        import torch
        
        # Hardware detection
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"[Faster-Whisper] Loading '{model_size}' on {device.upper()} with {compute_type}...")
        return WhisperModel(model_size, device=device, compute_type=compute_type)
    except ImportError:
        raise ImportError("faster-whisper is not installed. Run: pip install faster-whisper")


# ── System checks ─────────────────────────────────────────────────────────────

def is_ffmpeg_available() -> bool:
    """Return True if ffmpeg is on PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        return True
    except Exception:
        return False


def is_whisper_available() -> bool:
    """Return True if faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
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
    on_progress: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Transcribe an audio file using Faster-Whisper.
    Returns the parsed dict: {"text": "...", "segments": [{start, end, text, ...}, ...]}
    Yields to on_progress(text_so_far) if provided.
    """
    # faster-whisper returns an iterator of segments
    segments_gen, info = whisper_model.transcribe(
        str(audio_path),
        language=language if language != "auto" else None,
        task=task,
        vad_filter=True, # Recommended for faster-whisper to remove silence
    )
    
    segments = []
    full_text_chunks = []
    
    for seg in segments_gen:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip()
        })
        full_text_chunks.append(seg.text.strip())
        
        if on_progress:
            on_progress(seg.text.strip())
            
    return {
        "text": " ".join(full_text_chunks),
        "segments": segments
    }


def build_chunks(
    whisper_result: Dict[str, Any],
    video_number: str,
    video_title: str,
) -> List[Dict[str, Any]]:
    """Convert segment list into MindMesh chunk format."""
    chunks = []
    for seg in whisper_result.get("segments", []):
        chunks.append({
            "number": video_number,
            "title":  video_title,
            "start":  seg["start"],
            "end":    seg["end"],
            "text":   seg["text"],
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
    _step("Transcribe", "active", f"Faster-Whisper ({language} → {task})")
    try:
        # Wrap on_step to show live progress
        def _on_progress(latest_text: str):
            # Show the latest transcribed text snippet
            preview = latest_text[:40] + "..." if len(latest_text) > 40 else latest_text
            _step("Transcribe", "active", f"🗣️ {preview}")
            
        whisper_result = transcribe_audio(
            audio_path, whisper_model, video_number, video_title, language, task, on_progress=_on_progress
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

"""
validate_transcription.py — MindMesh AI
Validates that Faster-Whisper is installed, loads correctly, and strictly outputs
the required JSON dictionary format for MindMesh AI.
"""

import sys
import os
import json
from pathlib import Path

# Ensure root is in path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.transcription import get_whisper_model, is_whisper_available, transcribe_audio, build_chunks

def run_tests():
    print("=" * 50)
    print("MindMesh AI — Faster-Whisper Validation")
    print("=" * 50 + "\n")

    print("[1] Checking Installation...")
    if not is_whisper_available():
        print("  ✗ faster-whisper is not installed. Run: pip install faster-whisper")
        sys.exit(1)
    print("  ✓ faster-whisper is installed")

    print("\n[2] Loading Model (medium)...")
    try:
        model = get_whisper_model("medium")
        print("  ✓ Model loaded successfully")
    except Exception as e:
        print(f"  ✗ Failed to load model: {e}")
        sys.exit(1)

    print("\n[3] Transcription Test & JSON Format Check")
    # Check if any audio file exists to test, or skip transcription test
    audios_dir = ROOT / "audios"
    test_audio = None
    if audios_dir.exists():
        for f in audios_dir.glob("*.mp3"):
            test_audio = f
            break

    if not test_audio:
        print("  ⚠️ No MP3 files found in 'audios/' to test. Please upload a video first to validate inference.")
    else:
        print(f"  - Testing with {test_audio.name}...")
        try:
            result = transcribe_audio(
                test_audio, 
                model, 
                video_number="TEST_01", 
                video_title="Validation Test", 
                language="en", 
                task="transcribe"
            )
            print(f"  ✓ Transcribed {len(result.get('segments', []))} segments")
            
            chunks = build_chunks(result, "TEST_01", "Validation Test")
            print(f"  ✓ Built {len(chunks)} MindMesh chunks")
            
            # Validate JSON Schema
            assert len(chunks) > 0, "No chunks generated"
            sample_chunk = chunks[0]
            assert "number" in sample_chunk, "Missing 'number' in chunk"
            assert "title" in sample_chunk, "Missing 'title' in chunk"
            assert "start" in sample_chunk, "Missing 'start' in chunk"
            assert "end" in sample_chunk, "Missing 'end' in chunk"
            assert "text" in sample_chunk, "Missing 'text' in chunk"
            assert isinstance(sample_chunk["start"], (int, float)), "start must be float"
            
            print("  ✓ JSON Schema matches MindMesh requirements perfectly")
        except Exception as e:
            print(f"  ✗ Transcription or validation failed: {e}")
            sys.exit(1)

    print("\n" + "=" * 50)
    print("✅ Validation Complete!")

if __name__ == "__main__":
    run_tests()

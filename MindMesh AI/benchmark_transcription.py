"""
benchmark_transcription.py — MindMesh AI
Simple benchmark script to evaluate Faster-Whisper performance.
"""

import sys
import time
import os
from pathlib import Path

# Ensure root is in path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def run_benchmark():
    print("=" * 50)
    print("MindMesh AI — Faster-Whisper Benchmark")
    print("=" * 50 + "\n")
    
    audios_dir = ROOT / "audios"
    test_audio = None
    if audios_dir.exists():
        for f in audios_dir.glob("*.mp3"):
            test_audio = f
            break
            
    if not test_audio:
        print("⚠️ No MP3 files found in 'audios/' to benchmark. Upload a video first.")
        sys.exit(1)
        
    print(f"Target Audio: {test_audio.name}")
    print(f"File Size:    {test_audio.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 1. Load Model
    print("\n[1] Loading Model ('medium')...")
    t0 = time.time()
    
    from backend.transcription import get_whisper_model, transcribe_audio
    model = get_whisper_model("medium")
    
    load_time = time.time() - t0
    print(f"  ✓ Model loaded in {load_time:.2f} seconds")
    
    # 2. Transcribe Audio
    print("\n[2] Transcribing Audio...")
    t1 = time.time()
    
    result = transcribe_audio(
        test_audio, 
        model, 
        video_number="BENCH", 
        video_title="Benchmark", 
        language="hi", 
        task="translate"
    )
    
    transcribe_time = time.time() - t1
    segments = result.get('segments', [])
    
    print(f"  ✓ Transcribed {len(segments)} segments in {transcribe_time:.2f} seconds")
    
    if segments:
        audio_duration = segments[-1].get("end", 0)
        rtf = transcribe_time / audio_duration if audio_duration > 0 else 0
        print(f"  ✓ Estimated Audio Duration: {audio_duration:.2f} seconds")
        print(f"  ✓ Real-Time Factor (RTF):   {rtf:.2f}x (lower is faster)")
    
    print("\n" + "=" * 50)
    print("✅ Benchmark Complete!")

if __name__ == "__main__":
    run_benchmark()

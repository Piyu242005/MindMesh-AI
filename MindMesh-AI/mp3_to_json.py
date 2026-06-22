import os
import json
import torch
from faster_whisper import WhisperModel
import sys
from pathlib import Path

# Ensure backend module is available
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.telegram_helper import send_notification

# Hardware detection
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"
print(f"Loading model on {device.upper()} with {compute_type}...")

model = WhisperModel("medium", device=device, compute_type=compute_type)

audios = os.listdir("audios")

for audio in audios: 
    if "_" in audio and audio.endswith(".mp3"):
        number = audio.split("_")[0]
        title = audio.split("_")[1][:-4]
        print(f"Processing: {number} - {title}")
        
        segments_gen, info = model.transcribe(
            f"audios/{audio}", 
            language="hi",
            task="translate",
            vad_filter=True
        )
        
        chunks = []
        full_text_chunks = []
        for segment in segments_gen:
            chunks.append({
                "number": number, 
                "title": title, 
                "start": segment.start, 
                "end": segment.end, 
                "text": segment.text.strip()
            })
            full_text_chunks.append(segment.text.strip())
            print(f"  [{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}")
        
        chunks_with_metadata = {"chunks": chunks, "text": " ".join(full_text_chunks)}

        with open(f"jsons/{audio}.json", "w", encoding="utf-8") as f:
            json.dump(chunks_with_metadata, f, ensure_ascii=False, indent=2)

        # Telegram Notification
        send_notification(f"✅ <b>Transcription Completed</b>\n\nCourse: {title}\nChunks Generated: {len(chunks)}")
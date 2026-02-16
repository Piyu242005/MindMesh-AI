"""Stage 2: Transcribe audio files to timestamped JSON using Whisper."""

import whisper
import json
import os
import sys
import argparse
import logging
from config import Config
from utils import clean_text, deduplicate_chunks

logger = logging.getLogger("RAG.mp3_to_json")


def transcribe_audio(
    audio_path: str,
    model,
    language: str = "hi",
    task: str = "translate",
) -> dict:
    """Transcribe a single audio file and return structured chunks."""
    logger.info("Transcribing: %s", audio_path)

    result = model.transcribe(
        audio=audio_path,
        language=language,
        task=task,
        word_timestamps=False,
    )

    return result


def process_transcription(
    result: dict, title: str, number: str, clean: bool = True
) -> dict:
    """
    Convert Whisper transcription result into structured chunks.
    Optionally cleans text by removing filler words.
    """
    chunks = []
    for segment in result["segments"]:
        text = segment["text"]
        if clean:
            text = clean_text(text)

        if not text.strip():
            continue

        chunks.append(
            {
                "number": number,
                "title": title,
                "start": round(segment["start"], 2),
                "end": round(segment["end"], 2),
                "text": text,
            }
        )

    # Deduplicate near-identical consecutive chunks
    chunks = deduplicate_chunks(chunks, threshold=0.85)

    full_text = result.get("text", "")
    if clean:
        full_text = clean_text(full_text)

    return {"chunks": chunks, "text": full_text}


def run_transcription(
    audio_dir: str,
    output_dir: str,
    model_name: str = "large-v2",
    language: str = "hi",
    task: str = "translate",
    skip_existing: bool = True,
):
    """Transcribe all audio files in audio_dir and save JSONs to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(audio_dir):
        logger.error("Audio directory '%s' does not exist.", audio_dir)
        return

    audios = [f for f in os.listdir(audio_dir) if f.lower().endswith(".mp3")]
    if not audios:
        logger.warning("No MP3 files found in '%s'.", audio_dir)
        return

    logger.info("Loading Whisper model '%s'...", model_name)
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        logger.error("Failed to load Whisper model '%s': %s", model_name, e)
        sys.exit(1)

    logger.info("Found %d audio files to transcribe.", len(audios))

    for audio in sorted(audios):
        output_file = os.path.join(output_dir, f"{audio}.json")

        if skip_existing and os.path.exists(output_file):
            logger.info("Skipping (already exists): %s", audio)
            continue

        # Parse metadata from filename
        if "_" in audio:
            number = audio.split("_")[0]
            title = audio.split("_", 1)[1].rsplit(".", 1)[0]  # remove .mp3
        else:
            number = "00"
            title = os.path.splitext(audio)[0]

        try:
            result = transcribe_audio(
                os.path.join(audio_dir, audio), model, language, task
            )
            processed = process_transcription(result, title, number)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)

            logger.info(
                "Transcribed %s: %d chunks generated.", audio, len(processed["chunks"])
            )

        except Exception as e:
            logger.error("Failed to transcribe '%s': %s", audio, e)


def main():
    parser = argparse.ArgumentParser(description="Transcribe MP3 audio to JSON.")
    parser.add_argument(
        "--input", "-i", default=Config.AUDIOS_DIR, help="Input audio directory"
    )
    parser.add_argument(
        "--output", "-o", default=Config.JSONS_DIR, help="Output JSON directory"
    )
    parser.add_argument(
        "--model", "-m", default=Config.WHISPER_MODEL, help="Whisper model name"
    )
    parser.add_argument(
        "--language", "-l", default=Config.WHISPER_LANGUAGE, help="Source language"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Re-transcribe existing files"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    run_transcription(
        args.input,
        args.output,
        model_name=args.model,
        language=args.language,
        skip_existing=not args.force,
    )


if __name__ == "__main__":
    main()

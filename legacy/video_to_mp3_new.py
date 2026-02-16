"""Stage 1: Convert video files to MP3 audio using FFmpeg."""

import os
import sys
import subprocess
import argparse
import logging
from config import Config

logger = logging.getLogger("RAG.video_to_mp3")


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available in PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg not found. Please install FFmpeg and add it to PATH.")
        return False


def convert_video_to_mp3(
    input_dir: str, output_dir: str, skip_existing: bool = True
) -> int:
    """
    Convert all video files in input_dir to MP3 files in output_dir.
    Returns the number of files successfully converted.
    """
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_dir):
        logger.error("Input directory '%s' does not exist.", input_dir)
        return 0

    files = [
        f
        for f in os.listdir(input_dir)
        if f.lower().endswith((".mp4", ".mkv", ".avi", ".webm", ".mov"))
    ]

    if not files:
        logger.warning("No video files found in '%s'.", input_dir)
        return 0

    logger.info("Found %d video files to convert.", len(files))
    converted = 0

    for file in sorted(files):
        try:
            # Extract tutorial number and name
            tutorial_number = file.split(" [")[0].split(" #")[1]
            file_name = file.split(" ｜ ")[0]
        except (IndexError, ValueError):
            # Fallback: use filename without extension
            file_name = os.path.splitext(file)[0]
            tutorial_number = file_name.split("_")[0] if "_" in file_name else "00"
            logger.warning(
                "Could not parse filename '%s', using fallback naming.", file
            )

        output_file = os.path.join(output_dir, f"{tutorial_number}_{file_name}.mp3")

        if skip_existing and os.path.exists(output_file):
            logger.info("Skipping (already exists): %s", output_file)
            continue

        logger.info("Converting: %s -> %s", file, output_file)

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    os.path.join(input_dir, file),
                    "-q:a",
                    "2",
                    "-y",
                    output_file,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error("FFmpeg error for '%s': %s", file, result.stderr[-500:])
            else:
                converted += 1
                logger.info("Successfully converted: %s", file)

        except Exception as e:
            logger.error("Failed to convert '%s': %s", file, e)

    logger.info("Converted %d/%d files.", converted, len(files))
    return converted


def main():
    parser = argparse.ArgumentParser(description="Convert videos to MP3 audio files.")
    parser.add_argument(
        "--input", "-i", default=Config.VIDEOS_DIR, help="Input videos directory"
    )
    parser.add_argument(
        "--output", "-o", default=Config.AUDIOS_DIR, help="Output audio directory"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Re-convert existing files"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not check_ffmpeg():
        sys.exit(1)

    count = convert_video_to_mp3(args.input, args.output, skip_existing=not args.force)
    if count == 0:
        logger.warning("No files were converted.")


if __name__ == "__main__":
    main()

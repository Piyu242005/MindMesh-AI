"""Unified pipeline runner for all RAG stages."""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("RAG.pipeline")


def run_stage_1(args):
    """Stage 1: Video to MP3 conversion."""
    from video_to_mp3_new import convert_video_to_mp3, check_ffmpeg
    from config import Config

    logger.info("=" * 60)
    logger.info("STAGE 1: Video to MP3 Conversion")
    logger.info("=" * 60)

    if not check_ffmpeg():
        return False

    count = convert_video_to_mp3(
        Config.VIDEOS_DIR, Config.AUDIOS_DIR, skip_existing=not args.force
    )
    logger.info("Stage 1 complete: %d files converted.", count)
    return True


def run_stage_2(args):
    """Stage 2: Audio transcription."""
    from mp3_to_json_new import run_transcription
    from config import Config

    logger.info("=" * 60)
    logger.info("STAGE 2: Audio Transcription (Whisper)")
    logger.info("=" * 60)

    run_transcription(
        Config.AUDIOS_DIR,
        Config.JSONS_DIR,
        model_name=Config.WHISPER_MODEL,
        language=Config.WHISPER_LANGUAGE,
        skip_existing=not args.force,
    )
    logger.info("Stage 2 complete.")
    return True


def run_stage_3(args):
    """Stage 3: Embedding generation."""
    from preprocess_json_new import main as preprocess_main

    logger.info("=" * 60)
    logger.info("STAGE 3: Embedding Generation")
    logger.info("=" * 60)

    # Override sys.argv for preprocess_json's argparse
    original_argv = sys.argv
    sys.argv = ["preprocess_json_new.py"]
    if args.force:
        sys.argv.append("--force")
    try:
        preprocess_main()
    finally:
        sys.argv = original_argv

    logger.info("Stage 3 complete.")
    return True


def run_stage_4(args):
    """Stage 4: Interactive query mode."""
    from process_incoming_new import interactive_mode
    from search import HybridSearchEngine
    from utils import check_ollama_availability
    from config import Config

    logger.info("=" * 60)
    logger.info("STAGE 4: Interactive Query Mode")
    logger.info("=" * 60)

    if not check_ollama_availability():
        return False

    engine = HybridSearchEngine(use_reranker=not args.no_reranker)
    interactive_mode(engine, model=Config.LLM_MODEL)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="RAG Pipeline Runner — run all stages or specific ones."
    )
    parser.add_argument(
        "--stages",
        "-s",
        nargs="+",
        type=int,
        choices=[1, 2, 3, 4],
        default=[1, 2, 3, 4],
        help="Stages to run (default: all). 1=video2mp3, 2=transcribe, 3=embed, 4=query",
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force re-processing of existing files"
    )
    parser.add_argument(
        "--no-reranker", action="store_true", help="Disable cross-encoder reranking"
    )
    parser.add_argument(
        "--ui", action="store_true", help="Launch Streamlit web UI instead of CLI"
    )
    args = parser.parse_args()

    if args.ui:
        import subprocess
        logger.info("Launching Streamlit UI...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        return

    stage_runners = {1: run_stage_1, 2: run_stage_2, 3: run_stage_3, 4: run_stage_4}

    for stage_num in sorted(args.stages):
        logger.info("\nRunning Stage %d...", stage_num)
        success = stage_runners[stage_num](args)
        if not success:
            logger.error("Stage %d failed. Stopping pipeline.", stage_num)
            sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("ALL STAGES COMPLETE!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

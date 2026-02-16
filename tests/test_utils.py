"""Unit tests for the RAG pipeline utilities."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    seconds_to_timestamp,
    clean_text,
    deduplicate_chunks,
)


class TestSecondsToTimestamp:
    def test_zero(self):
        assert seconds_to_timestamp(0) == "00:00"

    def test_seconds_only(self):
        assert seconds_to_timestamp(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert seconds_to_timestamp(125) == "02:05"

    def test_hours(self):
        assert seconds_to_timestamp(3661) == "01:01:01"

    def test_float_input(self):
        assert seconds_to_timestamp(90.7) == "01:30"

    def test_large_value(self):
        assert seconds_to_timestamp(7200) == "02:00:00"


class TestCleanText:
    def test_removes_filler_words(self):
        result = clean_text("So um I think uh this is the answer")
        assert "um" not in result.lower()
        assert "uh" not in result.lower()

    def test_normalizes_whitespace(self):
        result = clean_text("  hello    world  ")
        assert result == "hello world"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_preserves_meaningful_content(self):
        text = "HTML stands for HyperText Markup Language"
        assert clean_text(text) == text

    def test_strips_leading_trailing(self):
        assert clean_text("  hello  ") == "hello"


class TestDeduplicateChunks:
    def test_no_duplicates(self):
        chunks = [
            {"text": "This is about HTML basics"},
            {"text": "CSS is used for styling web pages"},
        ]
        result = deduplicate_chunks(chunks)
        assert len(result) == 2

    def test_exact_duplicates(self):
        chunks = [
            {"text": "This is about HTML basics"},
            {"text": "This is about HTML basics"},
        ]
        result = deduplicate_chunks(chunks, threshold=0.9)
        assert len(result) == 1

    def test_near_duplicates(self):
        chunks = [
            {"text": "HTML is a markup language used for web development"},
            {"text": "HTML is a markup language used for web development pages"},
        ]
        result = deduplicate_chunks(chunks, threshold=0.8)
        assert len(result) == 1

    def test_empty_list(self):
        assert deduplicate_chunks([]) == []

    def test_single_item(self):
        chunks = [{"text": "hello"}]
        result = deduplicate_chunks(chunks)
        assert len(result) == 1


class TestChunking:
    def test_sliding_window(self):
        from chunking import sliding_window_chunks

        raw = [
            {"number": "1", "title": "Test", "start": 0, "end": 5, "text": "chunk one"},
            {"number": "1", "title": "Test", "start": 5, "end": 10, "text": "chunk two"},
            {"number": "1", "title": "Test", "start": 10, "end": 15, "text": "chunk three"},
            {"number": "1", "title": "Test", "start": 15, "end": 20, "text": "chunk four"},
            {"number": "1", "title": "Test", "start": 20, "end": 25, "text": "chunk five"},
            {"number": "1", "title": "Test", "start": 25, "end": 30, "text": "chunk six"},
            {"number": "1", "title": "Test", "start": 30, "end": 35, "text": "chunk seven"},
        ]

        merged = sliding_window_chunks(raw, window_seconds=15, overlap_seconds=5)

        # Should produce fewer chunks than raw
        assert len(merged) < len(raw)
        # Each merged chunk should contain text from multiple segments
        assert "chunk one" in merged[0]["text"]
        assert "chunk two" in merged[0]["text"]

    def test_empty_input(self):
        from chunking import sliding_window_chunks

        assert sliding_window_chunks([]) == []


class TestConfig:
    def test_defaults(self):
        from config import Config

        assert Config.EMBEDDING_MODEL == "bge-m3"
        assert Config.TOP_K_RESULTS == 5
        assert Config.SIMILARITY_THRESHOLD == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

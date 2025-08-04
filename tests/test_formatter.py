"""Tests for the formatter module."""

from recordnote.formatter import MinutesFormatter


def test_format_timestamp() -> None:
    """Test timestamp formatting."""
    formatter = MinutesFormatter()
    
    # Test various timestamps
    assert formatter._format_timestamp(0) == "00:00"
    assert formatter._format_timestamp(65) == "01:05"
    assert formatter._format_timestamp(3661) == "61:01"


def test_clean_text() -> None:
    """Test text cleaning functionality."""
    formatter = MinutesFormatter()
    
    # Test basic text cleaning
    text = "これは　　テスト　です。"
    expected = "これは テスト です。"
    assert formatter._clean_text(text) == expected
    
    # Test empty text
    assert formatter._clean_text("") == ""
    assert formatter._clean_text("   ") == ""


def test_get_summary_stats() -> None:
    """Test summary statistics generation."""
    formatter = MinutesFormatter()
    
    # Test with basic transcription result
    transcription_result = {
        "text": "これはテストです。",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "これはテストです。"}
        ]
    }
    
    stats = formatter.get_summary_stats(transcription_result)
    
    assert stats["total_duration"] == 2.0
    assert stats["segment_count"] == 1
    assert stats["character_count"] == 8
    assert stats["word_count"] == 1
    
    # Test with empty result
    empty_result = {"text": "", "segments": []}
    empty_stats = formatter.get_summary_stats(empty_result)
    
    assert empty_stats["total_duration"] == 0
    assert empty_stats["segment_count"] == 0
    assert empty_stats["character_count"] == 0
    assert empty_stats["word_count"] == 0
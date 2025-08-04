"""Meeting minutes formatting module."""

import re
from datetime import datetime
from typing import Any, Dict, List


class MinutesFormatter:
    """Formatter for converting transcribed text into readable meeting minutes."""

    def __init__(self) -> None:
        """Initialize the minutes formatter."""
        pass

    def format_minutes(
        self, transcription_result: Dict[str, Any], title: str = ""
    ) -> str:
        """Format transcription result into meeting minutes.

        Args:
            transcription_result: Result from transcriber containing text and segments
            title: Optional title for the meeting minutes

        Returns:
            Formatted meeting minutes as string
        """
        # Extract data from transcription result
        full_text = transcription_result.get("text", "")
        segments = transcription_result.get("segments", [])
        language = transcription_result.get("language", "ja")

        # Generate header
        header = self._generate_header(title)

        # Format segments with timestamps
        formatted_segments = self._format_segments(segments)

        # Clean and format full text
        cleaned_text = self._clean_text(full_text)

        # Combine all parts
        minutes = f"{header}\n\n"
        minutes += "## 音声認識結果\n\n"
        minutes += f"{cleaned_text}\n\n"

        if formatted_segments:
            minutes += "## タイムスタンプ付き詳細\n\n"
            minutes += formatted_segments

        minutes += f"\n\n---\n\n**言語**: {language}\n"
        minutes += f"**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"

        return minutes

    def _generate_header(self, title: str) -> str:
        """Generate header for meeting minutes.

        Args:
            title: Title of the meeting

        Returns:
            Formatted header string
        """
        if not title:
            title = "会議録"

        return f"# {title}\n\n**日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"

    def _format_segments(self, segments: List[Dict[str, Any]]) -> str:
        """Format segments with timestamps.

        Args:
            segments: List of segment dictionaries with start, end, and text

        Returns:
            Formatted segments string
        """
        if not segments:
            return ""

        formatted = ""
        for segment in segments:
            start_time = self._format_timestamp(segment.get("start", 0))
            end_time = self._format_timestamp(segment.get("end", 0))
            text = segment.get("text", "").strip()

            if text:
                formatted += f"**{start_time} - {end_time}**: {text}\n\n"

        return formatted

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp from seconds to MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _clean_text(self, text: str) -> str:
        """Clean and format transcribed text.

        Args:
            text: Raw transcribed text

        Returns:
            Cleaned and formatted text
        """
        if not text:
            return ""

        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", text.strip())

        # Add proper line breaks for readability
        # Split into sentences and add line breaks
        sentences = re.split(r"([。！？])", cleaned)
        formatted_sentences = []

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if sentence.strip():
                formatted_sentences.append(sentence.strip())

        # Join sentences with line breaks every 2-3 sentences for readability
        result = ""
        for i, sentence in enumerate(formatted_sentences):
            result += sentence
            if (i + 1) % 2 == 0 and i < len(formatted_sentences) - 1:
                result += "\n\n"
            elif i < len(formatted_sentences) - 1:
                result += " "

        return result

    def export_to_file(self, minutes: str, file_path: str) -> None:
        """Export formatted minutes to a file.

        Args:
            minutes: Formatted minutes string
            file_path: Path to save the file
        """
        from pathlib import Path

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(minutes)

    def get_summary_stats(self, transcription_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics of the transcription.

        Args:
            transcription_result: Result from transcriber

        Returns:
            Dictionary with summary statistics
        """
        segments = transcription_result.get("segments", [])
        full_text = transcription_result.get("text", "")

        if not segments:
            return {
                "total_duration": 0,
                "segment_count": 0,
                "word_count": len(full_text.split()) if full_text else 0,
                "character_count": len(full_text) if full_text else 0,
            }

        total_duration = segments[-1].get("end", 0) if segments else 0
        word_count = len(full_text.split()) if full_text else 0
        character_count = len(full_text) if full_text else 0

        return {
            "total_duration": total_duration,
            "segment_count": len(segments),
            "word_count": word_count,
            "character_count": character_count,
        }
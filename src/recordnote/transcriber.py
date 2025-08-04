"""Speech-to-text transcription module using Faster Whisper."""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from faster_whisper import WhisperModel


class SpeechTranscriber:
    """Speech transcriber using Faster Whisper for Japanese audio."""

    def __init__(self, model_size: str = "base") -> None:
        """Initialize the speech transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._model: Optional[WhisperModel] = None

    def load_model(self) -> None:
        """Load the Whisper model. Called automatically when needed."""
        if self._model is None:
            print(f"Loading Faster Whisper model: {self.model_size}")
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe_file(self, audio_file_path: Path) -> Dict[str, Any]:
        """Transcribe audio file to text.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary containing transcribed text and language info
        """
        if not audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        self.load_model()
        assert self._model is not None

        # Transcribe with Japanese language specified
        segments, info = self._model.transcribe(
            str(audio_file_path), language="ja", beam_size=5
        )

        segments_list: List[Dict[str, Any]] = []
        full_text = ""

        for segment in segments:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
            segments_list.append(segment_dict)
            full_text += segment.text.strip() + " "

        return {
            "text": full_text.strip(),
            "language": info.language,
            "segments": segments_list,
        }

    def transcribe_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Transcribe audio from bytes data.

        Args:
            audio_bytes: Audio data as bytes (WAV format)

        Returns:
            Dictionary containing transcribed text and language info
        """
        # Create temporary file for audio bytes
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        try:
            return self.transcribe_file(temp_path)
        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_size": self.model_size,
            "loaded": self._model is not None,
        }
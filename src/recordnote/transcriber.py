"""Speech-to-text transcription module using OpenAI Whisper."""

import tempfile
from pathlib import Path
from typing import Dict, Optional

import whisper
from whisper.model import Whisper


class SpeechTranscriber:
    """Speech transcriber using OpenAI Whisper for Japanese audio."""

    def __init__(self, model_size: str = "base") -> None:
        """Initialize the speech transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._model: Optional[Whisper] = None

    def load_model(self) -> None:
        """Load the Whisper model. Called automatically when needed."""
        if self._model is None:
            print(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(self.model_size)

    def transcribe_file(self, audio_file_path: Path) -> Dict[str, str]:
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
        result = self._model.transcribe(
            str(audio_file_path), language="ja", verbose=False
        )

        return {
            "text": result["text"].strip(),
            "language": result["language"],
            "segments": [
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                }
                for segment in result["segments"]
            ],
        }

    def transcribe_bytes(self, audio_bytes: bytes) -> Dict[str, str]:
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
"""Audio recording module using sounddevice."""

import io
import threading
import time
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.io import wavfile


class AudioRecorder:
    """Audio recorder class for recording voice to WAV files."""

    def __init__(self, sample_rate: int = 44100, channels: int = 1) -> None:
        """Initialize the audio recorder.

        Args:
            sample_rate: Sample rate for recording (default: 44100 Hz)
            channels: Number of audio channels (default: 1 for mono)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data: list[np.ndarray] = []
        self._recording_thread: Optional[threading.Thread] = None

    def start_recording(self) -> None:
        """Start audio recording."""
        if self.recording:
            raise RuntimeError("Recording is already in progress")

        self.recording = True
        self.audio_data = []
        self._recording_thread = threading.Thread(target=self._record_audio)
        self._recording_thread.start()

    def stop_recording(self) -> None:
        """Stop audio recording."""
        if not self.recording:
            raise RuntimeError("No recording in progress")

        self.recording = False
        if self._recording_thread:
            self._recording_thread.join()

    def save_to_file(self, file_path: Path) -> None:
        """Save recorded audio to WAV file.

        Args:
            file_path: Path to save the WAV file
        """
        if not self.audio_data:
            raise RuntimeError("No audio data to save")

        # Concatenate all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)

        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as WAV file
        wavfile.write(str(file_path), self.sample_rate, audio_array)

    def get_audio_bytes(self) -> bytes:
        """Get recorded audio as bytes in WAV format.

        Returns:
            Audio data as bytes in WAV format
        """
        if not self.audio_data:
            raise RuntimeError("No audio data available")

        # Concatenate all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)

        # Create WAV bytes using io.BytesIO
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, self.sample_rate, audio_array)
        wav_buffer.seek(0)
        return wav_buffer.read()

    def _record_audio(self) -> None:
        """Internal method to record audio in a separate thread."""

        def audio_callback(
            indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
        ) -> None:
            """Callback function for audio recording."""
            if status:
                print(f"Audio callback status: {status}")
            if self.recording:
                self.audio_data.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                dtype=np.float32,
            ):
                while self.recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Recording error: {e}")
            self.recording = False

    def is_recording(self) -> bool:
        """Check if recording is currently active.

        Returns:
            True if recording is active, False otherwise
        """
        return self.recording

    def get_duration(self) -> float:
        """Get the duration of recorded audio in seconds.

        Returns:
            Duration in seconds
        """
        if not self.audio_data:
            return 0.0

        total_frames = sum(len(chunk) for chunk in self.audio_data)
        return total_frames / self.sample_rate

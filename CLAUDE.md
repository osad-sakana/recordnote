# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

```bash
# Setup and dependencies
poetry install                          # Install all dependencies
poetry shell                           # Activate virtual environment

# Run the application
streamlit run main.py                   # Start the web application

# Code quality and testing
poetry run mypy src/                    # Type checking
poetry run black src/                   # Code formatting
poetry run isort src/                   # Import sorting
poetry run flake8 src/                  # Linting
poetry run pytest tests/               # Run all tests
poetry run pytest tests/test_formatter.py::test_clean_text  # Run single test

# Pre-commit hooks
pre-commit install                      # Setup hooks
pre-commit run --all-files             # Run all hooks manually
```

## Architecture Overview

RecordNote is a local Japanese voice-to-text meeting minutes application with a modular architecture:

### Core Processing Pipeline
1. **AudioRecorder** (`recorder.py`) - Captures real-time audio using sounddevice, stores in memory as numpy arrays
2. **SpeechTranscriber** (`transcriber.py`) - Processes audio through OpenAI Whisper for Japanese speech recognition
3. **MinutesFormatter** (`formatter.py`) - Converts transcribed text into structured meeting minutes with timestamps
4. **RecordNoteApp** (`app.py`) - Streamlit web interface orchestrating the entire workflow

### Key Design Patterns
- **State Management**: Streamlit session state manages recording workflow (`recording_state`: stopped/recording/processing/completed)
- **Threaded Recording**: Audio capture runs in separate thread to avoid blocking UI
- **Lazy Loading**: Whisper model loaded on-demand to reduce startup time
- **Modular Pipeline**: Each component can be used independently for testing/debugging

### Critical Implementation Details
- **Audio Format**: Uses WAV format internally, 44.1kHz sample rate, mono channel
- **Memory Management**: Audio stored as list of numpy chunks during recording, concatenated for processing
- **Japanese Optimization**: Whisper explicitly configured for Japanese language (`language="ja"`)
- **Temporary Files**: Uses Python tempfile for Whisper processing, automatically cleaned up

### Configuration
- **Whisper Models**: Configurable model size (tiny/base/small/medium/large) balancing speed vs accuracy
- **Audio Settings**: Sample rate and channels configurable in AudioRecorder constructor
- **Type Safety**: Strict mypy configuration with `disallow_untyped_defs=true`

### Development Notes
- Python 3.9+ required (excludes 3.9.7 due to Streamlit incompatibility)
- All external libraries have type stub ignores in mypy config
- Pre-commit hooks enforce black (88 char), isort (black profile), flake8, and mypy
- Tests focus on formatter logic due to external dependencies in other modules
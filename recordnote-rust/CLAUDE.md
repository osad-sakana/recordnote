# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

```bash
# Build and run
cargo build                             # Build debug version
cargo run                               # Run the GUI application
cargo build --release                   # Build optimized release version

# Testing
cargo test                              # Run all tests
cargo test --lib                        # Run unit tests only
cargo test --test integration_test     # Run integration tests only
cargo test -- --nocapture              # Run tests with output

# Code quality
cargo check                             # Check compilation without building
cargo clippy                            # Linting
cargo fmt                               # Code formatting

# Logging and debugging
RUST_LOG=info cargo run                 # Run with info logging
RUST_LOG=debug cargo run               # Run with debug logging
RUST_LOG=recordnote::audio=trace cargo run  # Module-specific logging
```

## Architecture Overview

RecordNote is a Rust-based Japanese voice recording and meeting minutes application built with Druid GUI framework. The architecture follows a modular design with clear separation between audio processing, speech recognition, formatting, and UI components.

### Core Module Structure

- **`src/audio/`** - Audio recording using `cpal` for cross-platform audio I/O
- **`src/speech/`** - Speech-to-text transcription (currently placeholder implementation)  
- **`src/formatter/`** - Meeting minutes formatting and Japanese text processing
- **`src/ui/`** - Druid GUI application with custom recording widget

### Key Design Patterns

**State Management**: The `AppState` struct in `src/ui/app.rs` manages the entire application state using Druid's reactive data model. State changes automatically trigger UI updates.

**Custom Widget Pattern**: `RecordingWidget` in `src/ui/recording_widget.rs` wraps the main UI and handles audio lifecycle events. This widget manages the actual recording functionality separate from UI layout concerns.

**Thread-Safe Audio Processing**: Audio recording runs on separate threads using `Arc<Mutex<>>` for safe shared state. The UI communicates with audio components through event-driven updates.

**Lazy Component Initialization**: Audio components (`AudioRecorder`, `WhisperTranscriber`, `MinutesFormatter`) are initialized when the UI window connects, not at application startup.

### Critical Implementation Details

**Audio Recording Flow**:
1. User clicks record → UI state changes to `is_recording: true`
2. `RecordingWidget` detects state change and calls `recorder.start_recording()`
3. Timer events update recording duration every 100ms
4. Stop button triggers processing phase with dummy transcription data
5. Results are formatted and displayed in the UI

**State Transitions**: 
- `stopped` → `recording` → `processing` → `completed`
- Each state change triggers appropriate UI updates (button states, status messages)

**Error Handling**: Uses `anyhow::Result` for error propagation with user-friendly error messages displayed in the status bar.

## Speech Recognition Integration

The current implementation uses placeholder/demo data for speech recognition. The `WhisperTranscriber` structure is prepared for integration with actual Whisper models:

- Commented-out dependencies for `candle-core/candle-nn/candle-transformers` in `Cargo.toml`
- `src/speech/transcriber.rs` contains the interface but returns dummy Japanese text
- To enable real speech recognition, uncomment the candle dependencies and implement actual model loading

## Development Notes

### Testing Strategy
- Unit tests focus on individual component functionality (formatter, recorder creation)
- Integration tests verify component interaction and data flow
- Audio components are difficult to test automatically due to hardware dependencies

### Audio Platform Considerations
- `cpal` streams are not `Send` across threads, requiring careful architecture for cross-platform compatibility  
- Recording state management uses `try_lock()` to avoid blocking the UI thread
- macOS requires microphone permissions which will prompt on first run

### Performance Characteristics
- GUI runs on main thread with 100ms timer updates during recording
- Audio processing happens synchronously after recording stops to avoid threading complexity
- Memory usage is optimized through lazy initialization and efficient buffer management

### Known Limitations
- No actual Whisper model integration (placeholder implementation)
- File save uses simple `std::fs::write` rather than native file dialogs
- No audio format configuration UI (hardcoded to 44.1kHz mono)
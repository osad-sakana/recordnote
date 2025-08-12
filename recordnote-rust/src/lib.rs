pub mod audio;
pub mod formatter;
pub mod speech;
pub mod ui;

pub use audio::recorder::AudioRecorder;
pub use formatter::minutes::MinutesFormatter;
pub use speech::transcriber::WhisperTranscriber;
pub use ui::app::RecordNoteApp;
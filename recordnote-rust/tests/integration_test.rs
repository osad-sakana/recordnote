use recordnote::{AudioRecorder, MinutesFormatter, WhisperTranscriber};
use std::path::PathBuf;
use tempfile::TempDir;

#[test]
fn test_audio_recorder_creation() {
    let recorder = AudioRecorder::default();
    assert!(!recorder.is_recording());
    assert_eq!(recorder.get_duration(), 0.0);
}

#[tokio::test]
async fn test_transcriber_creation() {
    let result = WhisperTranscriber::default();
    assert!(result.is_ok());
    
    let mut transcriber = result.unwrap();
    let info = transcriber.get_model_info();
    assert!(info.contains_key("model_size"));
    assert!(info.contains_key("loaded"));
}

#[test]
fn test_formatter_basic_functionality() {
    use recordnote::speech::transcriber::{TranscriptionResult, TranscriptionSegment};
    
    let formatter = MinutesFormatter::new();
    
    let transcription = TranscriptionResult {
        text: "これはテストです。".to_string(),
        language: "ja".to_string(),
        segments: vec![
            TranscriptionSegment {
                start: 0.0,
                end: 2.0,
                text: "これはテストです。".to_string(),
            }
        ],
    };
    
    let minutes = formatter.format_minutes(&transcription, Some("テスト会議"));
    
    assert!(minutes.contains("テスト会議"));
    assert!(minutes.contains("これはテストです。"));
    assert!(minutes.contains("音声認識結果"));
    assert!(minutes.contains("タイムスタンプ付き詳細"));
}

#[test]
fn test_formatter_export_to_file() {
    let formatter = MinutesFormatter::new();
    let temp_dir = TempDir::new().unwrap();
    let file_path = temp_dir.path().join("test_minutes.md");
    
    let content = "# テスト議事録\n\nこれはテストです。";
    let result = formatter.export_to_file(content, &file_path);
    
    assert!(result.is_ok());
    assert!(file_path.exists());
    
    let saved_content = std::fs::read_to_string(&file_path).unwrap();
    assert_eq!(saved_content, content);
}

#[test]
fn test_formatter_summary_stats() {
    use recordnote::speech::transcriber::{TranscriptionResult, TranscriptionSegment};
    
    let formatter = MinutesFormatter::new();
    
    let transcription = TranscriptionResult {
        text: "これは テスト です".to_string(),
        language: "ja".to_string(),
        segments: vec![
            TranscriptionSegment {
                start: 0.0,
                end: 1.5,
                text: "これは".to_string(),
            },
            TranscriptionSegment {
                start: 1.5,
                end: 3.0,
                text: "テスト です".to_string(),
            },
        ],
    };
    
    let stats = formatter.get_summary_stats(&transcription);
    
    assert_eq!(stats.total_duration, 3.0);
    assert_eq!(stats.segment_count, 2);
    assert_eq!(stats.word_count, 3); // "これは", "テスト", "です"
    assert!(stats.character_count > 0);
}

#[test]
fn test_recorder_state_management() {
    use recordnote::audio::recorder::RecordingState;
    
    let recorder = AudioRecorder::default();
    
    // Initial state should be stopped
    assert_eq!(recorder.get_state(), RecordingState::Stopped);
    assert!(!recorder.is_recording());
}

#[tokio::test] 
async fn test_transcriber_model_info() {
    let mut transcriber = WhisperTranscriber::new("tiny".to_string()).unwrap();
    let info = transcriber.get_model_info();
    
    assert_eq!(info.get("model_size").unwrap(), "tiny");
    assert_eq!(info.get("loaded").unwrap(), &serde_json::Value::Bool(false));
}
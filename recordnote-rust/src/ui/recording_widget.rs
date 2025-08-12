use super::app::AppState;
use crate::audio::recorder::AudioRecorder;
use crate::formatter::minutes::MinutesFormatter;
use crate::speech::transcriber::WhisperTranscriber;
use druid::{
    BoxConstraints, Env, Event, EventCtx, LayoutCtx, LifeCycle, LifeCycleCtx, PaintCtx, Size,
    TimerToken, UpdateCtx, Widget,
};
use std::sync::{Arc, Mutex};
use std::time::Duration;

pub struct RecordingWidget<W> {
    inner: W,
    recorder: Option<Arc<Mutex<AudioRecorder>>>,
    transcriber: Option<Arc<Mutex<WhisperTranscriber>>>,
    formatter: Option<MinutesFormatter>,
    timer_token: Option<TimerToken>,
    recording_started: bool,
    processing_started: bool,
}

impl<W> RecordingWidget<W> {
    pub fn new(inner: W) -> Self {
        Self {
            inner,
            recorder: None,
            transcriber: None,
            formatter: None,
            timer_token: None,
            recording_started: false,
            processing_started: false,
        }
    }
}

impl<W: Widget<AppState>> Widget<AppState> for RecordingWidget<W> {
    fn event(&mut self, ctx: &mut EventCtx, event: &Event, data: &mut AppState, env: &Env) {
        match event {
            Event::WindowConnected => {
                // Initialize components when window is connected
                if self.recorder.is_none() {
                    self.recorder = Some(Arc::new(Mutex::new(AudioRecorder::default())));
                    match WhisperTranscriber::default() {
                        Ok(transcriber) => {
                            self.transcriber = Some(Arc::new(Mutex::new(transcriber)));
                        }
                        Err(e) => {
                            log::error!("Failed to create transcriber: {}", e);
                        }
                    }
                    self.formatter = Some(MinutesFormatter::new());
                    log::info!("Audio components initialized");
                }
            }
            Event::Timer(token) => {
                if let Some(timer_token) = &self.timer_token {
                    if token == timer_token {
                        // Update duration if recording
                        if let Some(recorder) = &self.recorder {
                            if let Ok(recorder) = recorder.try_lock() {
                                if recorder.is_recording() {
                                    let duration = recorder.get_duration();
                                    data.duration = format!("録音時間: {:.1}秒", duration);
                                    ctx.request_update();
                                    
                                    // Schedule next update
                                    self.timer_token = Some(ctx.request_timer(Duration::from_millis(100)));
                                }
                            }
                        }
                    }
                }
            }
            _ => {}
        }

        // Handle state changes
        if let (Some(recorder), Some(transcriber), Some(formatter)) = 
            (&self.recorder, &self.transcriber, &self.formatter) {
            
            // Start recording if requested and not already started
            if data.is_recording && !self.recording_started {
                if let Ok(mut recorder_guard) = recorder.try_lock() {
                    match recorder_guard.start_recording() {
                        Ok(()) => {
                            self.recording_started = true;
                            self.timer_token = Some(ctx.request_timer(Duration::from_millis(100)));
                            log::info!("Recording started");
                        }
                        Err(e) => {
                            data.status = format!("❌ 録音開始エラー: {}", e);
                            data.is_recording = false;
                            data.recording_state = "stopped".to_string();
                        }
                    }
                }
            }

            // Stop recording and start processing if requested
            if data.is_processing && !self.processing_started && self.recording_started {
                self.processing_started = true;
                self.recording_started = false;
                
                // Stop recording synchronously
                if let Ok(mut recorder_guard) = recorder.try_lock() {
                    match recorder_guard.stop_recording() {
                        Ok(()) => {
                            log::info!("Recording stopped, processing...");
                            
                            // For demo purposes, create dummy transcription result
                            let dummy_result = crate::speech::transcriber::TranscriptionResult {
                                text: "これは音声認識の結果です。実際の録音内容がここに表示されます。".to_string(),
                                language: "ja".to_string(),
                                segments: vec![
                                    crate::speech::transcriber::TranscriptionSegment {
                                        start: 0.0,
                                        end: 3.0,
                                        text: "これは音声認識の結果です。".to_string(),
                                    },
                                    crate::speech::transcriber::TranscriptionSegment {
                                        start: 3.0,
                                        end: 6.0,
                                        text: "実際の録音内容がここに表示されます。".to_string(),
                                    },
                                ],
                            };
                            
                            let formatted = formatter.format_minutes(&dummy_result, None);
                            log::info!("Processing completed: {} chars", formatted.len());
                            
                            // Update UI with results
                            data.results_text = formatted.clone();
                            data.formatted_minutes = formatted;
                            data.is_processing = false;
                            data.can_download = true;
                            data.recording_state = "completed".to_string();
                            data.status = "✅ 処理完了!".to_string();
                        }
                        Err(e) => {
                            log::error!("Failed to stop recording: {}", e);
                            data.status = format!("❌ 録音停止エラー: {}", e);
                            data.is_processing = false;
                            data.recording_state = "stopped".to_string();
                        }
                    }
                }
            }

            // Reset states when starting new recording
            if !data.is_recording && !data.is_processing && self.recording_started {
                self.recording_started = false;
                self.processing_started = false;
                self.timer_token = None;
            }
        }

        self.inner.event(ctx, event, data, env);
    }

    fn lifecycle(&mut self, ctx: &mut LifeCycleCtx, event: &LifeCycle, data: &AppState, env: &Env) {
        self.inner.lifecycle(ctx, event, data, env);
    }

    fn update(&mut self, ctx: &mut UpdateCtx, old_data: &AppState, data: &AppState, env: &Env) {
        self.inner.update(ctx, old_data, data, env);
    }

    fn layout(&mut self, ctx: &mut LayoutCtx, bc: &BoxConstraints, data: &AppState, env: &Env) -> Size {
        self.inner.layout(ctx, bc, data, env)
    }

    fn paint(&mut self, ctx: &mut PaintCtx, data: &AppState, env: &Env) {
        self.inner.paint(ctx, data, env);
    }
}
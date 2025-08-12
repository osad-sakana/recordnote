use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Host, Stream, StreamConfig};
use hound::{WavSpec, WavWriter};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tokio::sync::mpsc;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum RecordingState {
    Stopped,
    Recording,
    Processing,
}

pub struct AudioRecorder {
    sample_rate: u32,
    channels: u16,
    state: Arc<Mutex<RecordingState>>,
    audio_data: Arc<Mutex<Vec<f32>>>,
    stream: Option<Stream>,
}

impl AudioRecorder {
    pub fn new(sample_rate: u32, channels: u16) -> Self {
        Self {
            sample_rate,
            channels,
            state: Arc::new(Mutex::new(RecordingState::Stopped)),
            audio_data: Arc::new(Mutex::new(Vec::new())),
            stream: None,
        }
    }

    pub fn default() -> Self {
        Self::new(44100, 1)
    }

    pub fn start_recording(&mut self) -> Result<()> {
        {
            let mut state = self.state.lock().unwrap();
            if *state != RecordingState::Stopped {
                return Err(anyhow::anyhow!("Recording is already in progress"));
            }
            *state = RecordingState::Recording;
        }

        // Clear previous audio data
        self.audio_data.lock().unwrap().clear();

        // Setup audio input
        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .context("No input device available")?;

        let config = self.get_stream_config(&device)?;

        let audio_data = Arc::clone(&self.audio_data);
        let state = Arc::clone(&self.state);

        let stream = device.build_input_stream(
            &config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                let state_guard = state.lock().unwrap();
                if *state_guard == RecordingState::Recording {
                    let mut audio_guard = audio_data.lock().unwrap();
                    audio_guard.extend_from_slice(data);
                }
            },
            move |err| {
                eprintln!("Audio stream error: {}", err);
            },
            None,
        )?;

        stream.play()?;
        self.stream = Some(stream);

        Ok(())
    }

    pub fn stop_recording(&mut self) -> Result<()> {
        {
            let mut state = self.state.lock().unwrap();
            if *state != RecordingState::Recording {
                return Err(anyhow::anyhow!("No recording in progress"));
            }
            *state = RecordingState::Processing;
        }

        // Stop the stream
        if let Some(stream) = self.stream.take() {
            drop(stream);
        }

        // Small delay to ensure all data is captured
        thread::sleep(Duration::from_millis(100));

        {
            let mut state = self.state.lock().unwrap();
            *state = RecordingState::Stopped;
        }

        Ok(())
    }

    pub fn is_recording(&self) -> bool {
        *self.state.lock().unwrap() == RecordingState::Recording
    }

    pub fn get_state(&self) -> RecordingState {
        *self.state.lock().unwrap()
    }

    pub fn save_to_file(&self, path: &str) -> Result<()> {
        let audio_data = self.audio_data.lock().unwrap();
        
        if audio_data.is_empty() {
            return Err(anyhow::anyhow!("No audio data to save"));
        }

        let spec = WavSpec {
            channels: self.channels,
            sample_rate: self.sample_rate,
            bits_per_sample: 32,
            sample_format: hound::SampleFormat::Float,
        };

        let mut writer = WavWriter::create(path, spec)?;

        for &sample in audio_data.iter() {
            writer.write_sample(sample)?;
        }

        writer.finalize()?;
        Ok(())
    }

    pub fn get_audio_bytes(&self) -> Result<Vec<u8>> {
        let audio_data = self.audio_data.lock().unwrap();
        
        if audio_data.is_empty() {
            return Err(anyhow::anyhow!("No audio data available"));
        }

        let spec = WavSpec {
            channels: self.channels,
            sample_rate: self.sample_rate,
            bits_per_sample: 32,
            sample_format: hound::SampleFormat::Float,
        };

        let mut buffer = Vec::new();
        {
            let mut writer = WavWriter::new(std::io::Cursor::new(&mut buffer), spec)?;
            
            for &sample in audio_data.iter() {
                writer.write_sample(sample)?;
            }
            
            writer.finalize()?;
        }

        Ok(buffer)
    }

    pub fn get_duration(&self) -> f64 {
        let audio_data = self.audio_data.lock().unwrap();
        if audio_data.is_empty() {
            return 0.0;
        }

        let total_frames = audio_data.len() as f64 / self.channels as f64;
        total_frames / self.sample_rate as f64
    }

    fn get_stream_config(&self, device: &Device) -> Result<StreamConfig> {
        let supported_configs_range = device
            .supported_input_configs()
            .context("Error querying input configs")?;

        // Try to find a config that matches our desired sample rate
        for supported_config in supported_configs_range {
            if supported_config.channels() == self.channels
                && supported_config.min_sample_rate().0 <= self.sample_rate
                && supported_config.max_sample_rate().0 >= self.sample_rate
            {
                return Ok(StreamConfig {
                    channels: self.channels,
                    sample_rate: cpal::SampleRate(self.sample_rate),
                    buffer_size: cpal::BufferSize::Default,
                });
            }
        }

        // If no exact match, use the default config
        let default_config = device
            .default_input_config()
            .context("No default input config")?;

        Ok(StreamConfig {
            channels: self.channels.min(default_config.channels()),
            sample_rate: cpal::SampleRate(self.sample_rate),
            buffer_size: cpal::BufferSize::Default,
        })
    }
}
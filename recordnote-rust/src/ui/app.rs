use super::recording_widget::RecordingWidget;
use druid::widget::{Button, Flex, Label, Scroll, Split, TextBox};
use druid::{
    AppLauncher, Color, Data, Env, Lens, Widget, WidgetExt, WindowDesc,
};

// Custom events for async operations
#[derive(Debug, Clone)]
pub enum AppEvent {
    UpdateDuration(f64),
    RecordingComplete,
    TranscriptionComplete(String),
    ProcessingError(String),
}

#[derive(Clone, Data, Lens)]
pub struct AppState {
    pub meeting_title: String,
    pub recording_state: String,
    pub duration: String,
    pub status: String,
    pub results_text: String,
    pub model_size: String,
    pub is_recording: bool,
    pub is_processing: bool,
    pub can_download: bool,
    pub formatted_minutes: String,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            meeting_title: String::new(),
            recording_state: "stopped".to_string(),
            duration: "録音時間: 0.0秒".to_string(),
            status: "録音待機中".to_string(),
            results_text: "録音を開始して音声を議事録に変換してください。".to_string(),
            model_size: "base".to_string(),
            is_recording: false,
            is_processing: false,
            can_download: false,
            formatted_minutes: String::new(),
        }
    }
}

pub struct RecordNoteApp;

impl RecordNoteApp {
    pub fn new() -> anyhow::Result<Self> {
        Ok(Self)
    }

    pub fn launch(self) -> anyhow::Result<()> {
        let main_window = WindowDesc::new(self.build_ui())
            .title("RecordNote - 議事録作成アプリ")
            .window_size((1200.0, 800.0))
            .resizable(true);

        let initial_state = AppState::new();

        AppLauncher::with_window(main_window)
            .launch(initial_state)
            .expect("Failed to launch application");

        Ok(())
    }

    fn build_ui(&self) -> impl Widget<AppState> {
        let left_panel = self.build_left_panel();
        let right_panel = self.build_right_panel();

        let ui = Split::columns(left_panel, right_panel)
            .split_point(0.4)
            .bar_size(2.0)
            .min_size(400.0, 400.0)
            .solid_bar(true);

        RecordingWidget::new(ui)
    }

    fn build_left_panel(&self) -> impl Widget<AppState> {
        let title = Label::new("録音コントロール")
            .with_text_size(24.0)
            .with_text_color(Color::rgb8(33, 33, 33));

        let meeting_title_input = TextBox::new()
            .with_placeholder("会議名（オプション）")
            .lens(AppState::meeting_title)
            .fix_height(40.0);

        let status_label = Label::new(|data: &AppState, _env: &Env| data.status.clone())
            .with_text_size(14.0)
            .with_text_color(Color::rgb8(117, 117, 117));

        let duration_label = Label::new(|data: &AppState, _env: &Env| data.duration.clone())
            .with_text_size(14.0)
            .with_text_color(Color::rgb8(117, 117, 117));

        let record_button = Button::new("🔴 録音開始")
            .on_click(|ctx, data: &mut AppState, _env| {
                if !data.is_recording && !data.is_processing {
                    data.is_recording = true;
                    data.recording_state = "recording".to_string();
                    data.status = "🎤 録音中...".to_string();
                    
                    // Send command to start recording
                    ctx.submit_command(druid::commands::SHOW_WINDOW);
                }
            })
            .disabled_if(|data, _env| data.is_recording || data.is_processing)
            .fix_height(48.0);

        let stop_button = Button::new("⏹️ 録音停止")
            .on_click(|ctx, data: &mut AppState, _env| {
                if data.is_recording {
                    data.is_recording = false;
                    data.is_processing = true;
                    data.recording_state = "processing".to_string();
                    data.status = "🔄 音声を処理中...".to_string();
                    
                    // Send command to stop recording and process
                    ctx.submit_command(druid::commands::SHOW_WINDOW);
                }
            })
            .disabled_if(|data, _env| !data.is_recording)
            .fix_height(48.0);

        let model_label = Label::new("Whisperモデル")
            .with_text_size(14.0);

        let model_selector = Label::new(|data: &AppState, _env: &Env| {
            format!("Model: {}", data.model_size)
        })
        .with_text_size(12.0)
        .with_text_color(Color::rgb8(117, 117, 117));

        Flex::column()
            .with_child(title)
            .with_spacer(20.0)
            .with_child(meeting_title_input)
            .with_spacer(20.0)
            .with_child(status_label)
            .with_spacer(10.0)
            .with_child(duration_label)
            .with_spacer(20.0)
            .with_child(record_button)
            .with_spacer(10.0)
            .with_child(stop_button)
            .with_spacer(30.0)
            .with_child(model_label)
            .with_spacer(10.0)
            .with_child(model_selector)
            .with_spacer(20.0)
            .padding(20.0)
            .background(Color::rgb8(248, 249, 250))
    }

    fn build_right_panel(&self) -> impl Widget<AppState> {
        let title = Label::new("結果")
            .with_text_size(24.0)
            .with_text_color(Color::rgb8(33, 33, 33));

        let results_area = Scroll::new(
            TextBox::multiline()
                .with_text_size(16.0)
                .lens(AppState::results_text)
                .disabled_if(|_data, _env| true) // Read-only
        )
        .vertical();

        let download_button = Button::new("📄 議事録をダウンロード")
            .on_click(|_ctx, data: &mut AppState, _env| {
                if data.can_download && !data.formatted_minutes.is_empty() {
                    // Generate filename with timestamp
                    use chrono::Local;
                    let timestamp = Local::now().format("%Y%m%d_%H%M%S");
                    let filename = format!("meeting_minutes_{}.md", timestamp);
                    
                    // For demo purposes, save to current directory
                    match std::fs::write(&filename, &data.formatted_minutes) {
                        Ok(()) => {
                            log::info!("議事録を保存しました: {}", filename);
                            // In a real app, you'd show a success dialog
                        }
                        Err(e) => {
                            log::error!("ファイル保存エラー: {}", e);
                            // In a real app, you'd show an error dialog
                        }
                    }
                }
            })
            .disabled_if(|data, _env| !data.can_download)
            .fix_width(200.0)
            .fix_height(48.0);

        let new_recording_button = Button::new("🔄 新しい録音を開始")
            .on_click(|_ctx, data: &mut AppState, _env| {
                data.recording_state = "stopped".to_string();
                data.status = "録音待機中".to_string();
                data.results_text = "録音を開始して音声を議事録に変換してください。".to_string();
                data.meeting_title.clear();
                data.duration = "録音時間: 0.0秒".to_string();
                data.is_recording = false;
                data.is_processing = false;
                data.can_download = false;
                data.formatted_minutes.clear();
            })
            .disabled_if(|data, _env| data.is_recording || data.is_processing)
            .fix_width(200.0)
            .fix_height(48.0);

        let button_row = Flex::row()
            .with_child(download_button)
            .with_spacer(10.0)
            .with_child(new_recording_button);

        Flex::column()
            .with_child(title)
            .with_spacer(20.0)
            .with_flex_child(results_area, 1.0)
            .with_spacer(20.0)
            .with_child(button_row)
            .padding(20.0)
            .background(Color::WHITE)
    }
}

impl Default for RecordNoteApp {
    fn default() -> Self {
        Self::new().unwrap()
    }
}
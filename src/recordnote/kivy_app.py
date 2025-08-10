"""Main Kivy application for RecordNote."""

import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import japanize_kivy
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.textfield import MDTextField
from plyer import filechooser

from .formatter import MinutesFormatter
from .recorder import AudioRecorder
from .transcriber import SpeechTranscriber


class RecordNoteKivyApp(MDApp):
    """Main Kivy application class for RecordNote."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the RecordNote Kivy application."""
        super().__init__(**kwargs)

        # Core components
        self.recorder = AudioRecorder()
        self.transcriber = SpeechTranscriber()
        self.formatter = MinutesFormatter()

        # State management
        self.recording_state = "stopped"  # stopped, recording, processing, completed
        self.transcribed_text = ""
        self.formatted_minutes = ""

        # UI components (will be set in build method)
        self.meeting_title_input: Optional[MDTextField] = None
        self.record_button: Optional[MDButton] = None
        self.stop_button: Optional[MDButton] = None
        self.duration_label: Optional[MDLabel] = None
        self.status_label: Optional[MDLabel] = None
        self.model_spinner: Optional[Spinner] = None
        self.results_text: Optional[TextInput] = None
        self.download_button: Optional[MDButton] = None
        self.new_recording_button: Optional[MDButton] = None
        self.progress_spinner: Optional[MDCircularProgressIndicator] = None

        # Scheduled events
        self.duration_update_event: Optional[Any] = None

    def build(self) -> BoxLayout:
        """Build the main UI layout."""
        # Configure KivyMD theme
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"  # Material Design 3

        # Set window properties
        Window.size = (1200, 800)
        Window.minimum_width = 800
        Window.minimum_height = 600
        self.title = "RecordNote - 議事録作成アプリ"

        # Main layout
        main_layout = BoxLayout(orientation="horizontal", padding=20, spacing=20)

        # Left panel - Recording controls
        left_panel = self._create_left_panel()
        main_layout.add_widget(left_panel)

        # Right panel - Results
        right_panel = self._create_right_panel()
        main_layout.add_widget(right_panel)

        return main_layout

    def _create_left_panel(self) -> MDCard:
        """Create the left panel with recording controls."""
        card = MDCard(size_hint=(0.4, 1), elevation=2, padding=20, spacing=15)

        layout = MDBoxLayout(orientation="vertical", spacing=20, adaptive_height=True)

        # Title
        title_label = MDLabel(
            text="録音コントロール",
            theme_text_color="Primary",
            font_style="Headline",
            size_hint_y=None,
            height="48dp",
        )
        layout.add_widget(title_label)

        # Meeting title input
        self.meeting_title_input = MDTextField(
            hint_text="会議名（オプション）",
            size_hint_y=None,
            height="48dp",
        )
        layout.add_widget(self.meeting_title_input)

        # Recording controls section
        controls_layout = self._create_recording_controls()
        layout.add_widget(controls_layout)

        # Settings section
        settings_layout = self._create_settings_section()
        layout.add_widget(settings_layout)

        card.add_widget(layout)
        return card

    def _create_recording_controls(self) -> MDBoxLayout:
        """Create recording controls section."""
        layout = MDBoxLayout(
            orientation="vertical", spacing=15, size_hint_y=None, height="200dp"
        )

        # Status label
        self.status_label = MDLabel(
            text="録音待機中",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height="40dp",
        )
        layout.add_widget(self.status_label)

        # Duration label
        self.duration_label = MDLabel(
            text="録音時間: 0.0秒",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height="40dp",
        )
        layout.add_widget(self.duration_label)

        # Record button
        self.record_button = MDButton(size_hint_y=None, height="48dp")
        self.record_button.add_widget(MDButtonText(text="🔴 録音開始"))
        self.record_button.bind(on_release=self.start_recording)
        layout.add_widget(self.record_button)

        # Stop button (initially hidden)
        self.stop_button = MDButton(
            size_hint_y=None,
            height="48dp",
            disabled=True,
        )
        self.stop_button.add_widget(MDButtonText(text="⏹️ 録音停止"))
        self.stop_button.bind(on_release=self.stop_recording)
        layout.add_widget(self.stop_button)

        return layout

    def _create_settings_section(self) -> MDBoxLayout:
        """Create settings section."""
        layout = MDBoxLayout(
            orientation="vertical", spacing=15, size_hint_y=None, height="150dp"
        )

        # Settings title
        settings_label = MDLabel(
            text="設定",
            theme_text_color="Primary",
            font_style="Title",
            size_hint_y=None,
            height="40dp",
        )
        layout.add_widget(settings_label)

        # Model selection
        model_layout = BoxLayout(
            orientation="vertical", size_hint_y=None, height="80dp", spacing=5
        )

        model_label = Label(text="Whisperモデル", size_hint_y=None, height="30dp")
        model_layout.add_widget(model_label)

        self.model_spinner = Spinner(
            text="base",
            values=["tiny", "base", "small", "medium", "large"],
            size_hint_y=None,
            height="40dp",
        )
        self.model_spinner.bind(text=self.on_model_change)
        model_layout.add_widget(self.model_spinner)

        layout.add_widget(model_layout)

        return layout

    def _create_right_panel(self) -> MDCard:
        """Create the right panel with results."""
        card = MDCard(size_hint=(0.6, 1), elevation=2, padding=20, spacing=15)

        layout = MDBoxLayout(orientation="vertical", spacing=20)

        # Title
        title_label = MDLabel(
            text="結果",
            theme_text_color="Primary",
            font_style="Headline",
            size_hint_y=None,
            height="48dp",
        )
        layout.add_widget(title_label)

        # Results text area
        scroll = ScrollView(size_hint=(1, 0.8))
        self.results_text = TextInput(
            text="録音を開始して音声を議事録に変換してください。",
            readonly=True,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            multiline=True,
            font_size=16,  # Increased font size for better readability
        )
        scroll.add_widget(self.results_text)
        layout.add_widget(scroll)

        # Action buttons layout
        buttons_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height="48dp",
            adaptive_width=True,
        )

        # Download button (initially disabled)
        self.download_button = MDButton(
            disabled=True,
            size_hint_x=None,
            width="200dp",
        )
        self.download_button.add_widget(MDButtonText(text="📄 議事録をダウンロード"))
        self.download_button.bind(on_release=self.download_minutes)
        buttons_layout.add_widget(self.download_button)

        # New recording button (initially disabled)
        self.new_recording_button = MDButton(
            disabled=True,
            size_hint_x=None,
            width="200dp",
        )
        self.new_recording_button.add_widget(MDButtonText(text="🔄 新しい録音を開始"))
        self.new_recording_button.bind(on_release=self.start_new_recording)
        buttons_layout.add_widget(self.new_recording_button)

        layout.add_widget(buttons_layout)

        # Progress spinner (initially hidden)
        self.progress_spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={"center_x": 0.5},
            opacity=0,
        )
        layout.add_widget(self.progress_spinner)

        card.add_widget(layout)
        return card

    def start_recording(self, instance: Any) -> None:
        """Start audio recording."""
        try:
            self.recorder.start_recording()
            self.recording_state = "recording"
            self._update_ui_for_recording_state()

            # Start updating duration
            self.duration_update_event = Clock.schedule_interval(
                self._update_duration, 0.1
            )

        except Exception as e:
            self._show_error(f"録音開始エラー: {e}")

    def stop_recording(self, instance: Any) -> None:
        """Stop audio recording and process."""
        try:
            self.recorder.stop_recording()
            self.recording_state = "processing"
            self._update_ui_for_recording_state()

            # Stop duration updates
            if self.duration_update_event:
                Clock.unschedule(self.duration_update_event)
                self.duration_update_event = None

            # Start processing in background thread
            threading.Thread(target=self._process_recording, daemon=True).start()

        except Exception as e:
            self._show_error(f"録音停止エラー: {e}")

    def _process_recording(self) -> None:
        """Process the recorded audio and generate minutes."""
        try:
            # Get audio data
            audio_bytes = self.recorder.get_audio_bytes()

            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_status("音声を認識中..."), 0)

            # Transcribe audio
            transcription_result = self.transcriber.transcribe_bytes(audio_bytes)
            self.transcribed_text = transcription_result["text"]

            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_status("議事録を整形中..."), 0)

            # Format minutes
            meeting_title = (
                self.meeting_title_input.text
                if self.meeting_title_input and self.meeting_title_input.text.strip()
                else "会議録"
            )
            formatted_minutes = self.formatter.format_minutes(
                transcription_result, meeting_title
            )

            self.formatted_minutes = formatted_minutes
            self.recording_state = "completed"

            # Update UI on main thread
            Clock.schedule_once(self._update_ui_after_processing, 0)

        except Exception as ex:
            Clock.schedule_once(lambda dt: self._show_error(f"処理エラー: {ex}"), 0)
            self.recording_state = "stopped"
            Clock.schedule_once(lambda dt: self._update_ui_for_recording_state(), 0)

    def _update_ui_after_processing(self, dt: float) -> None:
        """Update UI after processing is complete."""
        if self.results_text:
            self.results_text.text = self.formatted_minutes

        # Get stats and show completion message
        try:
            transcription_result = {"text": self.transcribed_text, "segments": []}
            stats = self.formatter.get_summary_stats(transcription_result)
            status_msg = (
                f"✅ 完了! 文字数: {stats['character_count']}, " f"単語数: {stats['word_count']}"
            )
            self._update_status(status_msg)
        except Exception:
            self._update_status("✅ 処理完了!")

        self._update_ui_for_recording_state()

    def _update_duration(self, dt: float) -> None:
        """Update the recording duration display."""
        if self.recorder.is_recording() and self.duration_label:
            duration = self.recorder.get_duration()
            self.duration_label.text = f"録音時間: {duration:.1f}秒"

    def _update_ui_for_recording_state(self) -> None:
        """Update UI based on current recording state."""
        if self.recording_state == "stopped":
            if self.record_button:
                self.record_button.disabled = False
            if self.stop_button:
                self.stop_button.disabled = True
            if self.progress_spinner:
                self.progress_spinner.opacity = 0
            if self.download_button:
                self.download_button.disabled = True
            if self.new_recording_button:
                self.new_recording_button.disabled = True
            self._update_status("録音待機中")

        elif self.recording_state == "recording":
            if self.record_button:
                self.record_button.disabled = True
            if self.stop_button:
                self.stop_button.disabled = False
            if self.progress_spinner:
                self.progress_spinner.opacity = 0
            self._update_status("🎤 録音中...")

        elif self.recording_state == "processing":
            if self.record_button:
                self.record_button.disabled = True
            if self.stop_button:
                self.stop_button.disabled = True
            if self.progress_spinner:
                self.progress_spinner.opacity = 1
            self._update_status("🔄 音声を処理中...")

        elif self.recording_state == "completed":
            if self.record_button:
                self.record_button.disabled = False
            if self.stop_button:
                self.stop_button.disabled = True
            if self.progress_spinner:
                self.progress_spinner.opacity = 0
            if self.download_button:
                self.download_button.disabled = False
            if self.new_recording_button:
                self.new_recording_button.disabled = False

    def _update_status(self, status: str) -> None:
        """Update the status label."""
        if self.status_label:
            self.status_label.text = status

    def on_model_change(self, spinner: Any, text: str) -> None:
        """Handle model selection change."""
        if text != self.transcriber.model_size:
            self.transcriber = SpeechTranscriber(text)

    def download_minutes(self, instance: Any) -> None:
        """Download the formatted minutes as a file."""
        if not self.formatted_minutes:
            return

        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_minutes_{timestamp}.md"

            # Open file chooser
            path = filechooser.save_file(
                title="議事録を保存",
                filters=[("Markdown files", "*.md"), ("All files", "*.*")],
                path=filename,
            )

            if path:
                # Save the file
                save_path = Path(path[0]) if isinstance(path, list) else Path(path)
                self.formatter.export_to_file(self.formatted_minutes, str(save_path))
                self._show_info(f"ファイルを保存しました: {save_path.name}")

        except Exception as e:
            self._show_error(f"ファイル保存エラー: {e}")

    def start_new_recording(self, instance: Any) -> None:
        """Reset for a new recording."""
        self.recording_state = "stopped"
        self.transcribed_text = ""
        self.formatted_minutes = ""

        if self.results_text:
            self.results_text.text = "録音を開始して音声を議事録に変換してください。"
        if self.meeting_title_input:
            self.meeting_title_input.text = ""
        if self.duration_label:
            self.duration_label.text = "録音時間: 0.0秒"

        self._update_ui_for_recording_state()

    def _show_error(self, message: str) -> None:
        """Show an error popup."""
        popup = Popup(
            title="エラー",
            content=Label(text=message),
            size_hint=(0.6, 0.4),
        )
        popup.open()

    def _show_info(self, message: str) -> None:
        """Show an info popup."""
        popup = Popup(
            title="情報",
            content=Label(text=message),
            size_hint=(0.6, 0.4),
        )
        popup.open()


def run_kivy_app() -> None:
    """Run the Kivy application."""
    app = RecordNoteKivyApp()
    app.run()


if __name__ == "__main__":
    run_kivy_app()

"""Main Streamlit application for RecordNote."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from .formatter import MinutesFormatter
from .recorder import AudioRecorder
from .transcriber import SpeechTranscriber


class RecordNoteApp:
    """Main application class for RecordNote."""

    def __init__(self) -> None:
        """Initialize the RecordNote application."""
        self.recorder = AudioRecorder()
        self.transcriber = SpeechTranscriber()
        self.formatter = MinutesFormatter()

    def run(self) -> None:
        """Run the Streamlit application."""
        st.set_page_config(
            page_title="RecordNote - 議事録作成アプリ",
            page_icon="🎤",
            layout="wide",
        )

        st.title("🎤 RecordNote - 議事録作成アプリ")
        st.markdown("日本語音声を録音して、自動的に議事録を作成します。")

        # Initialize session state
        if "recording_state" not in st.session_state:
            st.session_state.recording_state = "stopped"
        if "transcribed_text" not in st.session_state:
            st.session_state.transcribed_text = ""
        if "formatted_minutes" not in st.session_state:
            st.session_state.formatted_minutes = ""

        # Main interface
        col1, col2 = st.columns([1, 2])

        with col1:
            self._render_recording_panel()

        with col2:
            self._render_results_panel()

    def _render_recording_panel(self) -> None:
        """Render the recording control panel."""
        st.subheader("録音コントロール")

        # Meeting title input
        meeting_title = st.text_input("会議名（オプション）", placeholder="例: 週次定例会議")

        # Recording controls
        if st.session_state.recording_state == "stopped":
            if st.button("🔴 録音開始", type="primary", use_container_width=True):
                try:
                    self.recorder.start_recording()
                    st.session_state.recording_state = "recording"
                    st.rerun()
                except Exception as e:
                    st.error(f"録音開始エラー: {e}")

        elif st.session_state.recording_state == "recording":
            # Show recording status
            st.success("🎤 録音中...")

            # Display recording duration
            if self.recorder.is_recording():
                duration = self.recorder.get_duration()
                st.metric("録音時間", f"{duration:.1f}秒")

            if st.button("⏹️ 録音停止", type="secondary", use_container_width=True):
                try:
                    self.recorder.stop_recording()
                    st.session_state.recording_state = "processing"
                    st.rerun()
                except Exception as e:
                    st.error(f"録音停止エラー: {e}")

        elif st.session_state.recording_state == "processing":
            st.info("🔄 音声を処理中...")
            self._process_recording(meeting_title)

        # Model settings
        st.subheader("設定")
        model_size = st.selectbox(
            "Whisperモデル",
            ["tiny", "base", "small", "medium", "large"],
            index=1,
            help="大きなモデルほど精度が高いですが、処理時間が長くなります。",
        )

        if model_size != self.transcriber.model_size:
            self.transcriber = SpeechTranscriber(model_size)

        # Display model info
        model_info = self.transcriber.get_model_info()
        st.caption(f"モデル: {model_info['model_size']} | "
                  f"読み込み済み: {'Yes' if model_info['loaded'] else 'No'}")

    def _render_results_panel(self) -> None:
        """Render the results display panel."""
        st.subheader("結果")

        if st.session_state.formatted_minutes:
            # Display formatted minutes
            st.markdown("### 生成された議事録")
            st.markdown(st.session_state.formatted_minutes)

            # Download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_minutes_{timestamp}.md"

            st.download_button(
                label="📄 議事録をダウンロード",
                data=st.session_state.formatted_minutes,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True,
            )

            # New recording button
            if st.button("🔄 新しい録音を開始", use_container_width=True):
                self._reset_session()
                st.rerun()

        elif st.session_state.transcribed_text:
            st.info("音声認識は完了しましたが、議事録の整形中です...")

        else:
            st.info("録音を開始して音声を議事録に変換してください。")

    def _process_recording(self, meeting_title: str) -> None:
        """Process the recorded audio and generate minutes.

        Args:
            meeting_title: Title for the meeting minutes
        """
        try:
            # Get audio data
            audio_bytes = self.recorder.get_audio_bytes()

            # Transcribe audio
            with st.spinner("音声を認識中..."):
                transcription_result = self.transcriber.transcribe_bytes(audio_bytes)

            st.session_state.transcribed_text = transcription_result["text"]

            # Format minutes
            with st.spinner("議事録を整形中..."):
                formatted_minutes = self.formatter.format_minutes(
                    transcription_result, meeting_title or "会議録"
                )

            st.session_state.formatted_minutes = formatted_minutes
            st.session_state.recording_state = "completed"

            # Show summary stats
            stats = self.formatter.get_summary_stats(transcription_result)
            st.success(
                f"✅ 完了! 文字数: {stats['character_count']}, "
                f"単語数: {stats['word_count']}, "
                f"時間: {stats['total_duration']:.1f}秒"
            )

        except Exception as e:
            st.error(f"処理エラー: {e}")
            st.session_state.recording_state = "stopped"

        st.rerun()

    def _reset_session(self) -> None:
        """Reset the session state for a new recording."""
        st.session_state.recording_state = "stopped"
        st.session_state.transcribed_text = ""
        st.session_state.formatted_minutes = ""


def main() -> None:
    """Main entry point for the Streamlit app."""
    app = RecordNoteApp()
    app.run()


if __name__ == "__main__":
    main()
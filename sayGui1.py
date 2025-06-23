import sys
import asyncio
import subprocess
import shutil
import threading # Still using threading for asyncio bridge

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QComboBox, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject

import edge_tts

# --- Configuration ---
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
# DEFAULT_VOICE = "zh-CN-YunxiNeural"
# DEFAULT_VOICE = "zh-HK-HiuGaaiNeural"
# DEFAULT_VOICE = "zh-TW-HsiaoChenNeural"

# --- Helper to find player ---
def find_player():
    if shutil.which("mpv"):
        return ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"]
    elif shutil.which("ffplay"):
        return ["ffplay", "-autoexit", "-nodisp", "-loglevel", "error", "-i", "pipe:0"]
    return None

PLAYER_COMMAND = find_player()

# --- Worker for Voice Loading ---
class VoiceLoader(QObject):
    finished = Signal(list, str)  # list of voices, error message string

    def run(self):
        try:
            # Run the async function in a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            available_voices = loop.run_until_complete(edge_tts.list_voices())
            loop.close()

            chinese_voices = [v for v in available_voices if v['Locale'].startswith('zh-')]

            def sort_key(voice):
                name = voice['ShortName']
                if name == DEFAULT_VOICE: return "0"
                return name
            chinese_voices.sort(key=sort_key)

            self.finished.emit(chinese_voices, "")
        except Exception as e:
            self.finished.emit([], f"Could not load voices: {e}")

# --- Worker for TTS ---
class TTSWorker(QObject):
    finished = Signal(bool, str) # success (bool), error_message (str)
    status_update = Signal(str)

    def __init__(self, text, voice_short_name):
        super().__init__()
        self.text = text
        self.voice_short_name = voice_short_name
        self.player_process = None


    async def _speak_async_edge(self):
        self.status_update.emit(f"Generating audio with {self.voice_short_name}...")
        communicate = edge_tts.Communicate(self.text, self.voice_short_name)

        self.player_process = subprocess.Popen(PLAYER_COMMAND, stdin=subprocess.PIPE)
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    if self.player_process.stdin:
                        self.player_process.stdin.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    pass # Placeholder for potential future use
            if self.player_process.stdin:
                self.player_process.stdin.close()
            ret_code = self.player_process.wait()
            if ret_code != 0:
                raise RuntimeError(f"Player exited with code {ret_code}")
            return True, ""
        except Exception as e:
            if self.player_process and self.player_process.poll() is None:
                self.player_process.terminate() # Try to terminate
                try:
                    self.player_process.wait(timeout=1) # Wait a bit
                except subprocess.TimeoutExpired:
                    self.player_process.kill() # Force kill
            return False, f"Error during TTS/playback: {e}"
        finally:
            self.player_process = None


    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(self._speak_async_edge())
            loop.close()
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"TTS Worker critical error: {e}")


class SpeakApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chinese Text-to-Speech (Edge TTS with PySide6)")
        self.setGeometry(100, 100, 600, 450)

        if not PLAYER_COMMAND:
            QMessageBox.critical(self, "Error", "No suitable audio player (mpv or ffplay) found. Please install one.")
            sys.exit(1) # Or self.close() if app instance already exists

        self.current_tts_thread = None
        self.current_tts_worker = None

        self._setup_ui()
        self._load_voices()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Voice selection
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Select Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(250)
        self.voice_combo.setEnabled(False)
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        main_layout.addLayout(voice_layout)

        # Text input
        text_input_label = QLabel("Enter Chinese text:")
        main_layout.addWidget(text_input_label)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("你好，世界！")
        self.text_input.setPlainText("你好，世界！这是一个测试。") # Default text
        main_layout.addWidget(self.text_input)

        # Speak button
        self.speak_button = QPushButton("Speak")
        self.speak_button.setEnabled(False)
        self.speak_button.clicked.connect(self.on_speak_button_click)
        main_layout.addWidget(self.speak_button, alignment=Qt.AlignCenter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Status: Initializing...")

    def _load_voices(self):
        self.status_bar.showMessage("Status: Loading voices...")
        self.speak_button.setEnabled(False)
        self.voice_combo.setEnabled(False)

        self.voice_thread = QThread()
        self.voice_loader = VoiceLoader()
        self.voice_loader.moveToThread(self.voice_thread)

        self.voice_loader.finished.connect(self._on_voices_loaded)
        self.voice_loader.finished.connect(self.voice_thread.quit)
        self.voice_loader.finished.connect(self.voice_loader.deleteLater)
        self.voice_thread.finished.connect(self.voice_thread.deleteLater)
        self.voice_thread.started.connect(self.voice_loader.run)

        self.voice_thread.start()

    def _on_voices_loaded(self, voices_data, error_msg):
        if error_msg:
            QMessageBox.critical(self, "Voice Loading Error", error_msg)
            self.status_bar.showMessage(f"Status: Error loading voices. {error_msg}")
            return

        if not voices_data:
            QMessageBox.warning(self, "No Voices", "No Chinese voices found with edge-tts.")
            self.status_bar.showMessage("Status: No Chinese voices available.")
            return

        self.voices_map = {} # To store ShortName -> full data
        default_voice_idx = 0
        for i, v_data in enumerate(voices_data):
            display_name = f"{v_data['ShortName']} ({v_data['Gender']})"
            self.voice_combo.addItem(display_name, v_data['ShortName'])
            self.voices_map[v_data['ShortName']] = v_data
            if v_data['ShortName'] == DEFAULT_VOICE:
                default_voice_idx = i

        self.voice_combo.setCurrentIndex(default_voice_idx)
        self.status_bar.showMessage("Status: Ready")
        self.speak_button.setEnabled(True)
        self.voice_combo.setEnabled(True)

    def on_speak_button_click(self):
        text_to_speak = self.text_input.toPlainText().strip()
        selected_voice_short_name = self.voice_combo.currentData() # UserData is ShortName

        if not text_to_speak:
            QMessageBox.warning(self, "Input Error", "Please enter some text to speak.")
            return
        if not selected_voice_short_name:
            QMessageBox.warning(self, "Input Error", "Please select a voice.")
            return

        self.speak_button.setEnabled(False)
        self.voice_combo.setEnabled(False) # Disable during speech
        self.status_bar.showMessage(f"Status: Preparing to speak with {selected_voice_short_name}...")

        # Stop previous TTS thread if any is still running somehow (should not happen with button disable)
        if self.current_tts_thread and self.current_tts_thread.isRunning():
            print("Warning: Previous TTS thread still running. Attempting to terminate.")
            if self.current_tts_worker and self.current_tts_worker.player_process:
                self.current_tts_worker.player_process.kill() # Kill the player
            self.current_tts_thread.quit()
            self.current_tts_thread.wait(1000) # wait 1 sec

        self.current_tts_thread = QThread(self) # Parent to main window for auto-cleanup
        self.current_tts_worker = TTSWorker(text_to_speak, selected_voice_short_name)
        self.current_tts_worker.moveToThread(self.current_tts_thread)

        self.current_tts_worker.status_update.connect(self.status_bar.showMessage)
        self.current_tts_worker.finished.connect(self._on_speak_finished)
        # Clean up thread and worker
        self.current_tts_worker.finished.connect(self.current_tts_thread.quit)
        # self.current_tts_worker.finished.connect(self.current_tts_worker.deleteLater) # Careful with this
        self.current_tts_thread.finished.connect(self.current_tts_thread.deleteLater) # This is good
        self.current_tts_thread.started.connect(self.current_tts_worker.run)

        self.current_tts_thread.start()

    def _on_speak_finished(self, success, message):
        self.speak_button.setEnabled(True)
        self.voice_combo.setEnabled(True)
        if success:
            self.status_bar.showMessage("Status: Ready")
        else:
            self.status_bar.showMessage(f"Status: Error - {message}")
            if message: # Only show popup if there's a specific message
                QMessageBox.critical(self, "TTS Error", message)
            else:
                QMessageBox.critical(self, "TTS Error", "An unknown error occurred during text-to-speech.")

        # Worker and thread should be cleaned up by connections, but ensure references are cleared
        self.current_tts_worker = None
        self.current_tts_thread = None


    def closeEvent(self, event):
        # Clean up worker thread if it's running
        if self.current_tts_thread and self.current_tts_thread.isRunning():
            self.status_bar.showMessage("Status: Closing, stopping TTS...")
            if self.current_tts_worker and self.current_tts_worker.player_process:
                print("Killing player process on close.")
                # Send EOF to player stdin, then terminate/kill
                try:
                    if self.current_tts_worker.player_process.stdin:
                        self.current_tts_worker.player_process.stdin.close()
                except Exception:
                    pass # May already be closed or broken
                self.current_tts_worker.player_process.terminate()
                try:
                    self.current_tts_worker.player_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.current_tts_worker.player_process.kill()

            self.current_tts_thread.quit() # Request thread to quit
            if not self.current_tts_thread.wait(1000): # Wait up to 1 second
                print("TTS thread did not quit gracefully, terminating.")
                self.current_tts_thread.terminate() # Force terminate
                self.current_tts_thread.wait() # Wait for termination
        super().closeEvent(event)


def main():
    # Recommended for Qt:
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = SpeakApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
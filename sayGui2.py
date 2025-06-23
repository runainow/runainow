import sys
import asyncio
import subprocess
import shutil
import os
import signal
import time # For debugging

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QComboBox, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot

import edge_tts

# --- Configuration ---
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

def find_player():
    # ... (same as before)
    if shutil.which("mpv"):
        return ["mpv", "--no-cache", "--no-terminal", "--idle=yes", "--", "fd://0"]
    elif shutil.which("ffplay"):
        return ["ffplay", "-autoexit", "-nodisp", "-loglevel", "error", "-i", "pipe:0"]
    return None

PLAYER_COMMAND = find_player()

class VoiceLoader(QObject):
    finished = Signal(list, str)

    def __init__(self, parent=None): # Good practice to add parent for QObjects
        super().__init__(parent)
        print("[VoiceLoader] Initialized")

    def run(self):
        print("[VoiceLoader] run() called")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("[VoiceLoader] asyncio loop created and set.")
            
            print("[VoiceLoader] Attempting to run edge_tts.list_voices()...")
            start_time = time.time()
            available_voices = loop.run_until_complete(edge_tts.list_voices())
            end_time = time.time()
            print(f"[VoiceLoader] edge_tts.list_voices() completed in {end_time - start_time:.2f} seconds. Found {len(available_voices)} voices.")

            chinese_voices = [v for v in available_voices if v['Locale'].startswith('zh-')]
            print(f"[VoiceLoader] Filtered to {len(chinese_voices)} Chinese voices.")

            def sort_key(voice):
                name = voice['ShortName']
                if name == DEFAULT_VOICE: return "0"
                return name
            chinese_voices.sort(key=sort_key)
            
            print("[VoiceLoader] Emitting finished signal with voice data.")
            self.finished.emit(chinese_voices, "")
            print("[VoiceLoader] Finished signal emitted.")

        except Exception as e:
            print(f"[VoiceLoader] Exception in run(): {e}")
            import traceback
            traceback.print_exc() # Print full traceback
            self.finished.emit([], f"Could not load voices: {e}")
            print(f"[VoiceLoader] Finished signal emitted with error: {e}")
        finally:
            if 'loop' in locals() and loop.is_running(): # Ensure loop is closed if it was running
                print("[VoiceLoader] Closing asyncio loop in finally block.")
                loop.close()
            print("[VoiceLoader] run() finished execution.")

# TTSWorker class (same as before)
class TTSWorker(QObject):
    # ... (same content as your previous correct version)
    finished = Signal(bool, str)
    status_update = Signal(str)
    player_started = Signal(int)
    playback_officially_ended = Signal()

    def __init__(self, text, voice_short_name):
        super().__init__()
        self.text_to_speak = text
        self.voice_short_name = voice_short_name
        self.player_process = None
        self.player_pid = None
        self._is_paused_by_user = False
        self._stop_requested = False

    async def _speak_async_edge(self):
        self.status_update.emit(f"Generating audio with {self.voice_short_name}...")
        communicate = edge_tts.Communicate(self.text_to_speak, self.voice_short_name)
        try:
            self.player_process = subprocess.Popen(PLAYER_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.player_pid = self.player_process.pid
            self.player_started.emit(self.player_pid)

            async for chunk in communicate.stream():
                if self._stop_requested:
                    self.status_update.emit("TTS generation cancelled.")
                    return False, "TTS cancelled by user."
                if chunk["type"] == "audio":
                    if self.player_process.stdin:
                        try:
                            self.player_process.stdin.write(chunk["data"])
                        except BrokenPipeError:
                            self.status_update.emit("Player pipe broken.")
                            return False, "Player pipe broken during streaming."
                    else: return False, "Player stdin is None."
            
            if self.player_process.stdin: self.player_process.stdin.close()
            
            while self.player_process.poll() is None:
                if self._stop_requested: break
                await asyncio.sleep(0.1)

            if self._stop_requested:
                if self.player_process.poll() is None:
                    self.status_update.emit("Stopping player...")
                    if self._is_paused_by_user:
                        try: os.kill(self.player_pid, signal.SIGCONT)
                        except OSError: pass
                    self.player_process.terminate()
                    try: self.player_process.wait(timeout=1)
                    except subprocess.TimeoutExpired: self.player_process.kill()
                return False, "Playback stopped by user."

            ret_code = self.player_process.wait()
            self.playback_officially_ended.emit()
            if ret_code != 0 and not self._stop_requested :
                return False, f"Player exited with code {ret_code}"
            return True, ""
        except Exception as e:
            self.playback_officially_ended.emit() # Ensure emitted
            return False, f"Error during TTS/playback: {e}"
        finally:
            if self.player_process and self.player_process.poll() is None : # Ensure player is cleaned up if error before wait()
                print("[TTSWorker] Cleaning up player process in finally block due to early exit/error.")
                if self._is_paused_by_user:
                    try: os.kill(self.player_pid, signal.SIGCONT)
                    except OSError: pass
                self.player_process.terminate()
                try: self.player_process.wait(timeout=0.5)
                except subprocess.TimeoutExpired: self.player_process.kill()

            self.player_process = None
            self.player_pid = None


    def run(self):
        try:
            loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(self._speak_async_edge())
            loop.close()
            self.finished.emit(success, message)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.playback_officially_ended.emit() # Ensure emitted
            self.finished.emit(False, f"TTS Worker critical error: {e}")

    @Slot()
    def request_stop(self):
        self._stop_requested = True
        if self.player_pid and self._is_paused_by_user:
            try:
                os.kill(self.player_pid, signal.SIGCONT)
                self._is_paused_by_user = False
            except OSError: pass

    @Slot()
    def pause_player(self):
        if self.player_pid and not self._is_paused_by_user and not self._stop_requested:
            try:
                os.kill(self.player_pid, signal.SIGSTOP)
                self._is_paused_by_user = True
                self.status_update.emit("Status: Paused")
                return True
            except OSError as e: self.status_update.emit(f"Status: Error pausing - {e}")
        return False

    @Slot()
    def resume_player(self):
        if self.player_pid and self._is_paused_by_user and not self._stop_requested:
            try:
                os.kill(self.player_pid, signal.SIGCONT)
                self._is_paused_by_user = False
                self.status_update.emit("Status: Resuming...")
                return True
            except OSError as e: self.status_update.emit(f"Status: Error resuming - {e}")
        return False


class SpeakApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (same setup)
        self.setWindowTitle("Chinese Text-to-Speech (Edge TTS with PySide6)")
        self.setGeometry(100, 100, 650, 500)

        if not PLAYER_COMMAND:
            QMessageBox.critical(self, "Error", "No suitable audio player found.")
            sys.exit(1)

        self.current_tts_thread = None
        self.current_tts_worker = None
        self.current_player_pid = None
        self.is_playing_audio = False
        self.is_paused_by_gui = False
        
        self.voice_loader_worker = None # To keep a reference to the loader worker
        self.voice_thread = None 

        self._setup_ui()
        self._load_voices()

    def _setup_ui(self):
        # ... (same as before)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        voice_layout = QHBoxLayout()
        voice_label = QLabel("Select Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(250)
        self.voice_combo.setEnabled(False)
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        main_layout.addLayout(voice_layout)

        text_input_label = QLabel("Enter Chinese text (or select a portion to speak):")
        main_layout.addWidget(text_input_label)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("你好，世界！")
        self.text_input.setPlainText("你好，世界！这是一个测试。\n这是第二行，方便选择。")
        main_layout.addWidget(self.text_input)

        buttons_layout = QHBoxLayout()
        self.speak_button = QPushButton("Speak")
        self.speak_button.setEnabled(False)
        self.speak_button.clicked.connect(self.on_speak_button_click)
        buttons_layout.addWidget(self.speak_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.on_pause_button_click)
        buttons_layout.addWidget(self.pause_button)
        main_layout.addLayout(buttons_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Status: Initializing...")


    def _load_voices(self):
        print("[SpeakApp] _load_voices called.")
        self.status_bar.showMessage("Status: Loading voices...")
        
        if self.voice_thread and self.voice_thread.isRunning():
            print("[SpeakApp] Previous voice_thread is running. Quitting it.")
            self.voice_thread.quit()
            if not self.voice_thread.wait(1000): # Wait up to 1 sec
                print("[SpeakApp] Previous voice_thread did not quit gracefully. Terminating.")
                self.voice_thread.terminate()
                self.voice_thread.wait() # Wait for termination
        self.voice_thread = None # Clear old thread ref
        if self.voice_loader_worker: # Clear old worker ref
             self.voice_loader_worker.deleteLater() # Schedule old worker for deletion
             self.voice_loader_worker = None

        self.voice_thread = QThread(self) # Parent to main window
        self.voice_loader_worker = VoiceLoader() # Create new worker
        self.voice_loader_worker.moveToThread(self.voice_thread)
        print("[SpeakApp] VoiceLoader worker created and moved to new QThread.")

        # Connections
        self.voice_loader_worker.finished.connect(self._on_voices_loaded)
        # When worker's finished signal is emitted, it means its job is done.
        # Then we can quit the thread.
        self.voice_loader_worker.finished.connect(self.voice_thread.quit)
        # Schedule worker for deletion after its finished signal has been processed
        # and thread is about to quit or has quit.
        self.voice_thread.finished.connect(self.voice_loader_worker.deleteLater)
        # Schedule thread for deletion after it has finished.
        self.voice_thread.finished.connect(self.voice_thread.deleteLater)
        # Clear our Python references once the thread has finished and is about to be deleted.
        self.voice_thread.finished.connect(self._clear_voice_loader_refs)

        self.voice_thread.started.connect(self.voice_loader_worker.run)
        print("[SpeakApp] Starting voice_thread...")
        self.voice_thread.start()
        if self.voice_thread.isRunning():
            print("[SpeakApp] voice_thread is running.")
        else:
            print("[SpeakApp] voice_thread FAILED to start.")


    @Slot()
    def _clear_voice_loader_refs(self):
        print("[SpeakApp] _clear_voice_loader_refs called because voice_thread finished.")
        # By the time this is called, deleteLater should have been scheduled for both
        # worker and thread. We just nullify our Python references.
        self.voice_loader_worker = None
        self.voice_thread = None
        print("[SpeakApp] voice_loader_worker and voice_thread references cleared.")


    def _on_voices_loaded(self, voices_data, error_msg):
        print(f"[SpeakApp] _on_voices_loaded called. Error: '{error_msg}', Voices: {len(voices_data)}")
        if error_msg:
            QMessageBox.critical(self, "Voice Loading Error", error_msg)
            self.status_bar.showMessage(f"Status: Error loading voices. {error_msg}")
            return # Important to return so UI doesn't try to use empty data
        if not voices_data:
            QMessageBox.warning(self, "No Voices", "No Chinese voices found with edge-tts.")
            self.status_bar.showMessage("Status: No Chinese voices available.")
            return # Important

        current_selection_text = self.voice_combo.currentText() # Preserve selection if possible
        self.voice_combo.clear() # Clear old items

        for v_data in voices_data:
            display_name = f"{v_data['ShortName']} ({v_data['Gender']})"
            self.voice_combo.addItem(display_name, v_data['ShortName'])
        
        # Try to restore selection or set default
        idx = self.voice_combo.findText(current_selection_text)
        if idx != -1:
            self.voice_combo.setCurrentIndex(idx)
        else:
            default_idx = self.voice_combo.findData(DEFAULT_VOICE) # Find by ShortName (userData)
            if default_idx != -1:
                 self.voice_combo.setCurrentIndex(default_idx)
            elif self.voice_combo.count() > 0:
                 self.voice_combo.setCurrentIndex(0)


        self.status_bar.showMessage("Status: Ready")
        self.speak_button.setEnabled(True)
        self.voice_combo.setEnabled(True)
        print("[SpeakApp] Voices loaded and UI updated.")

    # ... on_speak_button_click and other methods remain the same as your corrected version ...
    def on_speak_button_click(self):
        self._stop_current_tts_if_running() 

        cursor = self.text_input.textCursor()
        text_to_speak = cursor.selectedText().strip() if cursor.hasSelection() else self.text_input.toPlainText().strip()
        
        selected_voice_short_name = self.voice_combo.currentData()

        if not text_to_speak:
            QMessageBox.warning(self, "Input Error", "Please enter or select text.")
            self.status_bar.showMessage("Status: Ready")
            return
        if not selected_voice_short_name:
            QMessageBox.warning(self, "Input Error", "Please select a voice.")
            self.status_bar.showMessage("Status: Ready")
            return
        
        self.status_bar.showMessage(f"Status: Preparing to speak '{text_to_speak[:20]}...'")
        self.is_playing_audio = True 
        self.is_paused_by_gui = False
        self.speak_button.setEnabled(False)
        self.voice_combo.setEnabled(False)
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(False) 

        self.current_tts_thread = QThread(self)
        self.current_tts_worker = TTSWorker(text_to_speak, selected_voice_short_name)
        self.current_tts_worker.moveToThread(self.current_tts_thread)

        self.current_tts_worker.status_update.connect(self.status_bar.showMessage)
        self.current_tts_worker.player_started.connect(self._on_player_started)
        self.current_tts_worker.playback_officially_ended.connect(self._on_playback_really_ended)
        self.current_tts_worker.finished.connect(self._on_speak_worker_finished)
        
        self.current_tts_thread.started.connect(self.current_tts_worker.run)
        self.current_tts_worker.finished.connect(self.current_tts_thread.quit) # Worker done -> Thread quit
        self.current_tts_thread.finished.connect(self._clear_current_tts_refs_and_delete) 

        self.current_tts_thread.start()

    @Slot()
    def _clear_current_tts_refs_and_delete(self):
        if self.current_tts_worker:
            self.current_tts_worker.deleteLater()
            # print(f"[SpeakApp] current_tts_worker ({id(self.current_tts_worker)}) scheduled for deletion.")
            self.current_tts_worker = None
        if self.current_tts_thread: 
            self.current_tts_thread.deleteLater()
            # print(f"[SpeakApp] current_tts_thread ({id(self.current_tts_thread)}) scheduled for deletion.")
            self.current_tts_thread = None

    def _stop_current_tts_if_running(self):
        worker_to_stop = self.current_tts_worker
        thread_to_stop = self.current_tts_thread

        self.current_tts_worker = None
        self.current_tts_thread = None
        self.current_player_pid = None 

        if worker_to_stop:
            worker_to_stop.request_stop() 

        if thread_to_stop and thread_to_stop.isRunning():
            print("Stopping previous TTS thread...")
            thread_to_stop.quit() 
            if not thread_to_stop.wait(1500): 
                print("TTS thread did not quit gracefully, terminating.")
                thread_to_stop.terminate() 
                thread_to_stop.wait()
        
        self.is_playing_audio = False
        self.is_paused_by_gui = False
        self.speak_button.setEnabled(True) 
        self.voice_combo.setEnabled(True) 
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(False)


    @Slot(int)
    def _on_player_started(self, pid):
        if self.sender() == self.current_tts_worker:
            self.current_player_pid = pid
            self.is_playing_audio = True
            self.pause_button.setEnabled(True)
            self.status_bar.showMessage(f"Status: Playing (PID: {pid})...")
        else:
            print("Warning: _on_player_started from a non-current worker. Ignoring.")


    @Slot(bool, str)
    def _on_speak_worker_finished(self, success, message):
        if self.sender() != self.current_tts_worker and self.current_tts_worker is not None:
            print("Warning: _on_speak_worker_finished from a non-current worker. Ignoring.")
            return

        if not success and message and "stopped by user" not in message and "cancelled by user" not in message:
            QMessageBox.critical(self, "TTS Error", message)
            self.status_bar.showMessage(f"Status: Error - {message}")
        elif success:
             self.status_bar.showMessage("Status: Playback stream finished.") 
        
        if not self.is_playing_audio and self.current_tts_worker is None: 
            self._reset_playback_ui_state()


    @Slot()
    def _on_playback_really_ended(self):
        if self.sender() != self.current_tts_worker and self.current_tts_worker is not None:
            print("Warning: _on_playback_really_ended from a non-current worker. Ignoring.")
            return

        self.status_bar.showMessage("Status: Ready (Player exited)")
        self._reset_playback_ui_state()


    def _reset_playback_ui_state(self):
        self.is_playing_audio = False
        self.is_paused_by_gui = False
        self.current_player_pid = None 
        self.speak_button.setEnabled(True)
        self.voice_combo.setEnabled(True)
        self.pause_button.setText("Pause")
        self.pause_button.setEnabled(False)

    def on_pause_button_click(self):
        if not self.is_playing_audio or not self.current_tts_worker: 
            return

        if self.is_paused_by_gui:
            if self.current_tts_worker.resume_player():
                self.is_paused_by_gui = False
                self.pause_button.setText("Pause")
                if self.current_player_pid: 
                    self.status_bar.showMessage(f"Status: Playing (PID: {self.current_player_pid})...")
                else:
                    self.status_bar.showMessage(f"Status: Resuming...")

        else:
            if self.current_tts_worker.pause_player():
                self.is_paused_by_gui = True
                self.pause_button.setText("Resume")

    def closeEvent(self, event):
        print("[SpeakApp] closeEvent called.")
        self.status_bar.showMessage("Status: Closing application...")
        self._stop_current_tts_if_running()

        if self.voice_thread and self.voice_thread.isRunning():
            print("[SpeakApp] Voice thread is running during closeEvent. Stopping it.")
            self.voice_thread.quit()
            if not self.voice_thread.wait(1000):
                 print("[SpeakApp] Voice thread did not quit gracefully during closeEvent. Terminating.")
                 self.voice_thread.terminate()
                 self.voice_thread.wait()
        self.voice_thread = None 
        if self.voice_loader_worker: # ensure worker is also cleaned up
            self.voice_loader_worker.deleteLater()
            self.voice_loader_worker = None
        
        print("[SpeakApp] Proceeding with super().closeEvent()")
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = SpeakApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
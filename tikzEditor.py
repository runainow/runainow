# tikz_gui.py
# Complete TikZ GUI editor with text preview window
# Requires: Python 3.8+, PySide-6, a working LaTeX installation with pdflatex,
# and the command-line tool pdftocairo (poppler-utils).

import os, sys, subprocess, tempfile, shutil, threading
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit,
    QLabel, QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QScrollArea, QSplitter, QDialog
)

class PreviewDialog(QDialog):
    """Dialog to show the exact LaTeX code before compilation"""
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LaTeX Code Preview - What Will Be Compiled")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Add label
        label = QLabel("This is the exact LaTeX code that will be sent to pdflatex:")
        layout.addWidget(label)
        
        # Add text area with the content
        text_area = QTextEdit()
        text_area.setPlainText(content)
        text_area.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        text_area.setReadOnly(True)
        layout.addWidget(text_area)
        
        # Add buttons
        button_layout = QHBoxLayout()
        compile_btn = QPushButton("Compile This Code")
        cancel_btn = QPushButton("Cancel")
        
        compile_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(compile_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

class RawTextEdit(QTextEdit):
    """Custom QTextEdit that preserves exact text formatting"""
    
    def __init__(self):
        super().__init__()
        self._raw_content = ""
    
    def setRawText(self, text):
        """Set text while preserving exact formatting"""
        self._raw_content = text
        # Use setHtml with <pre> to preserve exact whitespace
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        self.setHtml(f'<pre style="font-family: monospace;">{escaped_text}</pre>')
    
    def getRawText(self):
        """Get the exact raw text content"""
        return self._raw_content
    
    def insertFromMimeData(self, source):
        """Override to handle paste operations with exact formatting"""
        if source.hasText():
            text = source.text()
            cursor = self.textCursor()
            cursor.insertText(text)
            # Update raw content
            self._raw_content = self.toPlainText()

class ZoomablePreview(QScrollArea):
    def __init__(self):
        super().__init__()
        self.zoom_factor = 1.0
        self._pixmap = None
        
        # Create the image label
        self.image_label = QLabel("Compile to preview")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel{background:#ffffff;border:1px solid #aaa;}")
        
        # Set up scroll area
        self.setWidget(self.image_label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignCenter)
        
        # Enable mouse wheel zooming
        self.setFocusPolicy(Qt.WheelFocus)
    
    def setPixmap(self, pixmap):
        """Set the pixmap and apply current zoom"""
        self._pixmap = pixmap
        self._update_display()
    
    def setText(self, text):
        """Set text when no image is available"""
        self.image_label.setText(text)
        self._pixmap = None
    
    def zoom_in(self):
        """Zoom in by 25%"""
        self.zoom_factor *= 1.25
        self._update_display()
    
    def zoom_out(self):
        """Zoom out by 25%"""
        self.zoom_factor /= 1.25
        if self.zoom_factor < 0.1:  # Prevent zooming out too much
            self.zoom_factor = 0.1
        self._update_display()
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_factor = 1.0
        self._update_display()
    
    def fit_to_window(self):
        """Fit image to the scroll area size"""
        if self._pixmap:
            scroll_size = self.size()
            # Account for scrollbar space
            available_size = scroll_size * 0.95
            scale_x = available_size.width() / self._pixmap.width()
            scale_y = available_size.height() / self._pixmap.height()
            self.zoom_factor = min(scale_x, scale_y)
            self._update_display()
    
    def _update_display(self):
        """Update the displayed image with current zoom"""
        if self._pixmap:
            scaled_pixmap = self._pixmap.scaled(
                self._pixmap.size() * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_pixmap.size())
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

class Compiler(QObject):
    done = Signal(Path, str)          # image_path, log

    def __init__(self):
        super().__init__()
        self._thread = None

    def compile_async(self, full_document: str):
        if self._thread and self._thread.is_alive():
            return                          # prevent overlapping runs
        self._thread = threading.Thread(target=self._compile, args=(full_document,))
        self._thread.start()

    def _compile(self, full_document: str):
        tmp = Path(tempfile.mkdtemp())
        tex = tmp / "figure.tex"
        
        try:
            # Write file as raw bytes with no text processing whatsoever
            with open(tex, 'wb') as f:
                f.write(full_document.encode('utf-8'))

            print(f"Starting compilation in {tmp}")
            
            # Debug: Show exact content being written
            print(f"Exact content (first 300 characters): {repr(full_document[:300])}")
            
            # First pass: pdflatex with increased timeout and non-interactive mode
            result = subprocess.run(
                ["pdflatex", "-halt-on-error", "-interaction=nonstopmode", 
                 "-file-line-error", "-shell-escape", tex.name],
                cwd=tmp, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                timeout=120,  # Increased timeout to 2 minutes
                input=b'',    # Send empty input to prevent hanging
            )
            
            print(f"pdflatex return code: {result.returncode}")
            
            if result.stdout:
                stdout_text = result.stdout.decode('utf-8', errors='ignore')
                print("LaTeX stdout:", stdout_text[-1500:])  # Show last 1500 chars
            
            pdf = tmp / "figure.pdf"
            
            if pdf.exists() and pdf.stat().st_size > 0:
                print(f"PDF created successfully: {pdf.stat().st_size} bytes")
                
                # Convert PDF to PNG with higher timeout
                png = tmp / "figure.png"
                png_result = subprocess.run(
                    ["pdftocairo", "-singlefile", "-png", "-r", "150", pdf, png.stem],
                    cwd=tmp, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    timeout=60  # 1 minute for PDF conversion
                )
                
                if png.exists():
                    print(f"PNG created successfully: {png.stat().st_size} bytes")
                    log_content = ""
                    if (tmp / "figure.log").exists():
                        log_content = (tmp / "figure.log").read_text(encoding="utf8", errors='ignore')
                    self.done.emit(png, log_content)
                else:
                    print("PNG conversion failed")
                    if png_result.stdout:
                        print("pdftocairo output:", png_result.stdout.decode('utf-8', errors='ignore'))
                    self.done.emit(Path(), "PNG conversion failed")
            else:
                print("PDF not created or is empty")
                log_content = ""
                if (tmp / "figure.log").exists():
                    log_content = (tmp / "figure.log").read_text(encoding="utf8", errors='ignore')
                    print("LaTeX log content:", log_content[-1500:])  # Show last 1500 chars
                self.done.emit(Path(), f"PDF compilation failed. Return code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            print("Compilation timed out - document too complex or has infinite loop")
            self.done.emit(Path(), "Compilation timed out (>2 minutes). Document may be too complex.")
        except Exception as e:
            print(f"Compilation error: {e}")
            self.done.emit(Path(), f"Compilation error: {str(e)}")
        finally:
            # Clean up - comment out for debugging
            try:
                shutil.rmtree(tmp)
            except:
                pass

class TikzGUI(QWidget):
    DEBOUNCE_MS = 1500  # Increased debounce for large documents

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikZ GUI Editor - With Preview Window")

        # Create tab widget for editors
        self.tabs = QTabWidget()

        # TikZ picture editor tab - using standard QTextEdit for simple content
        self.tikz_editor = QTextEdit()
        self.tikz_editor.setPlainText("\\begin{tikzpicture}\n  \\draw (0,0) -- (2,1);\n\\end{tikzpicture}")

        # Document template editor tab - using standard QTextEdit
        self.document_editor = QTextEdit()
        default_template = """\\documentclass[tikz,border=2pt]{standalone}
\\usepackage{tikz}
\\usetikzlibrary{calc, positioning, arrows.meta}
\\begin{document}
{code}
\\end{document}"""
        self.document_editor.setPlainText(default_template)

        # Complete code editor tab - using RawTextEdit for exact formatting
        self.code_editor = RawTextEdit()
        complete_code_example = """\\documentclass[tikz,border=2pt]{standalone}
\\usepackage{tikz}
\\usetikzlibrary{calc, positioning, arrows.meta}
\\begin{document}
\\begin{tikzpicture}
  \\draw (0,0) -- (2,1);
\\end{tikzpicture}
\\end{document}"""
        self.code_editor.setRawText(complete_code_example)

        # Add tabs
        self.tabs.addTab(self.tikz_editor, "tikzpicture")
        self.tabs.addTab(self.document_editor, "document")
        self.tabs.addTab(self.code_editor, "code")

        # Create zoomable preview area
        self.preview = ZoomablePreview()
        self.preview.setMinimumWidth(400)

        # Zoom control buttons
        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        reset_zoom_btn = QPushButton("Reset Zoom")
        fit_window_btn = QPushButton("Fit to Window")
        zoom_label = QLabel("Zoom: 100%")
        self.zoom_label = zoom_label

        # Connect zoom button events
        zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_out_btn.clicked.connect(self._zoom_out)
        reset_zoom_btn.clicked.connect(self._reset_zoom)
        fit_window_btn.clicked.connect(self._fit_to_window)

        # Zoom controls layout
        zoom_controls = QHBoxLayout()
        zoom_controls.addWidget(zoom_in_btn)
        zoom_controls.addWidget(zoom_out_btn)
        zoom_controls.addWidget(reset_zoom_btn)
        zoom_controls.addWidget(fit_window_btn)
        zoom_controls.addWidget(zoom_label)

        # Right panel layout (preview + zoom controls)
        right_panel = QVBoxLayout()
        right_panel.addWidget(self.preview, 1)
        right_panel.addLayout(zoom_controls)

        # Main editor buttons
        open_btn         = QPushButton("Open")
        save_btn         = QPushButton("Save")
        paste_btn        = QPushButton("Paste from Clipboard")
        paste_to_code_btn = QPushButton("Paste to Code")
        preview_code_btn = QPushButton("Preview Code")  # NEW BUTTON
        compile_btn      = QPushButton("Compile")

        bar = QHBoxLayout()
        bar.addWidget(open_btn)
        bar.addWidget(save_btn)
        bar.addWidget(paste_btn)
        bar.addWidget(paste_to_code_btn)
        bar.addWidget(preview_code_btn)  # ADD NEW BUTTON
        bar.addWidget(compile_btn)
        
        left = QVBoxLayout()
        left.addWidget(self.tabs)
        left.addLayout(bar)

        # Main layout: left panel (editor) + right panel (preview + zoom)
        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addLayout(right_panel, 1)

        self.compiler = Compiler()
        self.compiler.done.connect(self._update_preview)

        # reactive compile after idle typing (for all editors)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._kick_compile)
        
        # Connect text changes from all editors to trigger compilation
        self.tikz_editor.textChanged.connect(lambda: self.timer.start(self.DEBOUNCE_MS))
        self.document_editor.textChanged.connect(lambda: self.timer.start(self.DEBOUNCE_MS))
        self.code_editor.textChanged.connect(lambda: self.timer.start(self.DEBOUNCE_MS))
        
        compile_btn.clicked.connect(self._kick_compile)
        preview_code_btn.clicked.connect(self._preview_code)  # CONNECT NEW BUTTON
        open_btn.clicked.connect(self._open)
        save_btn.clicked.connect(self._save)
        paste_btn.clicked.connect(self._paste_from_clipboard)
        paste_to_code_btn.clicked.connect(self._paste_to_code)

    # -------------- zoom helpers --------------------------------------------
    def _zoom_in(self):
        self.preview.zoom_in()
        self._update_zoom_label()

    def _zoom_out(self):
        self.preview.zoom_out()
        self._update_zoom_label()

    def _reset_zoom(self):
        self.preview.reset_zoom()
        self._update_zoom_label()

    def _fit_to_window(self):
        self.preview.fit_to_window()
        self._update_zoom_label()

    def _update_zoom_label(self):
        zoom_percent = int(self.preview.zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")

    # -------------- compilation helpers -------------------------------------- 
    def _prepare_document(self):
        """Prepare the document for compilation/preview"""
        current_tab_index = self.tabs.currentIndex()
        
        if current_tab_index == 2:  # code tab
            # Use complete code directly from RawTextEdit
            full_document = self.code_editor.getRawText() or self.code_editor.toPlainText()
        else:
            # Combine document template and tikzpicture code
            doc_template = self.document_editor.toPlainText()
            tikz_code = self.tikz_editor.toPlainText()
            
            # Simple string replacement - should be safe for templates
            if "{code}" in doc_template:
                full_document = doc_template.replace("{code}", tikz_code)
            else:
                # Fallback: direct concatenation
                full_document = doc_template + "\n" + tikz_code
        
        return full_document

    def _preview_code(self):
        """Show preview dialog with the exact LaTeX code"""
        full_document = self._prepare_document()
        
        dialog = PreviewDialog(full_document, self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # User clicked "Compile This Code"
            self._compile_document(full_document)

    def _kick_compile(self):
        """Compile based on the active tab"""
        full_document = self._prepare_document()
        self._compile_document(full_document)

    def _compile_document(self, full_document):
        """Actually compile the document"""
        # Show compilation status
        self.preview.setText("Compiling... (may take up to 2 minutes for large documents)")
        
        # Debug output
        print(f"Compiling document ({len(full_document)} characters)")
        print(f"First 300 characters: {repr(full_document[:300])}")
        
        self.compiler.compile_async(full_document)

    def _update_preview(self, img_path: Path, log: str):
        if img_path and img_path.exists():
            pixmap = QPixmap(str(img_path))
            self.preview.setPixmap(pixmap)
            self._update_zoom_label()
            print("Preview updated successfully")
        else:
            # Print to console instead of showing popup
            print(f"Compilation failed:\n{log}")
            self.preview.setText("Compilation failed (see console for details)")

    def _open(self):
        """Open file into the currently active tab"""
        current_tab_index = self.tabs.currentIndex()
        tab_names = ["tikzpicture", "document", "code"]
        tab_name = tab_names[current_tab_index]
        
        file_filters = [
            "TikZ (*.tikz *.tex)",
            "TeX Template (*.tex)",
            "LaTeX (*.tex *.latex)"
        ]
        file_filter = file_filters[current_tab_index]
        
        path, _ = QFileDialog.getOpenFileName(self, f"Open {tab_name} file", "", file_filter)
        
        if path:
            # Read file as raw bytes
            with open(path, 'rb') as f:
                content = f.read().decode('utf-8')
            
            if current_tab_index == 0:
                self.tikz_editor.setPlainText(content)
            elif current_tab_index == 1:
                self.document_editor.setPlainText(content)
            else:  # current_tab_index == 2
                self.code_editor.setRawText(content)

    def _save(self):
        """Save content from the currently active tab"""
        current_tab_index = self.tabs.currentIndex()
        tab_names = ["tikzpicture", "document", "code"]
        tab_name = tab_names[current_tab_index]
        
        file_filters = [
            "TikZ (*.tikz);;TeX (*.tex)",
            "TeX Template (*.tex)",
            "LaTeX (*.tex);;LaTeX (*.latex)"
        ]
        file_filter = file_filters[current_tab_index]
        
        path, _ = QFileDialog.getSaveFileName(self, f"Save {tab_name}", "", file_filter)
        
        if path:
            if current_tab_index == 0:
                content = self.tikz_editor.toPlainText()
            elif current_tab_index == 1:
                content = self.document_editor.toPlainText()
            else:  # current_tab_index == 2
                content = self.code_editor.getRawText() or self.code_editor.toPlainText()
            
            # Write file as raw bytes
            with open(path, 'wb') as f:
                f.write(content.encode('utf-8'))

    def _paste_from_clipboard(self):
        """Paste clipboard content into the currently active tab"""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        
        if clipboard_text:
            current_tab_index = self.tabs.currentIndex()
            tab_names = ["tikzpicture", "document", "code"]
            tab_name = tab_names[current_tab_index]
            
            if current_tab_index == 0:
                self.tikz_editor.setPlainText(clipboard_text)
            elif current_tab_index == 1:
                self.document_editor.setPlainText(clipboard_text)
            else:  # current_tab_index == 2
                self.code_editor.setRawText(clipboard_text)
                
            print(f"Pasted {len(clipboard_text)} characters into {tab_name} tab")
        else:
            print("Clipboard is empty")

    def _paste_to_code(self):
        """Paste clipboard content directly to the code tab with ZERO processing"""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        
        if clipboard_text:
            # Switch to code tab
            self.tabs.setCurrentIndex(2)
            
            # Use RawTextEdit's raw text setting to preserve exact formatting
            self.code_editor.setRawText(clipboard_text)
            
            # Debug verification
            retrieved_text = self.code_editor.getRawText()
            print(f"Clipboard -> Editor verification:")
            print(f"Clipboard length: {len(clipboard_text)}")
            print(f"Editor length: {len(retrieved_text)}")
            print(f"First 100 chars match: {clipboard_text[:100] == retrieved_text[:100]}")
            
            # Don't auto-compile, let user use Preview Code button first
            print(f"Pasted complete LaTeX document ({len(clipboard_text)} characters) to code tab")
            print("Use 'Preview Code' button to see exactly what will be compiled")
        else:
            print("Clipboard is empty")

def main():
    app = QApplication(sys.argv)
    # load a mono font if available
    mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    QApplication.setFont(mono)
    w = TikzGUI(); w.resize(1100, 700); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

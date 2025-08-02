# tikz_gui.py
# Minimal GUI editor for TikZ pictures.
# Requires: Python 3.8+, PySide-6, a working LaTeX installation with pdflatex,
# and the command-line tool pdftocairo (poppler-utils).

import os, sys, subprocess, tempfile, shutil, threading
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui  import QPixmap, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit,
    QLabel, QPushButton, QFileDialog, QMessageBox
)

def create_latex_document(tikz_code: str) -> str:
    return f"""\\documentclass[tikz,border=2pt]{{standalone}}
\\usepackage{{tikz}}
\\begin{{document}}
{tikz_code}
\\end{{document}}
"""

class Compiler(QObject):
    done = Signal(Path, str)          # image_path, log

    def __init__(self):
        super().__init__()
        self._thread = None

    def compile_async(self, tikz_code: str):
        if self._thread and self._thread.is_alive():
            return                          # prevent overlapping runs
        self._thread = threading.Thread(target=self._compile, args=(tikz_code,))
        self._thread.start()

    def _compile(self, tikz_code: str):
        tmp = Path(tempfile.mkdtemp())
        tex = tmp / "figure.tex"
        tex.write_text(create_latex_document(tikz_code), encoding="utf8")

        try:
            subprocess.run(
                ["pdflatex", "-halt-on-error", "-interaction=batchmode", tex.name],
                cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30
            )
            pdf = tmp / "figure.pdf"
            png = tmp / "figure.png"
            subprocess.run(
                ["pdftocairo", "-singlefile", "-png", pdf, png.stem],
                cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20
            )
            self.done.emit(png, (tmp / "figure.log").read_text(encoding="utf8") if (tmp / "figure.log").exists() else "")
        except Exception as e:
            print(f"Compilation error: {e}")  # Print to console instead
            self.done.emit(Path(), str(e))

class TikzGUI(QWidget):
    DEBOUNCE_MS = 800

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TikZ GUI Editor")

        self.editor   = QTextEdit()
        self.preview  = QLabel("Compile to preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumWidth(400)
        self.preview.setStyleSheet("QLabel{background:#ffffff;border:1px solid #aaa;}")

        open_btn   = QPushButton("Open")
        save_btn   = QPushButton("Save")
        paste_btn  = QPushButton("Paste from Clipboard")  # New button
        compile_btn= QPushButton("Compile")

        bar = QHBoxLayout()
        bar.addWidget(open_btn)
        bar.addWidget(save_btn)
        bar.addWidget(paste_btn)  # Add the new button to layout
        bar.addWidget(compile_btn)
        
        left = QVBoxLayout()
        left.addWidget(self.editor)
        left.addLayout(bar)

        root = QHBoxLayout(self)
        root.addLayout(left, 1)
        root.addWidget(self.preview, 1)

        self.compiler = Compiler()
        self.compiler.done.connect(self._update_preview)

        # reactive compile after idle typing
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._kick_compile)
        self.editor.textChanged.connect(lambda: self.timer.start(self.DEBOUNCE_MS))
        compile_btn.clicked.connect(self._kick_compile)
        open_btn.clicked.connect(self._open)
        save_btn.clicked.connect(self._save)
        paste_btn.clicked.connect(self._paste_from_clipboard)  # Connect new button

        # sensible defaults
        self.editor.setPlainText("\\begin{tikzpicture}\n  \\draw (0,0) -- (2,1);\n\\end{tikzpicture}")

    # -------------- helpers -------------------------------------------------
    def _kick_compile(self):
        self.compiler.compile_async(self.editor.toPlainText())

    def _update_preview(self, img_path: Path, log: str):
        if img_path and img_path.exists():
            self.preview.setPixmap(QPixmap(str(img_path)).scaled(
                self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Print to console instead of showing popup
            print(f"Compilation failed: {log or 'Unknown error'}")
            self.preview.setText("Compilation failed (see console)")

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open .tikz or .tex", "", "TikZ (*.tikz *.tex)")
        if path:
            self.editor.setPlainText(Path(path).read_text(encoding="utf8"))

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save TikZ code", "", "TikZ (*.tikz);;TeX (*.tex)")
        if path:
            Path(path).write_text(self.editor.toPlainText(), encoding="utf8")

    def _paste_from_clipboard(self):
        """Replace editor content with clipboard text"""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        if clipboard_text:
            self.editor.setPlainText(clipboard_text)
            print(f"Pasted {len(clipboard_text)} characters from clipboard")
        else:
            print("Clipboard is empty")

def main():
    app = QApplication(sys.argv)
    # load a mono font if available
    mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    QApplication.setFont(mono)
    w = TikzGUI(); w.resize(950, 600); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

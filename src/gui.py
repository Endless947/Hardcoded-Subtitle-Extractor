import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QTextEdit, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from src.video_utils import extract_frames
from src.ocr import ocr_frame_easyocr
from src.srt_writer import write_srt
from rapidfuzz import fuzz

class WorkerSignals(QObject):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)

class SubtitleExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Extractor")
        self.setGeometry(200, 200, 600, 500)

        # UI elements
        self.label = QLabel("Select a video file to extract subtitles", self)
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)

        self.btn_select = QPushButton("Select Video", self)
        self.btn_extract = QPushButton("Extract Subtitles", self)
        self.btn_save_txt = QPushButton("Save Subtitles as Text", self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.btn_cancel = QPushButton("Cancel Extraction", self)
        self.btn_cancel.setEnabled(False)

        self.cancel_flag = False
        self.video_path = None
        self.subs_text_only = []

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_extract)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_save_txt)
        layout.addWidget(self.log_area)
        self.setLayout(layout)

        # signals for thread-safe GUI updates
        self.signals = WorkerSignals()
        self.signals.log.connect(self.log_area.append)
        self.signals.progress.connect(self.progress_bar.setValue)

        # connect buttons
        self.btn_select.clicked.connect(self.select_video)
        self.btn_extract.clicked.connect(self.start_extraction_thread)
        self.btn_cancel.clicked.connect(self.cancel_extraction)
        self.btn_save_txt.clicked.connect(self.save_subtitles_text)

    def cancel_extraction(self):
        self.cancel_flag = True
        self.signals.log.emit("[INFO] Extraction cancelled by user.")

    def select_video(self):
        file_dialog = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Videos (*.mp4 *.avi *.mkv)"
        )
        if file_dialog[0]:
            self.video_path = file_dialog[0]
            self.signals.log.emit(f"[INFO] Selected: {self.video_path}")

    def start_extraction_thread(self):
        if not self.video_path:
            self.signals.log.emit("[ERROR] No video selected!")
            return
        thread = threading.Thread(target=self.extract_subtitles)
        thread.start()

    def extract_subtitles(self):
        self.signals.log.emit(f"[INFO] Extracting subtitles from: {self.video_path}")

        # extract frames every 5 seconds
        frames = extract_frames(self.video_path, interval_ms=500)
        total_frames = len(frames)
        self.progress_bar.setMaximum(total_frames)
        self.progress_bar.setValue(0)

        self.cancel_flag = False
        self.btn_cancel.setEnabled(True)

        entries = []
        seen_texts = []

        skip_keywords = [
            "activate", "windows", "go to settings",
            "activate windows", "go to settings to activate windows"
        ]

        for idx, (timestamp, frame) in enumerate(frames, start=1):
            if self.cancel_flag:
                break

            text = ocr_frame_easyocr(frame)
            if not text:
                self.signals.progress.emit(idx)
                continue  # skip empty frames

            clean_text = text.strip().lower()

            # skip unwanted overlay text
            if any(keyword in clean_text for keyword in skip_keywords):
                self.signals.progress.emit(idx)
                continue

            # skip near-duplicate lines
            is_duplicate = any(fuzz.ratio(clean_text, prev.lower()) > 90 for prev in seen_texts)
            if is_duplicate:
                self.signals.progress.emit(idx)
                continue

            # add new subtitle
            entries.append((timestamp, text))
            seen_texts.append(text)
            self.subs_text_only.append(text)
            self.signals.log.emit(f"[{timestamp:.1f}s] {text}")
            self.signals.progress.emit(idx)

        self.btn_cancel.setEnabled(False)

        # group similar consecutive texts for SRT
        subs = []
        if entries:
            current_text = entries[0][1]
            start_time = entries[0][0]
            last_time = entries[0][0]
            for t, text in entries[1:]:
                similarity = fuzz.ratio(current_text.lower(), text.lower())
                if similarity > 90:  # stricter threshold for near-duplicates
                    last_time = t
                else:
                    subs.append((start_time, last_time + 0.5, current_text))
                    current_text = text
                    start_time = t
                    last_time = t
            subs.append((start_time, last_time + 0.5, current_text))

        # save SRT
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Subtitles As", "output.srt", "Subtitle Files (*.srt)"
        )
        if save_path:
            write_srt(subs, save_path)
            self.signals.log.emit(f"[INFO] Subtitles saved to {save_path}")
        else:
            self.signals.log.emit("[INFO] SRT save cancelled.")

    def save_subtitles_text(self):
        if not self.subs_text_only:
            self.signals.log.emit("[ERROR] No subtitles to save!")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Subtitles As Text", "output.txt", "Text Files (*.txt)"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for line in self.subs_text_only:
                    f.write(line + "\n")
            self.signals.log.emit(f"[INFO] Subtitles saved as text to {save_path}")
        else:
            self.signals.log.emit("[INFO] Text save cancelled.")

def run_app():
    app = QApplication(sys.argv)
    window = SubtitleExtractorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()

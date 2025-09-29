import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QTextEdit, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt

from src.video_utils import extract_frames
from src.ocr import ocr_frame_easyocr
from src.srt_writer import write_srt
from rapidfuzz import fuzz

class SubtitleExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Extractor")
        self.setGeometry(200, 200, 600, 450)

        # UI elements
        self.label = QLabel("Select a video file to extract subtitles", self)
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)

        self.btn_select = QPushButton("Select Video", self)
        self.btn_extract = QPushButton("Extract Subtitles", self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.btn_cancel = QPushButton("Cancel Extraction", self)
        self.btn_cancel.setEnabled(False)  # disabled until extraction starts

        self.cancel_flag = False

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_extract)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.log_area)
        self.setLayout(layout)

        # connect signals
        self.btn_select.clicked.connect(self.select_video)
        self.btn_extract.clicked.connect(self.extract_subtitles)
        self.btn_cancel.clicked.connect(self.cancel_extraction)
        self.video_path = None
    
    def cancel_extraction(self):
        self.cancel_flag = True
        self.log_area.append("[INFO] Extraction cancelled by user.")

    def select_video(self):
        file_dialog = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Videos (*.mp4 *.avi *.mkv)"
        )
        if file_dialog[0]:
            self.video_path = file_dialog[0]
            self.log_area.append(f"[INFO] Selected: {self.video_path}")

    def extract_subtitles(self):
        if not self.video_path:
            self.log_area.append("[ERROR] No video selected!")
            return

        self.log_area.append(f"[INFO] Extracting subtitles from: {self.video_path}")
        frames = extract_frames(self.video_path, interval_ms=500)
        total_frames = len(frames)
        self.progress_bar.setMaximum(total_frames)
        self.progress_bar.setValue(0)

        self.cancel_flag = False
        self.btn_cancel.setEnabled(True)  # enable cancel button during extraction

        entries = []
        for idx, (timestamp, frame) in enumerate(frames, start=1):
            if self.cancel_flag:
                break  # stop processing immediately

            text = ocr_frame_easyocr(frame)
            if text:
                entries.append((timestamp, text))
                self.log_area.append(f"[{timestamp:.1f}s] {text}")

            # update progress bar
            self.progress_bar.setValue(idx)
            QApplication.processEvents()

        self.btn_cancel.setEnabled(False)  # disable after extraction


        # group similar consecutive texts
        subs = []
        if entries:
            current_text = entries[0][1]
            start_time = entries[0][0]
            last_time = entries[0][0]
            for t, text in entries[1:]:
                similarity = fuzz.ratio(current_text, text)
                if similarity > 80:
                    last_time = t
                else:
                    subs.append((start_time, last_time + 0.5, current_text))
                    current_text = text
                    start_time = t
                    last_time = t
            subs.append((start_time, last_time + 0.5, current_text))

        # ask user where to save
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Subtitles As", "output.srt", "Subtitle Files (*.srt)"
        )
        if save_path:
            write_srt(subs, save_path)
            self.log_area.append(f"[INFO] Subtitles saved to {save_path}")
        else:
            self.log_area.append("[INFO] Save cancelled.")

def run_app():
    app = QApplication(sys.argv)
    window = SubtitleExtractorApp()
    window.show()
    sys.exit(app.exec_())

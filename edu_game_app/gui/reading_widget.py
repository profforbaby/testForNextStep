"""
Reading passage display widget with text-to-speech
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTextEdit, QSlider)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor


class ReadingWidget(QWidget):
    """Widget for displaying reading passages with TTS support"""

    next_clicked = pyqtSignal(object)  # Emits passage when ready for quiz

    def __init__(self, text_reader):
        super().__init__()
        self.text_reader = text_reader
        self.current_passage = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(20)

        # Reading passage display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Arial", 16))
        layout.addWidget(self.text_display)

        layout.addSpacing(10)

        # TTS controls
        tts_controls = self.create_tts_controls()
        layout.addWidget(tts_controls)

        layout.addSpacing(20)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.read_button = QPushButton("Read Aloud")
        self.read_button.setMinimumHeight(50)
        self.read_button.setFont(QFont("Arial", 14))
        self.read_button.clicked.connect(self.read_aloud)
        button_layout.addWidget(self.read_button)

        self.stop_button = QPushButton("Stop Reading")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setFont(QFont("Arial", 14))
        self.stop_button.clicked.connect(self.stop_reading)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.next_button = QPushButton("Take Quiz →")
        self.next_button.setMinimumHeight(50)
        self.next_button.setFont(QFont("Arial", 14))
        self.next_button.clicked.connect(self.on_next_clicked)
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)

    def create_tts_controls(self) -> QWidget:
        """Create TTS speed controls"""
        controls = QWidget()
        layout = QHBoxLayout(controls)

        layout.addWidget(QLabel("Reading Speed:"))

        # Speed slider
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(2)
        self.speed_slider.setValue(1)  # Normal
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.valueChanged.connect(self.change_speed)
        layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("Normal")
        layout.addWidget(self.speed_label)

        layout.addStretch()

        return controls

    def set_passage(self, passage):
        """Set the passage to display"""
        self.current_passage = passage
        self.title_label.setText(passage.title)
        self.text_display.setPlainText(passage.content)

    def read_aloud(self):
        """Read passage aloud with TTS (runs in background thread)"""
        if not self.current_passage:
            return

        self.read_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        def on_done():
            # Called from TTS background thread — use QTimer to safely update UI
            QTimer.singleShot(0, self._on_reading_done)

        try:
            self.text_reader.read_text(self.current_passage.content, done_callback=on_done)
        except Exception as e:
            print(f"TTS Error: {e}")
            self._on_reading_done()

    def _on_reading_done(self):
        """Restore button states after reading finishes or is stopped"""
        self.read_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_reading(self):
        """Stop TTS"""
        self.text_reader.stop()
        self._on_reading_done()

    def change_speed(self, value):
        """Change reading speed"""
        speeds = {0: 'slow', 1: 'normal', 2: 'fast'}
        speed_labels = {0: 'Slow', 1: 'Normal', 2: 'Fast'}

        speed = speeds.get(value, 'normal')
        self.speed_label.setText(speed_labels.get(value, 'Normal'))
        self.text_reader.set_speed(speed)

    def on_next_clicked(self):
        """Handle next button click"""
        if self.current_passage:
            self.stop_reading()
            self.next_clicked.emit(self.current_passage)

"""
Timer widget for displaying game time balance
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette


class TimerWidget(QWidget):
    """Widget to display game time balance"""

    def __init__(self):
        super().__init__()
        self.time_minutes = 0
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Label
        label = QLabel("Game Time:")
        label.setFont(QFont("Arial", 10))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Time display
        self.time_label = QLabel("0m")
        self.time_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        # Set background color
        self.setAutoFillBackground(True)
        self.update_color()

    def update_time(self, minutes: int):
        """Update displayed time"""
        self.time_minutes = minutes

        # Format time
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            time_str = f"{hours}h {mins}m"
        else:
            time_str = f"{mins}m"

        self.time_label.setText(time_str)
        self.update_color()

    def update_color(self):
        """Update background color based on time available"""
        palette = self.palette()

        if self.time_minutes == 0:
            # Red when no time
            palette.setColor(QPalette.ColorRole.Window, QColor(255, 200, 200))
        elif self.time_minutes < 15:
            # Yellow when low time
            palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 200))
        else:
            # Green when good time
            palette.setColor(QPalette.ColorRole.Window, QColor(200, 255, 200))

        self.setPalette(palette)

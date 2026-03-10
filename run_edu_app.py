"""
Simple launcher for the Educational App
Run this file from the parent directory
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from edu_game_app/ before any other imports read env vars
load_dotenv(Path(__file__).parent / "edu_game_app" / ".env")

from PyQt6.QtWidgets import QApplication
from edu_game_app.gui.main_window import MainWindow


def main():
    """Main entry point"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Learn & Play")
    app.setOrganizationName("Educational Apps")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

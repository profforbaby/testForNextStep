"""
Main application entry point
Educational app for children - Learn & Play
"""
import sys
import os

# Add the parent directory to Python path to fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load .env file so ANTHROPIC_API_KEY is available
from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, '.env'))

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

"""
Main application window
"""
import sys
import signal
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QStackedWidget, QMessageBox,
                              QInputDialog, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QEvent, QRect
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import QApplication

from edu_game_app.gui.reading_widget import ReadingWidget
from edu_game_app.gui.quiz_widget import QuizWidget
from edu_game_app.gui.timer_widget import TimerWidget
from edu_game_app.gui.parent_panel import ParentPanel

from edu_game_app.core import (ContentGenerator, QuizEngine, DifficultyManager,
                   ProgressTracker, GameTimeTracker, TextReader, start_remote_server)
from edu_game_app.data import Database


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Learn & Play - Educational App")
        self.setMinimumSize(800, 600)

        # Initialize core components
        self.db = Database("edu_app.db")
        self.profile = self.db.get_or_create_profile()
        # Ensure existing profiles are upgraded to minimum level 4
        if self.profile.current_level < 4:
            self.profile.current_level = 4
            self.db.update_profile(self.profile)
        self.quiz_engine = QuizEngine()
        self.difficulty_mgr = DifficultyManager(self.profile.current_level)
        self.progress_tracker = ProgressTracker()
        self.db.reset_game_time_balance()
        self.game_tracker = GameTimeTracker(self.db)
        self.text_reader = TextReader()

        try:
            self.content_gen = ContentGenerator()
        except ValueError:
            self.content_gen = None
            QMessageBox.warning(self, "API Key Missing",
                              "Anthropic API key not found. Using fallback content.\n"
                              "Set ANTHROPIC_API_KEY environment variable for AI-generated content.")

        # Setup UI
        self.init_ui()
        self.setup_menu()

        # Timer for game time monitoring
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_game_time)
        self.game_timer.start(1000)  # Update every second

        # Start remote control server for phone access
        try:
            ip, port = start_remote_server(self.game_tracker, self.db)
            self._remote_url = f"http://{ip}:{port}"
        except Exception:
            self._remote_url = None

        # Track which low-time thresholds have already triggered a warning this session
        self._warned_thresholds: set = set()

        # Track current always-on-top state to avoid redundant flag changes
        self._always_on_top: bool = False

        # Flag set by SIGTERM (system shutdown/restart) — allows closeEvent to skip password
        self._system_shutdown: bool = False
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Apply correct initial window behavior based on starting balance
        self._update_window_lock(self.game_tracker.get_time_balance())

    def init_ui(self):
        """Initialize user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Header with welcome and status
        header = self.create_header()
        layout.addWidget(header)

        # Main content area with stacked widgets
        self.stacked_widget = QStackedWidget()

        # Home screen
        self.home_screen = self.create_home_screen()
        self.stacked_widget.addWidget(self.home_screen)

        # Reading widget
        self.reading_widget = ReadingWidget(self.text_reader)
        self.reading_widget.next_clicked.connect(self.start_quiz)
        self.stacked_widget.addWidget(self.reading_widget)

        # Quiz widget
        self.quiz_widget = QuizWidget()
        self.quiz_widget.quiz_finished.connect(self.handle_quiz_finished)
        self.stacked_widget.addWidget(self.quiz_widget)

        layout.addWidget(self.stacked_widget)

        # Show home screen initially
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def create_header(self) -> QWidget:
        """Create header with status info"""
        header = QWidget()
        header_layout = QHBoxLayout(header)

        # Welcome label
        self.welcome_label = QLabel(f"Welcome, {self.profile.name}!")
        self.welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.welcome_label)

        header_layout.addStretch()

        # Level indicator
        level_text = self.difficulty_mgr.get_level_description()
        self.level_label = QLabel(level_text)
        self.level_label.setFont(QFont("Arial", 12))
        header_layout.addWidget(self.level_label)

        header_layout.addSpacing(20)

        # Timer widget
        self.timer_widget = TimerWidget()
        self.timer_widget.update_time(self.game_tracker.get_time_balance())
        header_layout.addWidget(self.timer_widget)

        return header

    def create_home_screen(self) -> QWidget:
        """Create home screen with main menu"""
        home = QWidget()
        layout = QVBoxLayout(home)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Let's Learn and Play!")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(30)

        # Stats display
        stats = self.create_stats_widget()
        layout.addWidget(stats)

        layout.addSpacing(30)

        # Start reading button
        start_btn = QPushButton("Start Reading")
        start_btn.setMinimumSize(200, 60)
        start_btn.setFont(QFont("Arial", 16))
        start_btn.clicked.connect(lambda: self.start_reading_session())
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Play games button
        self.play_games_btn = QPushButton("Play Games")
        self.play_games_btn.setMinimumSize(200, 60)
        self.play_games_btn.setFont(QFont("Arial", 16))
        self.play_games_btn.clicked.connect(self.launch_game)
        self.play_games_btn.setEnabled(self.game_tracker.get_time_balance() > 0)
        layout.addWidget(self.play_games_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return home

    def create_stats_widget(self) -> QWidget:
        """Create widget showing progress stats"""
        stats = QWidget()
        layout = QVBoxLayout(stats)

        # Quizzes completed
        quiz_label = QLabel(f"Quizzes Completed: {self.profile.total_quizzes}")
        quiz_label.setFont(QFont("Arial", 14))
        quiz_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(quiz_label)

        # Current streak
        recent_attempts = self.db.get_recent_attempts(10)
        streak = self.progress_tracker.calculate_streak(recent_attempts)
        if streak > 0:
            streak_label = QLabel(f"Current Streak: {streak} in a row!")
            streak_label.setFont(QFont("Arial", 14))
            streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(streak_label)

        # Game time available
        time_balance = self.game_tracker.get_time_balance()
        time_label = QLabel(f"Game Time Available: {time_balance} minutes")
        time_label.setFont(QFont("Arial", 14))
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        return stats

    def setup_menu(self):
        """Setup application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close_app)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        parent_action = QAction("Parent Controls", self)
        parent_action.triggered.connect(self.show_parent_panel)
        settings_menu.addAction(parent_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        phone_action = QAction("Phone Control URL", self)
        phone_action.triggered.connect(self.show_phone_url)
        help_menu.addAction(phone_action)

    def start_reading_session(self, difficulty_level: int = None):
        """Start a new reading session"""
        level = difficulty_level if difficulty_level is not None else self.difficulty_mgr.current_level

        # Generate new passage
        if self.content_gen:
            try:
                passage = self.content_gen.generate_passage(
                    difficulty_level=level,
                    topic="random"
                )
            except Exception:
                passage = self.db.get_random_passage_by_level(level)
        else:
            passage = None

        if passage is None:
            passage = self.db.get_random_passage_by_level(level)

        passage.id = self.db.save_passage(passage)

        # Show reading widget
        self.reading_widget.set_passage(passage)
        self.stacked_widget.setCurrentWidget(self.reading_widget)

    def start_quiz(self, passage):
        """Start quiz for the passage"""
        self.quiz_widget.start_quiz(passage, self.quiz_engine)
        self.stacked_widget.setCurrentWidget(self.quiz_widget)

    def handle_quiz_finished(self, attempt):
        """Handle quiz completion"""
        # Save attempt to database
        attempt.id = self.db.save_quiz_attempt(attempt)

        # Update profile
        self.profile.total_quizzes += 1
        self.db.update_profile(self.profile)

        # Check if quiz passed
        passed = self.quiz_engine.check_passing(attempt)

        # Award game time if passed
        time_earned = 0
        if passed:
            time_earned = self.game_tracker.earn_time_from_quiz(True, 60)
            self._warned_thresholds.clear()  # reset warnings for new session

        # Adjust difficulty
        recent_attempts = self.db.get_recent_attempts(5)
        new_level, difficulty_msg = self.difficulty_mgr.adjust_difficulty(recent_attempts)

        if new_level != self.profile.current_level:
            self.profile.current_level = new_level
            self.db.update_profile(self.profile)

        # Show results
        self.show_results(attempt, passed, time_earned, difficulty_msg)

        # Check for milestones
        milestone_reached, milestone_msg = self.progress_tracker.check_milestone(
            self.profile.total_quizzes
        )
        if milestone_reached:
            QMessageBox.information(self, "Milestone!", milestone_msg)

        # Update UI
        self.update_ui()

        # If failed, offer a new easier passage so the kid can still earn game time
        if not passed:
            self.offer_new_passage()
        else:
            self.stacked_widget.setCurrentWidget(self.home_screen)

    def show_results(self, attempt, passed, time_earned, difficulty_msg):
        """Show quiz results dialog"""
        score_pct = attempt.score * 100
        feedback = self.quiz_engine.get_performance_feedback(attempt)

        message = f"{feedback}\n\n"
        message += f"Score: {attempt.questions_correct}/{attempt.questions_total} ({score_pct:.1f}%)\n"
        message += f"Time: {attempt.time_taken} seconds\n\n"

        if passed:
            message += f"You earned {time_earned} minutes of game time!\n\n"
        else:
            message += "You need 80% to earn game time.\n"
            message += "A new, easier story will be ready for you to try!\n\n"

        message += difficulty_msg

        QMessageBox.information(self, "Quiz Complete!", message)

    def offer_new_passage(self):
        """Offer a new easier passage after a failed quiz so the kid can still earn game time"""
        easier_level = max(1, self.difficulty_mgr.current_level - 1)

        reply = QMessageBox.question(
            self, "Try a New Story?",
            "Don't give up! Would you like to try a new, easier story to earn game time?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.start_reading_session(difficulty_level=easier_level)
        else:
            self.stacked_widget.setCurrentWidget(self.home_screen)

    def update_ui(self):
        """Update UI elements with current data"""
        # Update header
        level_text = self.difficulty_mgr.get_level_description()
        self.level_label.setText(level_text)

        # Update timer
        self.timer_widget.update_time(self.game_tracker.get_time_balance())

        # Update home screen stats
        self.home_screen = self.create_home_screen()
        self.stacked_widget.removeWidget(self.stacked_widget.widget(0))
        self.stacked_widget.insertWidget(0, self.home_screen)

        # Enable/disable play button
        self.play_games_btn.setEnabled(self.game_tracker.get_time_balance() > 0)

    def _update_window_lock(self, balance: int):
        """
        When balance == 0: app stays on top of everything and cannot be minimized.
        When balance  > 0: app behaves normally so the kid can use the browser/game.
        Only changes the window flag when the state actually changes to avoid flicker.
        """
        should_lock = (balance <= 0)
        if should_lock == self._always_on_top:
            return  # No change needed

        self._always_on_top = should_lock
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, should_lock)
        # Re-show is required for the flag change to take effect on all platforms
        self.show()
        if should_lock:
            self.activateWindow()
            self.raise_()

    def update_game_time(self):
        """Update game time display and enforce browser/game time limits (called every second)."""
        controller = self.game_tracker.controller

        # Keep browser session state in sync
        browser_running = controller.check_and_update_browser()

        balance = self.game_tracker.get_time_balance()
        self.timer_widget.update_time(balance)
        self.play_games_btn.setEnabled(balance > 0)

        # Keep always-on-top / minimize-lock in sync with current balance
        self._update_window_lock(balance)

        # No time available — kill browsers, Minecraft Education, and Steam immediately
        if balance <= 0:
            blocked_found = controller.detect_and_stop_blocked_apps()
            if blocked_found or browser_running:
                self.db.use_game_time(0)  # flush any remaining DB record
                QMessageBox.warning(
                    self, "Time's Up!",
                    "Your game time has run out!\nBrowser/games have been closed.\n\nComplete more reading tasks to earn more time!"
                )
                self._warned_thresholds.clear()
            return

        # Low-time warnings (only show each threshold once per session)
        if browser_running or controller.is_game_running:
            for threshold in (5, 1):
                if balance <= threshold and threshold not in self._warned_thresholds:
                    self._warned_thresholds.add(threshold)
                    QMessageBox.warning(
                        self, "Time Running Low!",
                        f"Only {balance} minute(s) of game time left!\nPlease start wrapping up."
                    )

    def launch_game(self):
        """Launch game selection"""
        QMessageBox.information(self, "Games",
                              "Game launching feature. Parents can configure allowed games in Settings.")

    def show_parent_panel(self):
        """Show parent control panel"""
        # Password protection
        password, ok = QInputDialog.getText(self, "Parent Password",
                                           "Enter parent password:",
                                           QLineEdit.EchoMode.Password)

        if ok and password == "parent123":  # Default password
            panel = ParentPanel(self, self.db, self.game_tracker)
            panel.exec()
        elif ok:
            QMessageBox.warning(self, "Access Denied", "Incorrect password!")

    def show_phone_url(self):
        """Show the URL for phone-based parent control"""
        if self._remote_url:
            QMessageBox.information(
                self, "Phone Control",
                f"Make sure your phone and this computer are on the same Wi-Fi network,\n"
                f"then open this URL in your phone's browser:\n\n"
                f"{self._remote_url}\n\n"
                f"Password is the same as the parent control password (default: parent123)"
            )
        else:
            QMessageBox.warning(self, "Phone Control", "Remote server failed to start. Please make sure the flask package is installed.")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Learn & Play",
                         "Educational App for Children\n\n"
                         "This app helps children improve reading skills\n"
                         "by earning game time through quiz completion.\n\n"
                         "Version 1.0")

    def close_app(self):
        """Close application with confirmation"""
        # Require password to close
        password, ok = QInputDialog.getText(self, "Close Application",
                                           "Enter parent password to close:",
                                           QLineEdit.EchoMode.Password)

        if ok and password == "parent123":
            self.db.close()
            self.close()
        elif ok:
            QMessageBox.warning(self, "Access Denied", "Incorrect password!")

    def moveEvent(self, event):
        """Keep window fully visible on screen — prevent dragging to screen edge."""
        super().moveEvent(event)
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available: QRect = screen.availableGeometry()
        geo = self.frameGeometry()
        x = max(available.left(), min(geo.x(), available.right() - geo.width()))
        y = max(available.top(), min(geo.y(), available.bottom() - geo.height()))
        if x != geo.x() or y != geo.y():
            self.move(x, y)

    def changeEvent(self, event):
        """Prevent minimizing when there is no game time."""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.game_tracker.get_time_balance() <= 0:
                # Immediately restore — kids cannot minimize while time is zero
                self.showNormal()
                self.activateWindow()
                self.raise_()
                event.ignore()
                return
        super().changeEvent(event)

    def _handle_sigterm(self, signum, frame):
        """Called when macOS sends SIGTERM during shutdown/restart/logout."""
        self._system_shutdown = True
        self.close()

    def closeEvent(self, event):
        """Handle window close event"""
        # Allow closing without password during system shutdown/restart/logout
        if self._system_shutdown:
            self.db.close()
            event.accept()
            return

        # Require password to close
        password, ok = QInputDialog.getText(self, "Close Application",
                                           "Enter parent password to close:",
                                           QLineEdit.EchoMode.Password)

        if ok and password == "parent123":
            self.db.close()
            event.accept()
        else:
            event.ignore()

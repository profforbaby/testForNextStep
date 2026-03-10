"""
Game controller for managing game time and launching games
"""
import os
import subprocess
import time
import psutil
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from pathlib import Path


class GameController:
    """Manages game launching and time enforcement"""

    # Browser process names to monitor (Windows)
    BROWSER_PROCESSES = {
        'chrome.exe', 'firefox.exe', 'msedge.exe',
        'opera.exe', 'brave.exe', 'iexplore.exe',
    }

    def __init__(self, time_balance: int = 0):
        """
        Initialize game controller

        Args:
            time_balance: Initial time balance in minutes
        """
        self.time_balance = time_balance
        self.time_used = 0
        self.is_game_running = False
        self.current_game_process = None
        self.game_start_time: Optional[datetime] = None
        self.allowed_games: List[str] = []
        self.timer_callback: Optional[Callable] = None

        # Browser monitoring
        self.browser_monitoring_enabled: bool = True
        self.is_browser_running: bool = False
        self.browser_start_time: Optional[datetime] = None

    def add_time(self, minutes: int):
        """Add earned game time"""
        self.time_balance += minutes

    def get_balance(self) -> int:
        """Get current time balance in minutes, subtracting both game and browser elapsed time."""
        elapsed = 0
        if self.is_game_running and self.game_start_time:
            elapsed += int((datetime.now() - self.game_start_time).total_seconds() / 60)
        if self.browser_monitoring_enabled and self.is_browser_running and self.browser_start_time:
            elapsed += int((datetime.now() - self.browser_start_time).total_seconds() / 60)
        return max(0, self.time_balance - elapsed)

    # ------------------------------------------------------------------
    # Browser monitoring
    # ------------------------------------------------------------------

    def _detect_browser(self) -> bool:
        """Return True if any monitored browser process is currently running."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in self.BROWSER_PROCESSES:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def check_and_update_browser(self) -> bool:
        """
        Call every tick to keep browser session state in sync.

        Returns:
            True if a browser is currently running.
        """
        if not self.browser_monitoring_enabled:
            return False

        browser_detected = self._detect_browser()

        if browser_detected and not self.is_browser_running:
            # Browser just opened — start tracking
            self.is_browser_running = True
            self.browser_start_time = datetime.now()

        elif not browser_detected and self.is_browser_running:
            # Browser was closed by the user — commit elapsed time
            self._commit_browser_time()

        return browser_detected

    def _commit_browser_time(self):
        """Deduct the current browser session from the stored balance and reset state."""
        if self.browser_start_time:
            elapsed = int((datetime.now() - self.browser_start_time).total_seconds() / 60)
            self.time_balance = max(0, self.time_balance - elapsed)
        self.is_browser_running = False
        self.browser_start_time = None

    def stop_browser_processes(self):
        """
        Force-close all monitored browser processes and commit the elapsed time.
        Called when the time balance hits zero.
        """
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and proc.info['name'].lower() in self.BROWSER_PROCESSES:
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self._commit_browser_time()

    def get_browser_session_minutes(self) -> int:
        """Return how many minutes the browser has been open in the current session."""
        if self.is_browser_running and self.browser_start_time:
            return int((datetime.now() - self.browser_start_time).total_seconds() / 60)
        return 0

    def has_time_available(self) -> bool:
        """Check if there's game time available"""
        return self.get_balance() > 0

    def set_allowed_games(self, game_paths: List[str]):
        """
        Set list of allowed games

        Args:
            game_paths: List of full paths to game executables or .app bundles
        """
        self.allowed_games = [g for g in game_paths if os.path.exists(g)]

    def add_allowed_game(self, game_path: str):
        """Add a game to allowed list"""
        if os.path.exists(game_path) and game_path not in self.allowed_games:
            self.allowed_games.append(game_path)

    def remove_allowed_game(self, game_path: str):
        """Remove a game from allowed list"""
        if game_path in self.allowed_games:
            self.allowed_games.remove(game_path)

    def launch_game(self, game_path: str) -> bool:
        """
        Launch a game if it's allowed and time is available

        Args:
            game_path: Path to game executable or .app bundle

        Returns:
            True if game was launched, False otherwise
        """
        # Check if game is allowed
        if game_path not in self.allowed_games:
            print(f"Game not in allowed list: {game_path}")
            return False

        # Check if time is available
        if not self.has_time_available():
            print("No game time available")
            return False

        # Check if a game is already running
        if self.is_game_running:
            print("A game is already running")
            return False

        try:
            # Launch game based on platform
            if game_path.endswith('.app'):
                # macOS app bundle
                self.current_game_process = subprocess.Popen(['open', '-a', game_path])
            else:
                # Regular executable
                self.current_game_process = subprocess.Popen([game_path])

            self.is_game_running = True
            self.game_start_time = datetime.now()
            print(f"Game launched: {game_path}")
            return True

        except Exception as e:
            print(f"Error launching game: {e}")
            return False

    def monitor_game_time(self, warning_callback: Optional[Callable] = None):
        """
        Monitor game time and enforce limits

        Args:
            warning_callback: Function to call when time is running low
                            Receives (minutes_remaining) as argument
        """
        if not self.is_game_running or not self.game_start_time:
            return

        elapsed_minutes = int((datetime.now() - self.game_start_time).total_seconds() / 60)
        remaining_minutes = self.time_balance - elapsed_minutes

        # Warning at 5 minutes
        if remaining_minutes == 5 and warning_callback:
            warning_callback(5)

        # Warning at 1 minute
        if remaining_minutes == 1 and warning_callback:
            warning_callback(1)

        # Time's up!
        if remaining_minutes <= 0:
            self.stop_game()

    def stop_game(self):
        """Stop the currently running game"""
        if not self.is_game_running:
            return

        try:
            if self.current_game_process:
                # Calculate time used
                if self.game_start_time:
                    elapsed = int((datetime.now() - self.game_start_time).total_seconds() / 60)
                    self.time_used += elapsed
                    self.time_balance = max(0, self.time_balance - elapsed)

                # Terminate the process
                self.current_game_process.terminate()
                time.sleep(1)

                # Force kill if still running
                if self.current_game_process.poll() is None:
                    self.current_game_process.kill()

            self.is_game_running = False
            self.current_game_process = None
            self.game_start_time = None
            print("Game stopped")

        except Exception as e:
            print(f"Error stopping game: {e}")

    def is_game_process_running(self, process_name: str) -> bool:
        """
        Check if a specific game process is running

        Args:
            process_name: Name of the process to check

        Returns:
            True if process is running, False otherwise
        """
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def get_running_games(self) -> List[str]:
        """Get list of currently running games from allowed list"""
        running = []
        for game_path in self.allowed_games:
            game_name = os.path.basename(game_path).replace('.app', '').replace('.exe', '')
            if self.is_game_process_running(game_name):
                running.append(game_name)
        return running

    def format_time_remaining(self) -> str:
        """Format remaining time as human-readable string"""
        minutes = self.get_balance()
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}h {mins}m"
        else:
            return f"{mins}m"


class GameTimeTracker:
    """Higher-level game time tracking with database integration"""

    def __init__(self, database):
        """
        Initialize tracker

        Args:
            database: Database instance for persistence
        """
        self.db = database
        self.controller = GameController(time_balance=self.db.get_game_time_balance())

    def earn_time_from_quiz(self, quiz_passed: bool, minutes: int = 60):
        """
        Award game time for passing a quiz

        Args:
            quiz_passed: Whether the quiz was passed
            minutes: Minutes to award (default 60)
        """
        if quiz_passed:
            self.controller.add_time(minutes)
            self.db.add_game_time(minutes)
            return minutes
        return 0

    def start_game_session(self, game_path: str) -> bool:
        """Start a game session"""
        return self.controller.launch_game(game_path)

    def end_game_session(self):
        """End current game session and update database"""
        if self.controller.is_game_running and self.controller.game_start_time:
            elapsed = int((datetime.now() - self.controller.game_start_time).total_seconds() / 60)
            self.db.use_game_time(elapsed)

        self.controller.stop_game()

    def get_time_balance(self) -> int:
        """Get current time balance"""
        return self.controller.get_balance()

    def get_time_summary(self) -> dict:
        """Get summary of game time usage"""
        return {
            'balance': self.controller.get_balance(),
            'formatted': self.controller.format_time_remaining(),
            'is_playing': self.controller.is_game_running,
            'has_time': self.controller.has_time_available()
        }

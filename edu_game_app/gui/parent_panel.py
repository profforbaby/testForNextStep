"""
Parent control panel for settings and configuration
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QListWidget, QTabWidget,
                              QWidget, QTextEdit, QFileDialog, QSpinBox,
                              QMessageBox, QTableWidget, QTableWidgetItem,
                              QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ParentPanel(QDialog):
    """Parent control panel"""

    def __init__(self, parent, database, game_tracker):
        super().__init__(parent)
        self.db = database
        self.game_tracker = game_tracker
        self.setWindowTitle("Parent Controls")
        self.setMinimumSize(600, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Parent Control Panel")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()

        # Settings tab
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "Settings")

        # Games tab
        games_tab = self.create_games_tab()
        tabs.addTab(games_tab, "Allowed Games")

        # Progress tab
        progress_tab = self.create_progress_tab()
        tabs.addTab(progress_tab, "Progress Report")

        # Time management tab
        time_tab = self.create_time_tab()
        tabs.addTab(time_tab, "Time Management")

        # Browser control tab
        browser_tab = self.create_browser_tab()
        tabs.addTab(browser_tab, "Browser Control")

        layout.addWidget(tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Child name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Child's Name:"))
        self.name_input = QLineEdit()
        profile = self.db.get_or_create_profile()
        self.name_input.setText(profile.name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addSpacing(20)

        # API Key section
        layout.addWidget(QLabel("Anthropic API Key (for AI-generated content):"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter Anthropic API key...")
        layout.addWidget(self.api_key_input)

        api_info = QLabel("Note: Get API key from https://console.anthropic.com/settings/keys\n"
                         "Set as environment variable ANTHROPIC_API_KEY")
        api_info.setWordWrap(True)
        api_info.setFont(QFont("Arial", 9))
        layout.addWidget(api_info)

        layout.addStretch()

        return tab

    def create_games_tab(self) -> QWidget:
        """Create games management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Allowed Games:"))

        # Games list
        self.games_list = QListWidget()
        for game in self.game_tracker.controller.allowed_games:
            self.games_list.addItem(game)
        layout.addWidget(self.games_list)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Game")
        add_btn.clicked.connect(self.add_game)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_game)
        btn_layout.addWidget(remove_btn)

        layout.addLayout(btn_layout)

        # Instructions
        instructions = QLabel(
            "Add games your child can play after earning time.\n"
            "On macOS: Select .app bundles from /Applications\n"
            "Examples: Minecraft.app, Roblox.app, etc."
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Arial", 9))
        layout.addWidget(instructions)

        return tab

    def create_progress_tab(self) -> QWidget:
        """Create progress report tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Get profile and recent attempts
        profile = self.db.get_or_create_profile()
        recent_attempts = self.db.get_recent_attempts(20)

        # Summary stats
        stats = QLabel(
            f"Total Quizzes: {profile.total_quizzes}\n"
            f"Current Level: {profile.current_level}\n"
            f"Game Time Balance: {self.game_tracker.get_time_balance()} minutes"
        )
        stats.setFont(QFont("Arial", 12))
        layout.addWidget(stats)

        layout.addSpacing(10)

        # Recent attempts table
        layout.addWidget(QLabel("Recent Quiz Attempts:"))

        self.attempts_table = QTableWidget()
        self.attempts_table.setColumnCount(5)
        self.attempts_table.setHorizontalHeaderLabels(
            ["Date", "Level", "Score", "Questions", "Time"]
        )

        self.attempts_table.setRowCount(len(recent_attempts))
        for i, attempt in enumerate(recent_attempts):
            self.attempts_table.setItem(i, 0, QTableWidgetItem(
                attempt.date.strftime("%Y-%m-%d %H:%M")
            ))
            self.attempts_table.setItem(i, 1, QTableWidgetItem(
                str(attempt.difficulty_level)
            ))
            self.attempts_table.setItem(i, 2, QTableWidgetItem(
                f"{attempt.score * 100:.1f}%"
            ))
            self.attempts_table.setItem(i, 3, QTableWidgetItem(
                f"{attempt.questions_correct}/{attempt.questions_total}"
            ))
            self.attempts_table.setItem(i, 4, QTableWidgetItem(
                f"{attempt.time_taken}s"
            ))

        layout.addWidget(self.attempts_table)

        # Export button
        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        layout.addWidget(export_btn)

        return tab

    def create_time_tab(self) -> QWidget:
        """Create time management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Current balance
        balance_label = QLabel(
            f"Current Balance: {self.game_tracker.get_time_balance()} minutes"
        )
        balance_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(balance_label)

        layout.addSpacing(20)

        # Manual adjustment
        layout.addWidget(QLabel("Manual Time Adjustment:"))

        adjust_layout = QHBoxLayout()

        self.time_spinbox = QSpinBox()
        self.time_spinbox.setMinimum(-1000)
        self.time_spinbox.setMaximum(1000)
        self.time_spinbox.setSuffix(" minutes")
        adjust_layout.addWidget(self.time_spinbox)

        adjust_btn = QPushButton("Adjust Time")
        adjust_btn.clicked.connect(self.adjust_time)
        adjust_layout.addWidget(adjust_btn)

        layout.addLayout(adjust_layout)

        layout.addSpacing(10)

        reset_btn = QPushButton("Reset All Time to 0")
        reset_btn.clicked.connect(self.reset_time)
        layout.addWidget(reset_btn)

        layout.addStretch()

        # Info
        info = QLabel(
            "Note: Children earn 60 minutes for each quiz passed (≥80%).\n"
            "Use manual adjustment sparingly for special circumstances."
        )
        info.setWordWrap(True)
        info.setFont(QFont("Arial", 9))
        layout.addWidget(info)

        return tab

    def create_browser_tab(self) -> QWidget:
        """Create browser monitoring control tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        controller = self.game_tracker.controller

        # --- Enable / disable toggle ---
        self.browser_monitor_checkbox = QCheckBox("啟用瀏覽器時間監控（瀏覽器使用時間從遊戲時間中扣除）")
        self.browser_monitor_checkbox.setFont(QFont("Arial", 12))
        self.browser_monitor_checkbox.setChecked(controller.browser_monitoring_enabled)
        self.browser_monitor_checkbox.toggled.connect(self.toggle_browser_monitoring)
        layout.addWidget(self.browser_monitor_checkbox)

        layout.addSpacing(10)

        # --- Current status ---
        status_group = QGroupBox("目前狀態")
        status_layout = QVBoxLayout(status_group)

        browser_active = controller.is_browser_running
        session_mins = controller.get_browser_session_minutes()

        status_text = "瀏覽器：正在使用中" if browser_active else "瀏覽器：未開啟"
        if browser_active:
            status_text += f"（本次已使用 {session_mins} 分鐘）"
        self.browser_status_label = QLabel(status_text)
        self.browser_status_label.setFont(QFont("Arial", 11))
        status_layout.addWidget(self.browser_status_label)

        balance_text = f"剩餘遊戲時間（含瀏覽器）：{self.game_tracker.get_time_balance()} 分鐘"
        self.browser_balance_label = QLabel(balance_text)
        self.browser_balance_label.setFont(QFont("Arial", 11))
        status_layout.addWidget(self.browser_balance_label)

        layout.addWidget(status_group)

        layout.addSpacing(10)

        # --- Monitored browser list ---
        browsers_group = QGroupBox("監控中的瀏覽器程序")
        browsers_layout = QVBoxLayout(browsers_group)

        for name in sorted(controller.BROWSER_PROCESSES):
            browsers_layout.addWidget(QLabel(f"  • {name}"))

        info = QLabel("（如需新增其他瀏覽器，請聯絡開發者修改設定）")
        info.setFont(QFont("Arial", 9))
        info.setWordWrap(True)
        browsers_layout.addWidget(info)

        layout.addWidget(browsers_group)

        layout.addSpacing(10)

        # --- Manual close button ---
        close_btn = QPushButton("立即關閉所有瀏覽器")
        close_btn.setFont(QFont("Arial", 12))
        close_btn.clicked.connect(self.force_close_browsers)
        layout.addWidget(close_btn)

        layout.addStretch()

        note = QLabel(
            "說明：瀏覽器使用時間與遊戲時間共用同一個時間額度。\n"
            "當時間耗盡時，瀏覽器將自動被關閉。"
        )
        note.setWordWrap(True)
        note.setFont(QFont("Arial", 9))
        layout.addWidget(note)

        return tab

    def toggle_browser_monitoring(self, enabled: bool):
        """Enable or disable browser monitoring"""
        self.game_tracker.controller.browser_monitoring_enabled = enabled
        state = "已啟用" if enabled else "已停用"
        QMessageBox.information(self, "設定已儲存", f"瀏覽器監控{state}。")

    def force_close_browsers(self):
        """Force-close all browser processes immediately"""
        reply = QMessageBox.question(
            self, "確認關閉",
            "確定要立即關閉所有瀏覽器嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.game_tracker.controller.stop_browser_processes()
            QMessageBox.information(self, "完成", "所有瀏覽器已關閉。")

    def save_settings(self):
        """Save settings"""
        profile = self.db.get_or_create_profile()
        profile.name = self.name_input.text()
        self.db.update_profile(profile)

        QMessageBox.information(self, "Success", "Settings saved!")

        # Update parent window
        if self.parent():
            self.parent().welcome_label.setText(f"Welcome, {profile.name}!")

    def add_game(self):
        """Add allowed game"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Game",
            "/Applications",
            "Applications (*.app);;All Files (*)"
        )

        if file_path:
            self.game_tracker.controller.add_allowed_game(file_path)
            self.games_list.addItem(file_path)

    def remove_game(self):
        """Remove selected game"""
        current_item = self.games_list.currentItem()
        if current_item:
            game_path = current_item.text()
            self.game_tracker.controller.remove_allowed_game(game_path)
            self.games_list.takeItem(self.games_list.row(current_item))

    def adjust_time(self):
        """Adjust time balance"""
        minutes = self.time_spinbox.value()
        if minutes > 0:
            self.game_tracker.controller.add_time(minutes)
            self.db.add_game_time(minutes)
        elif minutes < 0:
            self.db.use_game_time(abs(minutes))
            self.game_tracker.controller.time_balance = self.db.get_game_time_balance()

        QMessageBox.information(self, "Success",
                              f"Time adjusted by {minutes} minutes!")

        # Refresh display
        self.accept()

    def reset_time(self):
        """Reset all time to 0"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all game time to 0?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            current_balance = self.game_tracker.get_time_balance()
            if current_balance > 0:
                self.db.use_game_time(current_balance)
                self.game_tracker.controller.time_balance = 0

            QMessageBox.information(self, "Success", "Time reset to 0!")
            self.accept()

    def export_report(self):
        """Export progress report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            "progress_report.txt",
            "Text Files (*.txt)"
        )

        if file_path:
            profile = self.db.get_or_create_profile()
            attempts = self.db.get_recent_attempts(100)

            with open(file_path, 'w') as f:
                f.write("Educational App - Progress Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Child: {profile.name}\n")
                f.write(f"Total Quizzes: {profile.total_quizzes}\n")
                f.write(f"Current Level: {profile.current_level}\n\n")
                f.write("Recent Attempts:\n")
                f.write("-" * 50 + "\n")

                for attempt in attempts:
                    f.write(f"{attempt.date.strftime('%Y-%m-%d %H:%M')} | "
                           f"Level {attempt.difficulty_level} | "
                           f"Score: {attempt.score * 100:.1f}% | "
                           f"{attempt.questions_correct}/{attempt.questions_total}\n")

            QMessageBox.information(self, "Success",
                                  f"Report exported to {file_path}")

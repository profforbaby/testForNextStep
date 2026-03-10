"""
Quiz widget for answering questions
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QRadioButton, QButtonGroup,
                              QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class QuizWidget(QWidget):
    """Widget for taking quizzes"""

    quiz_finished = pyqtSignal(object)  # Emits QuizAttempt when done

    def __init__(self):
        super().__init__()
        self.passage = None
        self.quiz_engine = None
        self.quiz_session = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        layout.addSpacing(10)

        # Question number and text
        self.question_label = QLabel()
        self.question_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)

        layout.addSpacing(20)

        # Answer options
        self.answer_group = QButtonGroup()
        self.answer_buttons = []

        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            btn = QRadioButton()
            btn.setFont(QFont("Arial", 14))
            btn.toggled.connect(self.on_answer_selected)
            self.answer_group.addButton(btn, i)
            self.answer_buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacing(30)
        layout.addStretch()

        # Navigation buttons
        button_layout = QHBoxLayout()

        self.prev_button = QPushButton("← Previous")
        self.prev_button.setMinimumHeight(50)
        self.prev_button.setFont(QFont("Arial", 12))
        self.prev_button.clicked.connect(self.previous_question)
        button_layout.addWidget(self.prev_button)

        button_layout.addStretch()

        self.next_button = QPushButton("Next →")
        self.next_button.setMinimumHeight(50)
        self.next_button.setFont(QFont("Arial", 12))
        self.next_button.clicked.connect(self.next_question)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)

        self.submit_button = QPushButton("Submit Quiz")
        self.submit_button.setMinimumHeight(50)
        self.submit_button.setFont(QFont("Arial", 12))
        self.submit_button.clicked.connect(self.submit_quiz)
        self.submit_button.setVisible(False)
        self.submit_button.setEnabled(False)
        button_layout.addWidget(self.submit_button)

        layout.addLayout(button_layout)

    def start_quiz(self, passage, quiz_engine):
        """Start a new quiz"""
        self.passage = passage
        self.quiz_engine = quiz_engine
        self.quiz_session = quiz_engine.start_quiz(passage)

        # Setup progress bar
        total_questions = len(passage.questions)
        self.progress_bar.setMaximum(total_questions)
        self.progress_bar.setValue(0)

        # Show first question
        self.display_question()

    def display_question(self):
        """Display current question"""
        question = self.quiz_session.get_current_question()
        if not question:
            return

        # Update question number and text
        current_num = self.quiz_session.current_question_index + 1
        total = len(self.quiz_session.questions)
        self.question_label.setText(
            f"Question {current_num} of {total}:\n\n{question.question_text}"
        )

        # Update answer options - disable exclusive temporarily so all buttons can be unchecked
        self.answer_group.setExclusive(False)
        options = question.get_options()
        for i, (btn, option) in enumerate(zip(self.answer_buttons, options)):
            btn.setText(f"{chr(65 + i)}. {option}")
            btn.setChecked(False)
        self.answer_group.setExclusive(True)

        # Restore previous answer if exists
        previous_answer = self.quiz_session.get_answer()
        if previous_answer:
            answer_index = ord(previous_answer) - ord('A')
            if 0 <= answer_index < len(self.answer_buttons):
                self.answer_buttons[answer_index].setChecked(True)
                self.next_button.setEnabled(True)

        # Update button states
        self.prev_button.setEnabled(self.quiz_session.current_question_index > 0)

        # Show submit button on last question
        is_last = self.quiz_session.current_question_index == len(self.quiz_session.questions) - 1
        self.next_button.setVisible(not is_last)
        self.submit_button.setVisible(is_last)

        # Enable submit button only if last question is answered
        if is_last:
            is_answered = self.quiz_session.is_question_answered()
            self.submit_button.setEnabled(is_answered)
        else:
            # Reset next button state if no answer selected yet
            if not previous_answer:
                self.next_button.setEnabled(False)

        # Update progress
        answered, total = self.quiz_session.get_progress()
        self.progress_bar.setValue(answered)

    def on_answer_selected(self, checked):
        """Handle answer selection"""
        # Only process when a button is being checked (not unchecked)
        if not checked:
            return

        # Get selected answer
        selected_id = self.answer_group.checkedId()
        if selected_id >= 0:
            answer = chr(65 + selected_id)  # Convert to A, B, C, D
            self.quiz_session.answer_question(answer)

            # Enable appropriate navigation button
            is_last = self.quiz_session.current_question_index == len(self.quiz_session.questions) - 1
            if is_last:
                self.submit_button.setEnabled(True)
            else:
                self.next_button.setEnabled(True)

            # Update progress
            answered, total = self.quiz_session.get_progress()
            self.progress_bar.setValue(answered)

    def next_question(self):
        """Move to next question"""
        if self.quiz_session.next_question():
            self.display_question()

    def previous_question(self):
        """Move to previous question"""
        if self.quiz_session.previous_question():
            self.display_question()

    def submit_quiz(self):
        """Submit quiz and show results"""
        if not self.quiz_session.is_complete():
            # Warn about unanswered questions
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "Incomplete Quiz",
                                        "You haven't answered all questions. Submit anyway?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                return

        # Finish quiz
        attempt = self.quiz_session.finish_quiz()
        self.quiz_finished.emit(attempt)

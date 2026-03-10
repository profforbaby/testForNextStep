"""
Quiz engine for managing quiz sessions and scoring
"""
from datetime import datetime
from typing import List, Dict, Optional
from edu_game_app.data.models import Passage, Question, QuizAttempt


class QuizSession:
    """Manages a single quiz session"""

    def __init__(self, passage: Passage):
        """Initialize quiz session with a passage"""
        self.passage = passage
        self.questions = passage.questions
        self.current_question_index = 0
        self.answers: Dict[int, str] = {}  # question_index -> answer
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.score: float = 0.0

    def get_current_question(self) -> Optional[Question]:
        """Get the current question"""
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None

    def answer_question(self, answer: str) -> bool:
        """
        Answer the current question

        Args:
            answer: The selected answer (A, B, C, or D)

        Returns:
            True if answer was recorded, False if no current question
        """
        if self.current_question_index < len(self.questions):
            self.answers[self.current_question_index] = answer
            return True
        return False

    def next_question(self) -> bool:
        """
        Move to next question

        Returns:
            True if moved to next question, False if quiz is complete
        """
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            return True
        return False

    def previous_question(self) -> bool:
        """
        Move to previous question

        Returns:
            True if moved to previous question, False if already at first
        """
        if self.current_question_index > 0:
            self.current_question_index -= 1
            return True
        return False

    def is_question_answered(self, index: Optional[int] = None) -> bool:
        """Check if a question has been answered"""
        if index is None:
            index = self.current_question_index
        return index in self.answers

    def get_answer(self, index: Optional[int] = None) -> Optional[str]:
        """Get answer for a specific question"""
        if index is None:
            index = self.current_question_index
        return self.answers.get(index)

    def get_progress(self) -> tuple[int, int]:
        """
        Get quiz progress

        Returns:
            Tuple of (questions_answered, total_questions)
        """
        return len(self.answers), len(self.questions)

    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return len(self.answers) == len(self.questions)

    def calculate_score(self) -> tuple[float, int, int]:
        """
        Calculate quiz score

        Returns:
            Tuple of (score_percentage, correct_count, total_count)
        """
        if not self.is_complete():
            return 0.0, 0, len(self.questions)

        correct = 0
        total = len(self.questions)

        for i, question in enumerate(self.questions):
            if i in self.answers:
                if question.is_correct(self.answers[i]):
                    correct += 1

        self.score = (correct / total) if total > 0 else 0.0
        return self.score, correct, total

    def finish_quiz(self) -> QuizAttempt:
        """
        Finish the quiz and create attempt record

        Returns:
            QuizAttempt object with results
        """
        self.end_time = datetime.now()
        score, correct, total = self.calculate_score()

        time_taken = int((self.end_time - self.start_time).total_seconds())

        attempt = QuizAttempt(
            date=self.end_time,
            passage_id=self.passage.id if self.passage.id else 0,
            difficulty_level=self.passage.difficulty_level,
            score=score,
            time_taken=time_taken,
            questions_total=total,
            questions_correct=correct
        )

        return attempt

    def get_results_summary(self) -> Dict:
        """Get detailed results summary"""
        score, correct, total = self.calculate_score()

        results = {
            'score_percentage': round(score * 100, 1),
            'correct_count': correct,
            'total_count': total,
            'time_taken': int((datetime.now() - self.start_time).total_seconds()),
            'passed': score >= 0.8,
            'questions': []
        }

        for i, question in enumerate(self.questions):
            user_answer = self.answers.get(i, '')
            is_correct = question.is_correct(user_answer) if user_answer else False

            results['questions'].append({
                'question': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct
            })

        return results


class QuizEngine:
    """Main quiz engine for managing quiz flow"""

    PASSING_SCORE = 0.80  # 80% required to pass

    def __init__(self):
        """Initialize quiz engine"""
        self.current_session: Optional[QuizSession] = None

    def start_quiz(self, passage: Passage) -> QuizSession:
        """
        Start a new quiz session

        Args:
            passage: The passage with questions

        Returns:
            New QuizSession object
        """
        self.current_session = QuizSession(passage)
        return self.current_session

    def get_current_session(self) -> Optional[QuizSession]:
        """Get the current active quiz session"""
        return self.current_session

    def submit_answer(self, answer: str) -> bool:
        """Submit answer for current question"""
        if self.current_session:
            return self.current_session.answer_question(answer)
        return False

    def next_question(self) -> bool:
        """Move to next question"""
        if self.current_session:
            return self.current_session.next_question()
        return False

    def finish_quiz(self) -> Optional[QuizAttempt]:
        """Finish current quiz and get results"""
        if self.current_session:
            return self.current_session.finish_quiz()
        return None

    def check_passing(self, attempt: QuizAttempt) -> bool:
        """Check if quiz attempt passed"""
        return attempt.score >= self.PASSING_SCORE

    def calculate_time_earned(self, attempt: QuizAttempt) -> int:
        """
        Calculate game time earned from quiz

        Args:
            attempt: The quiz attempt

        Returns:
            Minutes of game time earned (60 if passed, 0 if failed)
        """
        if self.check_passing(attempt):
            return 60  # 1 hour for passing
        return 0

    def get_performance_feedback(self, attempt: QuizAttempt) -> str:
        """Get personalized feedback based on performance"""
        score_pct = attempt.score * 100

        if score_pct >= 100:
            return "Perfect! You're a reading superstar! 🌟"
        elif score_pct >= 90:
            return "Excellent work! You really understood the story! 🎉"
        elif score_pct >= 80:
            return "Great job! You passed and earned game time! ✅"
        elif score_pct >= 70:
            return "Good effort! Just a little more to pass. Try again! 💪"
        elif score_pct >= 60:
            return "Nice try! Let's read it again more carefully. 📖"
        else:
            return "Keep practicing! You'll get better with each try! 🌱"

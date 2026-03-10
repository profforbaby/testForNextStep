"""
Data models for the educational app
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ChildProfile:
    """Child user profile"""
    id: Optional[int] = None
    name: str = "Student"
    current_level: int = 1
    total_quizzes: int = 0
    created_date: datetime = None

    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()


@dataclass
class Question:
    """Quiz question"""
    id: Optional[int] = None
    passage_id: int = 0
    question_text: str = ""
    correct_answer: str = ""
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    question_type: str = "multiple_choice"

    def get_options(self) -> List[str]:
        """Return list of answer options"""
        return [self.option_a, self.option_b, self.option_c, self.option_d]

    def is_correct(self, answer: str) -> bool:
        """Check if answer is correct"""
        return answer.strip().lower() == self.correct_answer.strip().lower()


@dataclass
class Passage:
    """Reading passage"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    difficulty_level: int = 1
    word_count: int = 0
    topic: str = "general"
    questions: List[Question] = None

    def __post_init__(self):
        if self.questions is None:
            self.questions = []
        if self.word_count == 0:
            self.word_count = len(self.content.split())


@dataclass
class QuizAttempt:
    """Record of a quiz attempt"""
    id: Optional[int] = None
    date: datetime = None
    passage_id: int = 0
    difficulty_level: int = 1
    score: float = 0.0
    time_taken: int = 0
    questions_total: int = 0
    questions_correct: int = 0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()

    def passed(self, threshold: float = 0.8) -> bool:
        """Check if quiz passed"""
        return self.score >= threshold


@dataclass
class GameSession:
    """Game time tracking"""
    id: Optional[int] = None
    date: datetime = None
    minutes_earned: int = 0
    minutes_used: int = 0
    balance: int = 0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()

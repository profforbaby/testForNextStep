"""
Database operations for the educational app
"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from edu_game_app.data.models import ChildProfile, Passage, Question, QuizAttempt, GameSession


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str = "edu_app.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize database and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Child profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS child_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_level INTEGER DEFAULT 1,
                total_quizzes INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Passages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                difficulty_level INTEGER DEFAULT 1,
                word_count INTEGER,
                topic TEXT DEFAULT 'general'
            )
        ''')

        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passage_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                question_type TEXT DEFAULT 'multiple_choice',
                FOREIGN KEY (passage_id) REFERENCES passages(id)
            )
        ''')

        # Quiz attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                passage_id INTEGER,
                difficulty_level INTEGER,
                score REAL,
                time_taken INTEGER,
                questions_total INTEGER,
                questions_correct INTEGER,
                FOREIGN KEY (passage_id) REFERENCES passages(id)
            )
        ''')

        # Game sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                minutes_earned INTEGER DEFAULT 0,
                minutes_used INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()

    def get_or_create_profile(self, name: str = "Student") -> ChildProfile:
        """Get existing profile or create new one"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM child_profile LIMIT 1")
        row = cursor.fetchone()

        if row:
            return ChildProfile(
                id=row['id'],
                name=row['name'],
                current_level=row['current_level'],
                total_quizzes=row['total_quizzes'],
                created_date=datetime.fromisoformat(row['created_date'])
            )
        else:
            # Create new profile
            cursor.execute(
                "INSERT INTO child_profile (name, current_level, total_quizzes) VALUES (?, ?, ?)",
                (name, 1, 0)
            )
            self.conn.commit()
            return self.get_or_create_profile(name)

    def update_profile(self, profile: ChildProfile):
        """Update child profile"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE child_profile
            SET name = ?, current_level = ?, total_quizzes = ?
            WHERE id = ?
        ''', (profile.name, profile.current_level, profile.total_quizzes, profile.id))
        self.conn.commit()

    def save_passage(self, passage: Passage) -> int:
        """Save passage and its questions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO passages (title, content, difficulty_level, word_count, topic)
            VALUES (?, ?, ?, ?, ?)
        ''', (passage.title, passage.content, passage.difficulty_level,
              passage.word_count, passage.topic))
        passage_id = cursor.lastrowid

        # Save questions
        for question in passage.questions:
            cursor.execute('''
                INSERT INTO questions (passage_id, question_text, correct_answer,
                                     option_a, option_b, option_c, option_d, question_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (passage_id, question.question_text, question.correct_answer,
                  question.option_a, question.option_b, question.option_c,
                  question.option_d, question.question_type))

        self.conn.commit()
        return passage_id

    def get_passage_with_questions(self, passage_id: int) -> Optional[Passage]:
        """Get passage with all its questions"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM passages WHERE id = ?", (passage_id,))
        row = cursor.fetchone()

        if not row:
            return None

        passage = Passage(
            id=row['id'],
            title=row['title'],
            content=row['content'],
            difficulty_level=row['difficulty_level'],
            word_count=row['word_count'],
            topic=row['topic']
        )

        # Get questions
        cursor.execute("SELECT * FROM questions WHERE passage_id = ?", (passage_id,))
        questions = []
        for q_row in cursor.fetchall():
            questions.append(Question(
                id=q_row['id'],
                passage_id=q_row['passage_id'],
                question_text=q_row['question_text'],
                correct_answer=q_row['correct_answer'],
                option_a=q_row['option_a'],
                option_b=q_row['option_b'],
                option_c=q_row['option_c'],
                option_d=q_row['option_d'],
                question_type=q_row['question_type']
            ))
        passage.questions = questions

        return passage

    def save_quiz_attempt(self, attempt: QuizAttempt) -> int:
        """Save quiz attempt"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO quiz_attempts
            (passage_id, difficulty_level, score, time_taken, questions_total, questions_correct)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (attempt.passage_id, attempt.difficulty_level, attempt.score,
              attempt.time_taken, attempt.questions_total, attempt.questions_correct))
        self.conn.commit()
        return cursor.lastrowid

    def get_recent_attempts(self, limit: int = 10) -> List[QuizAttempt]:
        """Get recent quiz attempts"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM quiz_attempts
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))

        attempts = []
        for row in cursor.fetchall():
            attempts.append(QuizAttempt(
                id=row['id'],
                date=datetime.fromisoformat(row['date']),
                passage_id=row['passage_id'],
                difficulty_level=row['difficulty_level'],
                score=row['score'],
                time_taken=row['time_taken'],
                questions_total=row['questions_total'],
                questions_correct=row['questions_correct']
            ))
        return attempts

    def get_game_time_balance(self) -> int:
        """Get current game time balance in minutes"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(balance) as total FROM game_sessions")
        row = cursor.fetchone()
        return row['total'] if row['total'] else 0

    def add_game_time(self, minutes: int):
        """Add earned game time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (minutes_earned, minutes_used, balance)
            VALUES (?, 0, ?)
        ''', (minutes, minutes))
        self.conn.commit()

    def use_game_time(self, minutes: int):
        """Deduct used game time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (minutes_earned, minutes_used, balance)
            VALUES (0, ?, ?)
        ''', (minutes, -minutes))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

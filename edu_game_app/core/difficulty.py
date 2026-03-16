"""
Adaptive difficulty system
Adjusts reading level based on student performance
"""
from typing import List
from edu_game_app.data.models import QuizAttempt


class DifficultyManager:
    """Manages adaptive difficulty levels based on performance"""

    # Difficulty level constraints
    MIN_LEVEL = 1
    MAX_LEVEL = 4

    # Performance thresholds
    EXCELLENT_THRESHOLD = 0.90  # 90% or higher
    POOR_THRESHOLD = 0.70       # Below 70%

    # Number of consecutive attempts to trigger level change
    CONSECUTIVE_FOR_INCREASE = 3
    CONSECUTIVE_FOR_DECREASE = 2

    def __init__(self, current_level: int = 4):
        """Initialize with current difficulty level"""
        self.current_level = max(self.MIN_LEVEL, min(current_level, self.MAX_LEVEL))

    def adjust_difficulty(self, recent_attempts: List[QuizAttempt]) -> tuple[int, str]:
        """
        Adjust difficulty based on recent quiz performance

        Args:
            recent_attempts: List of recent quiz attempts (most recent first)

        Returns:
            Tuple of (new_level, reason_message)
        """
        if not recent_attempts or len(recent_attempts) < 2:
            return self.current_level, "Not enough data to adjust difficulty"

        # Analyze recent performance
        analysis = self._analyze_performance(recent_attempts)

        old_level = self.current_level
        reason = ""

        # Check for level increase (doing too well)
        if analysis['consecutive_excellent'] >= self.CONSECUTIVE_FOR_INCREASE:
            if self.current_level < self.MAX_LEVEL:
                self.current_level += 1
                reason = f"Great job! You got {analysis['consecutive_excellent']} excellent scores in a row. Moving to Level {self.current_level}!"
            else:
                reason = "Excellent work! You're already at the highest level — Primary 6 master!"

        # Check for level decrease (struggling)
        elif analysis['consecutive_poor'] >= self.CONSECUTIVE_FOR_DECREASE:
            if self.current_level > self.MIN_LEVEL:
                self.current_level -= 1
                reason = f"Let's try slightly easier passages. Moving to Level {self.current_level}."
            else:
                reason = "Keep practicing! You're doing fine at this level."

        # No change needed
        else:
            reason = "Current level is just right for you. Keep it up!"

        return self.current_level, reason

    def _analyze_performance(self, attempts: List[QuizAttempt]) -> dict:
        """Analyze performance patterns from recent attempts"""
        analysis = {
            'average_score': 0.0,
            'consecutive_excellent': 0,
            'consecutive_poor': 0,
            'trend': 'stable'
        }

        if not attempts:
            return analysis

        # Calculate average score
        scores = [attempt.score for attempt in attempts[:5]]  # Last 5 attempts
        analysis['average_score'] = sum(scores) / len(scores)

        # Count consecutive excellent scores
        for attempt in attempts:
            if attempt.score >= self.EXCELLENT_THRESHOLD:
                analysis['consecutive_excellent'] += 1
            else:
                break

        # Count consecutive poor scores
        for attempt in attempts:
            if attempt.score < self.POOR_THRESHOLD:
                analysis['consecutive_poor'] += 1
            else:
                break

        # Determine trend
        if len(attempts) >= 3:
            recent_avg = sum(a.score for a in attempts[:3]) / 3
            older_avg = sum(a.score for a in attempts[3:6]) / max(len(attempts[3:6]), 1)

            if recent_avg > older_avg + 0.1:
                analysis['trend'] = 'improving'
            elif recent_avg < older_avg - 0.1:
                analysis['trend'] = 'declining'

        return analysis

    def get_level_description(self, level: int = None) -> str:
        """Get description of a difficulty level"""
        if level is None:
            level = self.current_level

        descriptions = {
            1: "Level 1 (Beginner): Simple sentences with basic words",
            2: "Level 2 (Intermediate): Longer passages with more vocabulary",
            3: "Level 3 (Advanced): Challenging stories with descriptive language",
            4: "Level 4 (Primary 6): 200-300 word passages with inference, vocabulary, and critical thinking"
        }
        return descriptions.get(level, "Unknown level")

    def should_show_encouragement(self, attempt: QuizAttempt) -> tuple[bool, str]:
        """
        Determine if encouragement message should be shown

        Args:
            attempt: The quiz attempt to evaluate

        Returns:
            Tuple of (should_show, message)
        """
        score = attempt.score

        if score >= 1.0:
            return True, "Perfect score! You're a reading star! ⭐"
        elif score >= self.EXCELLENT_THRESHOLD:
            return True, "Excellent work! You really understood that story! 🎉"
        elif score >= 0.80:
            return True, "Good job! You passed! Keep reading! 📚"
        elif score >= 0.60:
            return True, "Nice try! Let's practice a bit more. 💪"
        else:
            return True, "That's okay! Reading takes practice. Try again! 🌟"

    def get_next_level_suggestion(self, recent_attempts: List[QuizAttempt]) -> str:
        """Get suggestion for what student should focus on"""
        if not recent_attempts:
            return "Start with some reading practice!"

        analysis = self._analyze_performance(recent_attempts)

        if analysis['average_score'] >= self.EXCELLENT_THRESHOLD:
            return "You're doing great! Keep challenging yourself!"
        elif analysis['average_score'] >= 0.80:
            return "You're making good progress! Keep practicing!"
        elif analysis['trend'] == 'improving':
            return "You're getting better! Keep up the good work!"
        elif analysis['trend'] == 'declining':
            return "Take your time and read carefully. You've got this!"
        else:
            return "Keep practicing and you'll improve!"

    def estimate_time_to_level_up(self, recent_attempts: List[QuizAttempt]) -> str:
        """Estimate how close student is to next level"""
        if self.current_level >= self.MAX_LEVEL:
            return "You're already at the top level! Amazing!"

        if not recent_attempts:
            return "Complete some quizzes to see your progress!"

        analysis = self._analyze_performance(recent_attempts)
        excellent_count = analysis['consecutive_excellent']

        if excellent_count >= self.CONSECUTIVE_FOR_INCREASE:
            return "Ready to level up after this quiz!"
        else:
            remaining = self.CONSECUTIVE_FOR_INCREASE - excellent_count
            return f"Get {remaining} more excellent score(s) to level up!"


class ProgressTracker:
    """Track learning progress and milestones"""

    def __init__(self):
        self.milestones = {
            5: "🎯 Completed 5 quizzes!",
            10: "🌟 10 quizzes done - You're on fire!",
            25: "🏆 Amazing! 25 quizzes completed!",
            50: "👑 Wow! 50 quizzes - You're a reading champion!",
            100: "🎊 Incredible! 100 quizzes - Reading master!"
        }

    def check_milestone(self, quiz_count: int) -> tuple[bool, str]:
        """
        Check if a milestone was reached

        Args:
            quiz_count: Total number of quizzes completed

        Returns:
            Tuple of (milestone_reached, message)
        """
        if quiz_count in self.milestones:
            return True, self.milestones[quiz_count]
        return False, ""

    def get_progress_message(self, quiz_count: int, current_level: int) -> str:
        """Get overall progress message"""
        return f"You've completed {quiz_count} quizzes at Level {current_level}!"

    def calculate_streak(self, attempts: List[QuizAttempt], passing_score: float = 0.8) -> int:
        """Calculate current streak of passing quizzes"""
        streak = 0
        for attempt in attempts:
            if attempt.score >= passing_score:
                streak += 1
            else:
                break
        return streak

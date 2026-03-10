"""Core module initialization"""
from edu_game_app.core.content_generator import ContentGenerator
from edu_game_app.core.tts_engine import TTSEngine, TextReader
from edu_game_app.core.difficulty import DifficultyManager, ProgressTracker
from edu_game_app.core.quiz_engine import QuizEngine, QuizSession
from edu_game_app.core.game_controller import GameController, GameTimeTracker
from edu_game_app.core.remote_server import start_remote_server

__all__ = [
    'ContentGenerator',
    'TTSEngine',
    'TextReader',
    'DifficultyManager',
    'ProgressTracker',
    'QuizEngine',
    'QuizSession',
    'GameController',
    'GameTimeTracker',
    'start_remote_server',
]

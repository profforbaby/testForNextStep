"""
Text-to-Speech engine for reading assistance
Uses system TTS for natural voice output
"""
import threading
import pyttsx3
from typing import Optional, Callable


class TTSEngine:
    """Text-to-speech engine — runs speech in a background thread to avoid blocking Qt."""

    def __init__(self):
        self.is_speaking = False
        self._rate = 150
        self._volume = 0.9
        self._voice_id: Optional[str] = None
        self._current_engine: Optional[pyttsx3.Engine] = None
        self._lock = threading.Lock()
        self._find_voice()

    def _find_voice(self):
        """Discover a preferred voice ID without keeping an engine alive on the main thread."""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            preferred_names = ['zira', 'samantha', 'karen', 'victoria', 'alex']
            for voice in voices:
                voice_name = voice.name.lower()
                for pref in preferred_names:
                    if pref in voice_name:
                        self._voice_id = voice.id
                        break
                if self._voice_id:
                    break
            engine.stop()
            del engine
        except Exception as e:
            print(f"TTS voice discovery error: {e}")

    def speak(self, text: str, done_callback: Optional[Callable] = None):
        """
        Speak text in a background thread so Qt's event loop is not blocked.

        Args:
            text: Text to speak
            done_callback: Called (from the background thread) when speech finishes or stops
        """
        self.stop()  # cancel any in-progress speech first
        self.is_speaking = True
        t = threading.Thread(target=self._speak_thread, args=(text, done_callback), daemon=True)
        t.start()

    def _speak_thread(self, text: str, done_callback: Optional[Callable]):
        engine = None
        try:
            engine = pyttsx3.init()
            with self._lock:
                self._current_engine = engine
            if self._voice_id:
                engine.setProperty('voice', self._voice_id)
            engine.setProperty('rate', self._rate)
            engine.setProperty('volume', self._volume)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS speak error: {e}")
        finally:
            with self._lock:
                self._current_engine = None
            self.is_speaking = False
            if done_callback:
                done_callback()

    def stop(self):
        """Stop current speech."""
        self.is_speaking = False
        with self._lock:
            if self._current_engine:
                try:
                    self._current_engine.stop()
                except Exception:
                    pass

    def set_rate(self, rate: int):
        self._rate = rate

    def set_volume(self, volume: float):
        self._volume = volume

    def get_available_voices(self) -> list:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            result = [(v.id, v.name, v.languages) for v in voices]
            engine.stop()
            del engine
            return result
        except Exception:
            return []

    def set_voice(self, voice_id: str):
        self._voice_id = voice_id

    def speak_word(self, word: str):
        self.speak(word)

    def speak_sentence(self, sentence: str):
        self.speak(sentence)


class TextReader:
    """Higher-level text reading with highlighting support"""

    def __init__(self):
        self.tts = TTSEngine()
        self.current_text = ""
        self.words = []
        self.current_index = 0

    def read_text(self, text: str, highlight_callback: Optional[Callable] = None,
                  done_callback: Optional[Callable] = None):
        """
        Read text aloud in a background thread.

        Args:
            text: Text to read
            highlight_callback: Unused placeholder (kept for API compatibility)
            done_callback: Called when speech finishes (from background thread)
        """
        self.current_text = text
        self.words = text.split()
        self.current_index = 0
        self.tts.speak(text, done_callback=done_callback)

    def read_word(self, word: str):
        """Read a single word (for help/pronunciation)"""
        self.tts.speak_word(word)

    def read_sentence(self, sentence: str):
        """Read a sentence"""
        self.tts.speak_sentence(sentence)

    def stop(self):
        """Stop reading"""
        self.tts.stop()

    def set_speed(self, speed: str = "normal"):
        """
        Set reading speed

        Args:
            speed: 'slow' (120 wpm), 'normal' (150 wpm), 'fast' (180 wpm)
        """
        speeds = {
            'slow': 120,
            'normal': 150,
            'fast': 180
        }
        rate = speeds.get(speed, 150)
        self.tts.set_rate(rate)

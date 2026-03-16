"""
Text-to-Speech engine for reading assistance
Uses macOS 'say' command on macOS, pyttsx3 on other platforms
"""
import platform
import subprocess
import threading
from typing import Optional, Callable

_IS_MACOS = platform.system() == 'Darwin'


class TTSEngine:
    """Text-to-speech engine — runs speech in a background thread to avoid blocking Qt."""

    def __init__(self):
        self.is_speaking = False
        self._rate = 150  # words per minute
        self._volume = 0.9
        self._voice_id: Optional[str] = None
        self._current_process: Optional[subprocess.Popen] = None  # macOS
        self._lock = threading.Lock()
        if not _IS_MACOS:
            self._find_voice()

    def _find_voice(self):
        """Discover a preferred pyttsx3 voice (non-macOS only)."""
        try:
            import pyttsx3
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
        """Speak text in a background thread so Qt's event loop is not blocked."""
        self.stop()  # cancel any in-progress speech first
        self.is_speaking = True
        t = threading.Thread(target=self._speak_thread, args=(text, done_callback), daemon=True)
        t.start()

    def _speak_thread(self, text: str, done_callback: Optional[Callable]):
        try:
            if _IS_MACOS:
                self._speak_macos(text)
            else:
                self._speak_pyttsx3(text)
        except Exception as e:
            print(f"TTS speak error: {e}")
        finally:
            self.is_speaking = False
            if done_callback:
                done_callback()

    def _speak_macos(self, text: str):
        """Use macOS built-in 'say' command."""
        # Pass text via stdin to avoid argument length limits and character escaping issues.
        # Use DEVNULL for stdout/stderr to avoid inheriting broken file descriptors
        # when the app is launched from a shell script (e.g. run_app.sh via Finder).
        proc = subprocess.Popen(
            ['/usr/bin/say', '-r', str(self._rate)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        with self._lock:
            self._current_process = proc
        _, err = proc.communicate(input=text.encode('utf-8'))
        if proc.returncode != 0:
            print(f"TTS say error (exit {proc.returncode}): {err.decode().strip()}")
        with self._lock:
            self._current_process = None

    def _speak_pyttsx3(self, text: str):
        """Use pyttsx3 on non-macOS platforms."""
        import pyttsx3
        engine = pyttsx3.init()
        if self._voice_id:
            engine.setProperty('voice', self._voice_id)
        engine.setProperty('rate', self._rate)
        engine.setProperty('volume', self._volume)
        engine.say(text)
        engine.runAndWait()

    def stop(self):
        """Stop current speech."""
        self.is_speaking = False
        with self._lock:
            if self._current_process:
                try:
                    self._current_process.terminate()
                except Exception:
                    pass
                self._current_process = None

    def set_rate(self, rate: int):
        self._rate = rate

    def set_volume(self, volume: float):
        self._volume = volume

    def get_available_voices(self) -> list:
        if _IS_MACOS:
            return []  # macOS uses system default voice
        try:
            import pyttsx3
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

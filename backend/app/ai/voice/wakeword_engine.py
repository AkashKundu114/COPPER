import asyncio
import threading
from typing import Callable, Optional
from app.core.config import settings
from app.core.logger import logger

_listening = False
_callback: Optional[Callable] = None


class WakeWordEngine:
    def __init__(self):
        self.wake_word = settings.WAKE_WORD.lower()
        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._on_detected: Optional[Callable] = None

    def set_callback(self, callback: Callable):
        self._on_detected = callback

    def start(self):
        if self._active:
            return
        self._active = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"Wake word engine started, listening for '{self.wake_word}'")

    def stop(self):
        self._active = False
        logger.info("Wake word engine stopped")

    def _listen_loop(self):
        """Continuous microphone listening loop using vosk/pvporcupine or simple keyword detection."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Wake word microphone ready")
                while self._active:
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                        text = recognizer.recognize_google(audio).lower()
                        if self.wake_word in text:
                            logger.info(f"Wake word detected: '{text}'")
                            if self._on_detected:
                                self._on_detected()
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        logger.debug(f"Wake word listen error: {e}")
        except Exception as e:
            logger.error(f"Wake word engine error: {e}")

    def simulate_detection(self):
        """Manually trigger wake word (for testing)."""
        logger.info("Wake word manually triggered")
        if self._on_detected:
            self._on_detected()


wake_engine = WakeWordEngine()

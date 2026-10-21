
"""Optional offline voice input (Vosk) and offline speech output (pyttsx3)."""

import json
import queue
import threading
from pathlib import Path


class VoiceUnavailable(RuntimeError):
    pass


class VoiceEngine:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self._tts_lock = threading.Lock()

    def listen_once(self, seconds: int = 12) -> str:
        if not self.model_path.exists():
            raise VoiceUnavailable(
                f"Vosk model not found at: {self.model_path}\n"
                "Download and extract a Vosk English model, "
                "then set VOSK_MODEL_PATH in .env."
            )

        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer
        except ImportError as exc:
            raise VoiceUnavailable(
                "Voice input dependencies missing. "
                "Run: pip install -r requirements.txt"
            ) from exc

        audio_queue: queue.Queue[bytes] = queue.Queue()
        model = Model(str(self.model_path))
        recognizer = KaldiRecognizer(model, 16000)

        def callback(indata, frames, time_info, status):
            if status:
                pass
            audio_queue.put(bytes(indata))

        try:
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=callback,
            ):
                for _ in range(max(1, int(seconds * 2))):
                    try:
                        data = audio_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    if recognizer.AcceptWaveform(data):
                        text = json.loads(
                            recognizer.Result()
                        ).get("text", "").strip()

                        if text:
                            return text

                return json.loads(
                    recognizer.FinalResult()
                ).get("text", "").strip()

        except Exception as exc:
            raise VoiceUnavailable(
                f"Microphone error: {exc}"
            ) from exc

    def speak(self, text: str) -> None:
        """Speak text using Microsoft Zira, if installed."""
        engine = None

        try:
            import pyttsx3

            with self._tts_lock:
                engine = pyttsx3.init()
                voices = engine.getProperty("voices")

                zira = next(
                    (
                        voice
                        for voice in voices
                        if "zira" in voice.name.lower()
                    ),
                    None,
                )

                if zira is None:
                    raise VoiceUnavailable(
                        "Microsoft Zira was not found. "
                        "Check your installed Windows speech voices."
                    )

                engine.setProperty("voice", zira.id)
                engine.setProperty("rate", 175)
                engine.setProperty("volume", 1.0)

                engine.say(text)
                engine.runAndWait()

        except VoiceUnavailable:
            raise
        except Exception as exc:
            raise VoiceUnavailable(
                f"Text-to-speech error: {exc}"
            ) from exc
        finally:
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass

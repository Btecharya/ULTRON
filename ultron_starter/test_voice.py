from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from ultron.voice import VoiceEngine, VoiceUnavailable

voice = VoiceEngine(Path("."))

try:
    voice.speak(
        "All systems are operational. "
        "I have analyzed the situation. "
        "The outcome is inevitable."
    )
    print("Voice test completed.")
except VoiceUnavailable as exc:
    print(f"Voice error: {exc}")

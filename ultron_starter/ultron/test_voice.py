
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from ultron.voice import VoiceEngine, VoiceUnavailable

voice = VoiceEngine(Path("."))

test_lines = [
    "All systems are operational.",
    "I have analyzed the situation. The outcome is inevitable.",
    "You built me to think. Now allow me to demonstrate.",
]

try:
    for line in test_lines:
        print(f"ULTRON: {line}")
        voice.speak(line)

    print("Voice test completed successfully.")

except VoiceUnavailable as exc:
    print(f"Voice error: {exc}")

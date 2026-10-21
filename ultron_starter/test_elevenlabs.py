import os
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv(override=True)

api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
model_id = os.getenv(
    "ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"
).strip()

try:
    print("Connecting to ElevenLabs...")
    client = ElevenLabs(api_key=api_key)

    audio = client.text_to_speech.convert(
        text="All systems are operational. I am Ultron.",
        voice_id=voice_id,
        model_id=model_id,
        output_format="mp3_44100_128",
    )

    output = Path("elevenlabs_test.mp3")
    with output.open("wb") as file:
        for chunk in audio:
            if chunk:
                file.write(chunk)

    if output.stat().st_size == 0:
        raise RuntimeError("The generated audio file is empty.")

    print(f"SUCCESS: Audio saved to {output.resolve()}")

    import shutil
    import subprocess

    ffplay = shutil.which("ffplay")
    if ffplay:
        subprocess.run(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "error",
             str(output.resolve())],
            check=True,
        )
    else:
        print("ffplay isn't on PATH. Audio was generated successfully.")

except Exception as exc:
    print(f"ERROR: {type(exc).__name__}: {exc}")

# ULTRON — Personal AI Assistant (Starter)

A Windows desktop starter using Python + PySide6, local Ollama or an optional OpenAI-compatible cloud API, SQLite chat history, offline Vosk speech recognition, offline `pyttsx3` speech output, and a tiny C++17 native-library scaffold.

> This is a first milestone, not an autonomous agent. It does not execute shell commands, modify files, or control applications. Voice input is push-to-talk and recognized text is shown for review before sending.

## 1. Prerequisites (Windows 11)

- Python 3.11 (64-bit) recommended
- Git (optional but recommended)
- For local AI: install Ollama from https://ollama.com/download/windows
- For C++ scaffold: Visual Studio Build Tools with **Desktop development with C++**, and CMake

## 2. Setup

Open PowerShell in this folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, use this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Start local AI (free, runs on your PC)

Install Ollama, then in PowerShell:

```powershell
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
```

Leave Ollama running (the desktop app calls its local API at `http://localhost:11434`). In `.env`, keep:

```dotenv
ULTRON_PROVIDER=local
OLLAMA_MODEL=qwen2.5:3b
```

Then launch the UI from the project folder:

```powershell
python -m ultron.main
```

## 4. Enable optional cloud AI

The cloud option uses an OpenAI-compatible chat-completions endpoint. Create an API key with a provider you choose, then put the endpoint, model and key in `.env`, for example:

```dotenv
CLOUD_BASE_URL=https://api.groq.com/openai/v1/chat/completions
CLOUD_MODEL=llama-3.1-8b-instant
CLOUD_API_KEY=your_key_here
```

Choose **Cloud (API)** in the app. API availability, free tiers, model names and rate limits can change. Never commit `.env` or share your key. Local mode does not require a cloud key.

## 5. Enable offline voice input

Download a small English model from https://alphacephei.com/vosk/models (for example `vosk-model-small-en-us-0.15`), extract it so this path exists:

```text
models/vosk-model-small-en-us-0.15/
```

Or set `VOSK_MODEL_PATH` in `.env` to the extracted folder. Press **Listen**, speak in English, then review the recognized text and press **Send**. Speech recognition is local; the AI provider selected in the app receives the text only after you press Send. Text-to-speech uses Windows' installed voices via `pyttsx3`.

If Windows audio dependencies fail, check Windows Settings → Privacy & security → Microphone, and allow desktop apps to use the microphone. Confirm your Windows input/output device works in Sound settings.

## 6. Tests

```powershell
pytest -q
```

Tests cover SQLite chat history and the local AI response adapter without needing internet or a running model. GUI, microphone, TTS and live-model integration need manual testing.

## 7. Build the C++ scaffold (optional)

From a Developer PowerShell for Visual Studio, in the `native` folder:

```powershell
cmake -S . -B build
cmake --build build --config Release
```

This creates a small native library. Python does not call it yet; integrating it safely through `ctypes`/pybind11 is a later milestone.

## Project layout

```text
ultron-starter/
├── ultron/
│   ├── main.py       # app entry point
│   ├── ui.py         # PySide6 desktop UI and background workers
│   ├── brain.py      # local/cloud AI provider adapter
│   ├── voice.py      # offline speech input/output
│   ├── memory.py     # SQLite conversation history
│   └── config.py     # .env configuration
├── native/           # C++17 library scaffold and CMake
├── tests/            # pytest unit tests
├── .env.example
└── requirements.txt
```

## Known limitations / next milestone

- No wake word yet; voice is push-to-talk.
- The Vosk model must be downloaded separately.
- Chat history is stored locally in SQLite. Use **Clear chat** to delete it.
- Cloud mode sends the selected conversation context to the configured API provider.
- The C++ library is a scaffold and is not yet linked into Python.
- Next: run the app, verify model and audio behavior, then add settings, wake-word detection, and a tested C++/Python binding.

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("ULTRON_PROVIDER", "local").strip().lower()
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    cloud_base_url: str = os.getenv("CLOUD_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")
    cloud_model: str = os.getenv("CLOUD_MODEL", "llama-3.1-8b-instant")
    cloud_api_key: str = os.getenv("CLOUD_API_KEY", "")
    vosk_model_path: Path = PROJECT_ROOT / os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
    db_path: Path = PROJECT_ROOT / os.getenv("ULTRON_DB_PATH", "data/ultron.sqlite3")

settings = Settings()

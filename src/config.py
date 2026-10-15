import os
from pathlib import Path
from typing import Optional
from google import genai

def load_dotenv(env_path: Optional[str] = None) -> None:
    """Lightweight .env loader without requiring external third-party packages."""
    if env_path is None:
        candidates = [Path(".env"), Path("../.env"), Path(__file__).resolve().parent.parent / ".env"]
        for p in candidates:
            if p.exists():
                env_path = str(p)
                break
    if env_path and os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val

# Auto load on import
load_dotenv()

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def get_api_key() -> Optional[str]:
    """Retrieve Gemini API key from environment."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

def get_gemini_client(api_key: Optional[str] = None) -> Optional[genai.Client]:
    """Instantiate and return a google-genai Client if an API key is available."""
    key = api_key or get_api_key()
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as e:
        print(f"[Warning] Failed to initialize Google GenAI client: {e}")
        return None

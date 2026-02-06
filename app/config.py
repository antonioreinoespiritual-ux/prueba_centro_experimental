from __future__ import annotations

from pathlib import Path
import os


def load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def get_groq_api_url() -> str:
    return os.getenv(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1/chat/completions",
    ).strip()


def get_groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

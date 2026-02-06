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


def get_deepseek_api_key() -> str:
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


def get_deepseek_api_url() -> str:
    return os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions").strip()


def get_deepseek_model() -> str:
    return os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

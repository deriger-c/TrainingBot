from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    google_script_url: str
    google_script_secret: str
    admin_user_id: int | None
    default_timezone: str
    database_url: str
    worker_token: str
    public_base_url: str
    miniapp_url: str
    ollama_base_url: str
    ollama_model: str


def _optional_int(value: str | None) -> int | None:
    if not value or value == "your_telegram_user_id":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "your_telegram_bot_token":
        raise RuntimeError("Не задан BOT_TOKEN в .env")

    return Config(
        bot_token=token,
        google_script_url=os.getenv("GOOGLE_SCRIPT_URL", "").strip(),
        google_script_secret=os.getenv("GOOGLE_SCRIPT_SECRET", "").strip(),
        admin_user_id=_optional_int(os.getenv("ADMIN_USER_ID")),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "Asia/Jerusalem").strip(),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/training_bot.db").strip(),
        worker_token=os.getenv("WORKER_TOKEN", "").strip(),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/"),
        miniapp_url=os.getenv("MINIAPP_URL", "").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip(),
    )

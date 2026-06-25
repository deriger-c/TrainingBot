from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from config import Config


@dataclass(frozen=True)
class TelegramWebAppUser:
    telegram_id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""


def parse_and_validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> TelegramWebAppUser:
    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram initData")

    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", "")
    auth_date = int(values.get("auth_date") or 0)
    if not received_hash or not auth_date:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram initData")
    if time.time() - auth_date > max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired Telegram initData")

    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad Telegram initData signature")

    try:
        user = json.loads(values.get("user", "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram user") from exc
    if not user.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram user")
    return TelegramWebAppUser(
        telegram_id=int(user["id"]),
        username=str(user.get("username", "")),
        first_name=str(user.get("first_name", "")),
        last_name=str(user.get("last_name", "")),
    )


def validate_worker_token(config: Config, token: str | None = Header(default=None, alias="X-Worker-Token")) -> None:
    if not config.worker_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="WORKER_TOKEN is not configured")
    if not token or not hmac.compare_digest(token, config.worker_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad worker token")


def validate_telegram_webhook_secret(config: Config, token: str | None) -> None:
    if not config.telegram_webhook_secret:
        return
    if not token or not hmac.compare_digest(token, config.telegram_webhook_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad Telegram webhook secret")

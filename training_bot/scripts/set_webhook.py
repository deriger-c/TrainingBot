from __future__ import annotations

import asyncio
import re

from aiogram import Bot

from config import load_config

WEBHOOK_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


async def main() -> None:
    config = load_config()
    if not config.public_base_url:
        print("PUBLIC_BASE_URL is not set.")
        print("Set it only after Render gives you the public backend URL.")
        print("")
        print("Example .env value:")
        print("PUBLIC_BASE_URL=https://your-training-bot-api.onrender.com")
        print("")
        print("Then run again:")
        print("python -m scripts.set_webhook")
        raise SystemExit(2)
    if not config.public_base_url.startswith("https://"):
        print("PUBLIC_BASE_URL must be a public HTTPS URL for Telegram webhooks.")
        print(f"Current value: {config.public_base_url}")
        print("Example: https://your-training-bot-api.onrender.com")
        raise SystemExit(2)
    if config.telegram_webhook_secret and not WEBHOOK_SECRET_RE.fullmatch(config.telegram_webhook_secret):
        print("TELEGRAM_WEBHOOK_SECRET contains characters Telegram does not allow.")
        print("Use only latin letters, digits, underscore and hyphen: A-Z a-z 0-9 _ -")
        print("")
        print("Good example:")
        print("TELEGRAM_WEBHOOK_SECRET=training_bot_webhook_2026_safe_token")
        print("")
        print("Set the exact same value in Render and in your local .env, then run this script again.")
        raise SystemExit(2)

    webhook_url = f"{config.public_base_url}/telegram/webhook"
    bot = Bot(token=config.bot_token)
    try:
        await bot.set_webhook(
            webhook_url,
            secret_token=config.telegram_webhook_secret or None,
            drop_pending_updates=True,
        )
        info = await bot.get_webhook_info()
    finally:
        await bot.session.close()

    print(f"Webhook set to: {webhook_url}")
    print(f"Telegram reports: {info.url}")
    if info.last_error_message:
        print(f"Last error: {info.last_error_message}")


if __name__ == "__main__":
    asyncio.run(main())

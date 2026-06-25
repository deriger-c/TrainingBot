from __future__ import annotations

import asyncio

from aiogram import Bot

from config import load_config


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

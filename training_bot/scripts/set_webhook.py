from __future__ import annotations

import asyncio

from aiogram import Bot

from config import load_config


async def main() -> None:
    config = load_config()
    if not config.public_base_url:
        raise RuntimeError("PUBLIC_BASE_URL is required to set Telegram webhook")

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

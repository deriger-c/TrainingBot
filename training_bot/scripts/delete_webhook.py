from __future__ import annotations

import asyncio

from aiogram import Bot

from config import load_config


async def main() -> None:
    config = load_config()
    bot = Bot(token=config.bot_token)
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        info = await bot.get_webhook_info()
    finally:
        await bot.session.close()

    print("Webhook deleted.")
    print(f"Telegram reports: {info.url or 'no webhook'}")


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot_factory import build_dispatcher
from config import load_config
from utils.logger import setup_logging


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="workout_a", description="Начать Workout A"),
            BotCommand(command="workout_b", description="Начать Workout B"),
            BotCommand(command="history", description="История тренировок"),
            BotCommand(command="progress", description="Мой прогресс"),
            BotCommand(command="goals", description="Цели"),
            BotCommand(command="settings", description="Настройки"),
            BotCommand(command="import_first_workout", description="Импортировать первую тренировку"),
            BotCommand(command="sync", description="Синхронизировать pending-данные"),
            BotCommand(command="cancel", description="Отменить текущий сценарий"),
        ]
    )


async def main() -> None:
    setup_logging()
    config = load_config()
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp: Dispatcher = build_dispatcher(config)

    await set_commands(bot)
    logging.getLogger(__name__).info("Training bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

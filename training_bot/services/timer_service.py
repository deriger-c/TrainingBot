from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


class TimerService:
    def __init__(self) -> None:
        self._tasks: dict[tuple[int, int], asyncio.Task] = {}

    async def start_rest_timer(self, bot: Bot, chat_id: int, user_id: int, seconds: int) -> None:
        self.cancel(chat_id, user_id)
        await bot.send_message(chat_id, f"Отдых начался: {seconds} секунд")
        task = asyncio.create_task(self._finish_after(bot, chat_id, user_id, seconds))
        self._tasks[(chat_id, user_id)] = task

    def cancel(self, chat_id: int, user_id: int) -> None:
        task = self._tasks.pop((chat_id, user_id), None)
        if task and not task.done():
            task.cancel()

    async def _finish_after(self, bot: Bot, chat_id: int, user_id: int, seconds: int) -> None:
        try:
            await asyncio.sleep(seconds)
            await bot.send_message(chat_id, "Отдых закончен. Переходим дальше, когда будешь готов.")
        except asyncio.CancelledError:
            logger.info("Rest timer cancelled for chat=%s user=%s", chat_id, user_id)
        finally:
            self._tasks.pop((chat_id, user_id), None)

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, admin_user_id: int) -> None:
        self.admin_user_id = admin_user_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user and user.id == self.admin_user_id:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Нет доступа к этому боту.", show_alert=True)
            return None
        if isinstance(event, Message):
            await event.answer("Нет доступа к этому боту.")
            return None
        return None

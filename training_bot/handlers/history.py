from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main_menu import BTN_HISTORY
from services.google_sheets_api import GoogleSheetsAPI
from utils.formatters import format_history

router = Router()


@router.message(Command("history"))
@router.message(F.text == BTN_HISTORY)
async def history(message: Message, google_api: GoogleSheetsAPI) -> None:
    try:
        items = await google_api.get_history()
    except Exception:
        await message.answer("Не удалось получить историю из Google Sheets. Проверь WEB_APP_URL и деплой Apps Script.")
        return
    await message.answer(format_history(items))

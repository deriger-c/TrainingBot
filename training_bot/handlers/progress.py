from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main_menu import BTN_PROGRESS
from services.google_sheets_api import GoogleSheetsAPI
from services.progress_service import filter_key_progress
from utils.formatters import format_progress

router = Router()


@router.message(Command("progress"))
@router.message(F.text == BTN_PROGRESS)
async def progress(message: Message, google_api: GoogleSheetsAPI) -> None:
    try:
        items = filter_key_progress(await google_api.get_progress())
    except Exception:
        await message.answer("Не удалось получить прогресс из Google Sheets. Сохранение локально не потеряно.")
        return
    await message.answer(format_progress(items))

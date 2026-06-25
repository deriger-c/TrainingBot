from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from data.first_workout_import import (
    FIRST_WORKOUT_PROGRESS_ROWS,
    FIRST_WORKOUT_RESULTS,
    FIRST_WORKOUT_SESSION,
)
from keyboards.main_menu import main_menu_keyboard
from services.google_sheets_api import GoogleSheetsAPI

router = Router()


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, текущий сценарий отменён.", reply_markup=main_menu_keyboard())


@router.message(Command("sync"))
async def sync_pending(message: Message, google_api: GoogleSheetsAPI) -> None:
    await message.answer("Пробую отправить pending-данные в Google Sheets...")
    sent, failed = await google_api.sync_pending()
    if failed:
        await message.answer(f"Синхронизировано: {sent}. Осталось с ошибкой: {failed}.")
    else:
        await message.answer(f"Готово. Синхронизировано записей: {sent}.")


@router.message(Command("import_first_workout"))
async def import_first_workout(message: Message, google_api: GoogleSheetsAPI) -> None:
    await message.answer("Импортирую первую тренировку 16.06.2026 и базовый прогресс...")
    workout_saved = await google_api.save_workout_bundle(FIRST_WORKOUT_SESSION, FIRST_WORKOUT_RESULTS)
    progress_saved, progress_failed = await google_api.save_progress_rows(FIRST_WORKOUT_PROGRESS_ROWS)
    if workout_saved and progress_failed == 0:
        await message.answer(
            f"Готово. Первая тренировка и {progress_saved} строк прогресса сохранены в Google Sheets.",
            reply_markup=main_menu_keyboard(),
        )
        return
    await message.answer(
        "Google Sheets сейчас недоступен или не настроен. Я сохранил импорт локально в pending. "
        "После настройки GOOGLE_SCRIPT_URL запусти /sync.",
        reply_markup=main_menu_keyboard(),
    )

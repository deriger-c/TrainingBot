from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from keyboards.main_menu import BTN_QUICK_ADD, main_menu_keyboard
from keyboards.settings_keyboards import quick_workout_keyboard
from services.google_sheets_api import GoogleSheetsAPI
from services.workout_service import make_quick_result
from states.quick_add_states import QuickAddStates
from utils.validators import validate_result_input

router = Router()


@router.message(Command("quick_add"))
@router.message(F.text == BTN_QUICK_ADD)
async def quick_add_start(message: Message, state: FSMContext) -> None:
    await state.set_state(QuickAddStates.waiting_text)
    await message.answer(
        "Напиши результат одной строкой.\nПример: <code>Подтягивания +5kg 6/5/5/4</code>"
    )


@router.message(QuickAddStates.waiting_text)
async def quick_add_text(message: Message, state: FSMContext) -> None:
    ok, text, error = validate_result_input(message.text)
    if not ok:
        await message.answer(error)
        return
    await state.update_data(quick_text=text)
    await state.set_state(QuickAddStates.choosing_workout)
    await message.answer("К какой тренировке добавить результат?", reply_markup=quick_workout_keyboard())


@router.callback_query(QuickAddStates.choosing_workout, F.data.startswith("quick:"))
async def quick_add_save(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
    google_api: GoogleSheetsAPI,
) -> None:
    data = await state.get_data()
    workout_type = callback.data.split(":", 1)[1]
    workout_type = "" if workout_type == "none" else workout_type
    result = make_quick_result(data["quick_text"], workout_type, config.default_timezone)
    saved = await google_api.save_exercise_result(result)
    await state.clear()
    if saved:
        await callback.message.answer("Результат сохранён в Google Sheets.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.answer(
            "Не удалось сохранить в Google Sheets. Я временно сохранил тренировку локально.",
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()

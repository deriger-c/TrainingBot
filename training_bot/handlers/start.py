from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from keyboards.main_menu import BTN_HELP, main_menu_keyboard

router = Router()


HELP_TEXT = """
Я буду вести тебя по тренировке как тренер:

• сначала вес, сон и энергия;
• потом разминка;
• затем упражнения по одному;
• после результата предложу отдых;
• в конце покажу итог и сохраню всё в Google Sheets.

Команды:
/workout_a — начать Workout A
/workout_b — начать Workout B
/history — последние тренировки
/progress — прогресс
/goals — цели
/settings — настройки
/sync — отправить pending-данные в Google Sheets
/cancel — отменить текущий сценарий
""".strip()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет. Я твой тренировочный бот: веду по разминке, упражнениям, отдыху и сохраняю результат.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def help_message(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())

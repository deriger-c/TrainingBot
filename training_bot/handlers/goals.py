from __future__ import annotations

from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.exercise_program import DEFAULT_GOALS
from keyboards.goals_keyboards import goals_back_keyboard, goals_menu_keyboard
from keyboards.main_menu import BTN_GOALS
from services.google_sheets_api import GoogleSheetsAPI
from states.goal_states import GoalStates
from utils.formatters import format_goals
from utils.time_utils import current_timestamp

router = Router()


@router.message(Command("goals"))
@router.message(F.text == BTN_GOALS)
async def goals_menu(message: Message) -> None:
    await message.answer("🎯 Меню целей", reply_markup=goals_menu_keyboard())


@router.callback_query(F.data == "goals:menu")
async def goals_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("🎯 Меню целей", reply_markup=goals_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "goals:list")
async def goals_list(callback: CallbackQuery, google_api: GoogleSheetsAPI) -> None:
    items = await _get_or_seed_goals(google_api)
    await callback.message.answer(format_goals(items), reply_markup=goals_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "goals:add")
async def goal_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_name)
    await callback.message.answer("Название цели? Например: <code>Стойка лицом к стене</code>")
    await callback.answer()


@router.message(GoalStates.waiting_name)
async def goal_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не должно быть пустым.")
        return
    await state.update_data(goal_name=name)
    await state.set_state(GoalStates.waiting_category)
    await message.answer("Категория? Например: Skill, Strength, Core.")


@router.message(GoalStates.waiting_category)
async def goal_category(message: Message, state: FSMContext) -> None:
    category = (message.text or "").strip()
    if not category:
        await message.answer("Категория не должна быть пустой.")
        return
    await state.update_data(category=category)
    await state.set_state(GoalStates.waiting_target)
    await message.answer("Целевой результат? Например: <code>60 секунд</code> или <code>+10kg 6 reps</code>.")


@router.message(GoalStates.waiting_target)
async def goal_target(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    target = (message.text or "").strip()
    if not target:
        await message.answer("Цель не должна быть пустой.")
        return
    data = await state.get_data()
    now = current_timestamp("Asia/Jerusalem")
    goal = {
        "Goal ID": f"goal-{uuid4().hex[:8]}",
        "Goal Name": data["goal_name"],
        "Category": data["category"],
        "Target": target,
        "Current Result": "",
        "Status": "active",
        "Created At": now,
        "Updated At": now,
        "Notes": "",
    }
    saved = await google_api.save_goal(goal)
    await state.clear()
    await message.answer("Цель сохранена." if saved else "Не удалось сохранить цель. Проверь Google Sheets.")


@router.callback_query(F.data == "goals:edit")
async def goal_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_edit_id)
    await callback.message.answer("Пришли Goal ID цели, а затем я попрошу новый текущий результат.")
    await callback.answer()


@router.message(GoalStates.waiting_edit_id)
async def goal_edit_id(message: Message, state: FSMContext) -> None:
    goal_id = (message.text or "").strip()
    await state.update_data(goal_id=goal_id)
    await state.set_state(GoalStates.waiting_edit_value)
    await message.answer("Новый текущий результат или заметка по цели?")


@router.message(GoalStates.waiting_edit_value)
async def goal_edit_value(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    data = await state.get_data()
    value = (message.text or "").strip()
    ok = await google_api.update_goal(
        data["goal_id"],
        {"Current Result": value, "Updated At": current_timestamp("Asia/Jerusalem")},
    )
    await state.clear()
    await message.answer("Цель обновлена." if ok else "Не удалось обновить цель.")


@router.callback_query(F.data == "goals:complete")
async def goal_complete(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_complete_id)
    await callback.message.answer("Пришли Goal ID цели, которую отметить выполненной.")
    await callback.answer()


@router.message(GoalStates.waiting_complete_id)
async def goal_complete_id(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    goal_id = (message.text or "").strip()
    ok = await google_api.update_goal(goal_id, {"Status": "completed", "Updated At": current_timestamp("Asia/Jerusalem")})
    await state.clear()
    await message.answer("Готово, цель отмечена выполненной." if ok else "Не удалось обновить цель.")


@router.callback_query(F.data == "goals:delete")
async def goal_delete(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_delete_id)
    await callback.message.answer("Пришли Goal ID цели, которую удалить.")
    await callback.answer()


@router.message(GoalStates.waiting_delete_id)
async def goal_delete_id(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    goal_id = (message.text or "").strip()
    ok = await google_api.delete_goal(goal_id)
    await state.clear()
    await message.answer("Цель удалена." if ok else "Не удалось удалить цель.")


async def _get_or_seed_goals(google_api: GoogleSheetsAPI) -> list[dict]:
    try:
        items = await google_api.get_goals()
    except Exception:
        return []
    if items:
        return items
    now = current_timestamp("Asia/Jerusalem")
    seeded = []
    for item in DEFAULT_GOALS:
        goal = {
            "Goal ID": f"goal-{uuid4().hex[:8]}",
            "Goal Name": item["goal_name"],
            "Category": item["category"],
            "Target": item["target"],
            "Current Result": "",
            "Status": "active",
            "Created At": now,
            "Updated At": now,
            "Notes": "Стандартная цель",
        }
        if await google_api.save_goal(goal):
            seeded.append(goal)
    return seeded

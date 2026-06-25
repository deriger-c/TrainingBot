from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.main_menu import BTN_SETTINGS
from keyboards.settings_keyboards import settings_keyboard
from services.google_sheets_api import GoogleSheetsAPI
from states.settings_states import SettingsStates
from utils.validators import parse_float

router = Router()


DEFAULT_SETTINGS = {
    "Default Body Weight": 58.0,
    "Show Timers": True,
    "Show Technique Tips": True,
    "Default Rest Seconds": 90,
    "Language": "ru",
    "Show Estimated Timing": True,
}


@router.message(Command("settings"))
@router.message(F.text == BTN_SETTINGS)
async def settings(message: Message, google_api: GoogleSheetsAPI) -> None:
    current = await _settings_for_user(message.from_user.id, google_api)
    await message.answer(_format_settings(current), reply_markup=_settings_markup(current))


@router.callback_query(F.data == "settings:weight")
async def settings_weight(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_body_weight)
    await callback.message.answer("Новый вес тела по умолчанию в кг?")
    await callback.answer()


@router.message(SettingsStates.waiting_body_weight)
async def settings_weight_save(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    ok, value, error = parse_float(message.text, min_value=30, max_value=200, field_name="Вес")
    if not ok:
        await message.answer(error)
        return
    current = await _settings_for_user(message.from_user.id, google_api)
    current["Default Body Weight"] = value
    saved = await google_api.save_settings({"User ID": message.from_user.id, **current})
    await state.clear()
    await message.answer("Вес обновлён." if saved else "Не удалось сохранить настройки.")


@router.callback_query(F.data == "settings:rest")
async def settings_rest(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsStates.waiting_rest_seconds)
    await callback.message.answer("Время отдыха по умолчанию в секундах?")
    await callback.answer()


@router.message(SettingsStates.waiting_rest_seconds)
async def settings_rest_save(message: Message, state: FSMContext, google_api: GoogleSheetsAPI) -> None:
    ok, value, error = parse_float(message.text, min_value=10, max_value=600, field_name="Отдых")
    if not ok:
        await message.answer(error)
        return
    current = await _settings_for_user(message.from_user.id, google_api)
    current["Default Rest Seconds"] = int(value)
    saved = await google_api.save_settings({"User ID": message.from_user.id, **current})
    await state.clear()
    await message.answer("Время отдыха обновлено." if saved else "Не удалось сохранить настройки.")


@router.callback_query(F.data.in_({"settings:toggle_timers", "settings:toggle_tips", "settings:toggle_timing"}))
async def settings_toggle(callback: CallbackQuery, google_api: GoogleSheetsAPI) -> None:
    current = await _settings_for_user(callback.from_user.id, google_api)
    field_by_action = {
        "settings:toggle_timers": "Show Timers",
        "settings:toggle_tips": "Show Technique Tips",
        "settings:toggle_timing": "Show Estimated Timing",
    }
    field = field_by_action[callback.data]
    current[field] = not _as_bool(current.get(field, True))
    await google_api.save_settings({"User ID": callback.from_user.id, **current})
    await callback.message.answer(_format_settings(current), reply_markup=_settings_markup(current))
    await callback.answer("Настройка обновлена")


async def _settings_for_user(user_id: int, google_api: GoogleSheetsAPI) -> dict:
    try:
        row = await google_api.get_settings(user_id)
    except Exception:
        row = None
    if not row:
        return dict(DEFAULT_SETTINGS)
    return {
        "Default Body Weight": float(row.get("Default Body Weight", DEFAULT_SETTINGS["Default Body Weight"])),
        "Show Timers": _as_bool(row.get("Show Timers", DEFAULT_SETTINGS["Show Timers"])),
        "Show Technique Tips": _as_bool(row.get("Show Technique Tips", DEFAULT_SETTINGS["Show Technique Tips"])),
        "Default Rest Seconds": int(row.get("Default Rest Seconds", DEFAULT_SETTINGS["Default Rest Seconds"])),
        "Language": row.get("Language", "ru"),
        "Show Estimated Timing": _as_bool(row.get("Show Estimated Timing", DEFAULT_SETTINGS["Show Estimated Timing"])),
    }


def _settings_markup(current: dict):
    return settings_keyboard(
        show_timers=_as_bool(current.get("Show Timers", True)),
        show_tips=_as_bool(current.get("Show Technique Tips", True)),
        show_timing=_as_bool(current.get("Show Estimated Timing", True)),
    )


def _format_settings(current: dict) -> str:
    return "\n".join(
        [
            "⚙️ <b>Настройки</b>",
            f"Вес тела: {current.get('Default Body Weight')} кг",
            f"Таймер отдыха: {'включён' if _as_bool(current.get('Show Timers')) else 'выключен'}",
            f"Отдых по умолчанию: {current.get('Default Rest Seconds')} сек",
            f"Подсказки по технике: {'показывать' if _as_bool(current.get('Show Technique Tips')) else 'скрывать'}",
            f"Примерный тайминг: {'показывать' if _as_bool(current.get('Show Estimated Timing')) else 'скрывать'}",
            "Язык: русский",
        ]
    )


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes", "да", "вкл", "on"}

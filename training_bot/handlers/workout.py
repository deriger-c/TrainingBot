from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from data.exercise_program import get_warmup, get_workout
from keyboards.main_menu import BTN_WORKOUT_A, BTN_WORKOUT_B, main_menu_keyboard
from keyboards.workout_keyboards import (
    after_result_keyboard,
    energy_keyboard,
    exercise_input_keyboard,
    falls_keyboard,
    pain_keyboard,
    reserve_seconds_keyboard,
    rest_keyboard,
    rir_keyboard,
    summary_keyboard,
    technique_keyboard,
    warmup_confirm_keyboard,
)
from services.google_sheets_api import GoogleSheetsAPI
from services.progression_rules_service import (
    enrich_result_with_decision,
    format_decision_message,
    is_hold_exercise,
)
from services.timer_service import TimerService
from services.workout_service import (
    create_session,
    exercise_from_state,
    finalize_session,
    make_exercise_result,
)
from states.workout_states import WorkoutStates
from utils.formatters import format_exercise, format_workout_summary
from utils.time_utils import current_time_hhmm
from utils.validators import extract_weight_used, is_skip_result, parse_float, validate_result_input

router = Router()


@router.message(Command("workout_a"))
@router.message(F.text == BTN_WORKOUT_A)
async def workout_a(message: Message, state: FSMContext) -> None:
    await _start_workout(message, state, "A")


@router.message(Command("workout_b"))
@router.message(F.text == BTN_WORKOUT_B)
async def workout_b(message: Message, state: FSMContext) -> None:
    await _start_workout(message, state, "B")


async def _start_workout(message: Message, state: FSMContext, workout_type: str) -> None:
    await state.clear()
    await state.update_data(workout_type=workout_type, results=[], phase="setup")
    await state.set_state(WorkoutStates.waiting_body_weight)
    await message.answer(
        f"Начинаем Workout {workout_type}. Сначала короткая настройка.\n\n"
        "Твой вес тела сегодня? Например: <code>58</code>"
    )


@router.message(WorkoutStates.waiting_body_weight)
async def body_weight(message: Message, state: FSMContext) -> None:
    ok, value, error = parse_float(message.text, min_value=30, max_value=200, field_name="Вес тела")
    if not ok:
        await message.answer(error)
        return
    await state.update_data(body_weight=value)
    await state.set_state(WorkoutStates.waiting_sleep_hours)
    await message.answer("Сколько часов сна было? Например: <code>8</code>")


@router.message(WorkoutStates.waiting_sleep_hours)
async def sleep_hours(message: Message, state: FSMContext) -> None:
    ok, value, error = parse_float(message.text, min_value=0, max_value=16, field_name="Сон")
    if not ok:
        await message.answer(error)
        return
    await state.update_data(sleep_hours=value)
    await state.set_state(WorkoutStates.waiting_energy_level)
    await message.answer("Уровень энергии сегодня?", reply_markup=energy_keyboard())


@router.callback_query(WorkoutStates.waiting_energy_level, F.data.startswith("energy:"))
async def energy_level(callback: CallbackQuery, state: FSMContext, config: Config, google_api: GoogleSheetsAPI) -> None:
    energy = callback.data.split(":", 1)[1]
    data = await state.get_data()
    workout_type = data["workout_type"]
    session = create_session(
        workout_type=workout_type,
        body_weight=float(data["body_weight"]),
        sleep_hours=float(data["sleep_hours"]),
        energy_level=energy,
        timezone_name=config.default_timezone,
    )
    settings = await _load_settings(callback.from_user.id, google_api)
    await state.update_data(
        energy_level=energy,
        session=session,
        phase="warmup",
        index=0,
        settings=settings,
        current_rest_seconds=0,
        timezone_name=config.default_timezone,
    )
    await callback.message.answer(
        "Начинаем разминку. Я проведу тебя по каждому пункту, как по обычным упражнениям."
    )
    await _show_current_exercise(callback.message, state)
    await callback.answer()


@router.message(WorkoutStates.waiting_result)
async def exercise_result(message: Message, state: FSMContext) -> None:
    ok, result_text, error = validate_result_input(message.text)
    if not ok:
        await message.answer(error)
        return
    if is_skip_result(result_text):
        await _store_current_result(state, result_text, {})
        await state.set_state(WorkoutStates.after_result)
        await message.answer("Упражнение помечено как пропущенное.", reply_markup=after_result_keyboard())
        return

    await state.update_data(pending_result_text=result_text, pending_meta={})
    exercise = exercise_from_state(await state.get_data())
    await state.set_state(WorkoutStates.waiting_rir)
    if is_hold_exercise(exercise.name, exercise.planned_reps):
        await message.answer(
            "Сколько секунд ты мог бы продержаться ещё с чистой техникой?",
            reply_markup=reserve_seconds_keyboard(),
        )
    else:
        await message.answer(
            "Сколько чистых повторений оставалось в запасе?\n"
            "Это RIR. Например: сделал 10, мог бы ещё 2 — нажми 2.",
            reply_markup=rir_keyboard(),
        )


@router.callback_query(WorkoutStates.waiting_rir, F.data.startswith("rir:"))
async def save_rir(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    await _update_pending_meta(state, {"rir": value})
    await _ask_pain(callback, state)


@router.callback_query(WorkoutStates.waiting_rir, F.data.startswith("reserve:"))
async def save_reserve(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.split(":", 1)[1]
    await _update_pending_meta(state, {"reserve_seconds": value})
    await _ask_pain(callback, state)


@router.callback_query(WorkoutStates.waiting_pain, F.data.startswith("pain:"))
async def save_pain(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":", 1)[1])
    await _update_pending_meta(state, {"pain_level": value})
    await state.set_state(WorkoutStates.waiting_technique)
    await callback.message.answer(
        "Техника была чистой и подконтрольной?",
        reply_markup=technique_keyboard(),
    )
    await callback.answer()


@router.callback_query(WorkoutStates.waiting_technique, F.data.startswith("technique:"))
async def save_technique(callback: CallbackQuery, state: FSMContext) -> None:
    technique_ok = callback.data.endswith(":ok")
    await _update_pending_meta(state, {"technique_ok": technique_ok})
    data = await state.get_data()
    exercise = exercise_from_state(data)
    if _needs_falls_question(exercise.name):
        await state.set_state(WorkoutStates.waiting_falls)
        await callback.message.answer("Были падения или потеря контроля в стойке?", reply_markup=falls_keyboard())
        await callback.answer()
        return
    await _finalize_pending_result(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.waiting_falls, F.data.startswith("falls:"))
async def save_falls(callback: CallbackQuery, state: FSMContext) -> None:
    value = int(callback.data.split(":", 1)[1])
    await _update_pending_meta(state, {"fall_count": value})
    await _finalize_pending_result(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.waiting_result, F.data == "workout:skip_waiting")
async def skip_waiting(callback: CallbackQuery, state: FSMContext) -> None:
    await _store_current_result(state, "skip", {})
    await state.set_state(WorkoutStates.after_result)
    await callback.message.answer("Упражнение помечено как пропущенное.", reply_markup=after_result_keyboard())
    await callback.answer()


@router.callback_query(F.data == "workout:cancel")
async def workout_cancel(callback: CallbackQuery, state: FSMContext, timer_service: TimerService) -> None:
    timer_service.cancel(callback.message.chat.id, callback.from_user.id)
    await state.clear()
    await callback.message.answer("Тренировка отменена.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "workout:note")
async def add_result_note(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.waiting_result_note)
    await callback.message.answer("Напиши заметку к последнему упражнению.")
    await callback.answer()


@router.message(WorkoutStates.waiting_result_note)
async def save_result_note(message: Message, state: FSMContext) -> None:
    note = (message.text or "").strip()
    data = await state.get_data()
    results = list(data.get("results", []))
    if results:
        results[-1]["notes"] = note
    await state.update_data(results=results)
    await state.set_state(WorkoutStates.after_result)
    await message.answer("Заметку добавил.", reply_markup=after_result_keyboard())


@router.callback_query(WorkoutStates.after_result, F.data == "workout:retry")
async def retry_result(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    results = list(data.get("results", []))
    current = data.get("current_exercise", {})
    if results and results[-1].get("exercise_name") == current.get("name"):
        results.pop()
        await state.update_data(results=results)
    await _show_current_exercise(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "workout:skip_last")
async def skip_last(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    results = list(data.get("results", []))
    if results:
        results[-1]["actual_result"] = "skipped"
        results[-1]["status"] = "skipped"
        results[-1]["progression_eligible"] = False
        results[-1]["progression_status"] = "skipped"
    await state.update_data(results=results)
    await callback.message.answer("Последнее упражнение помечено как пропущенное.", reply_markup=after_result_keyboard())
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "rest:start")
async def rest_start(callback: CallbackQuery, state: FSMContext, timer_service: TimerService, bot: Bot) -> None:
    data = await state.get_data()
    exercise = exercise_from_state(data)
    seconds = int(data.get("current_rest_seconds") or exercise.rest_seconds)
    await state.update_data(current_rest_seconds=seconds)
    await timer_service.start_rest_timer(bot, callback.message.chat.id, callback.from_user.id, seconds)
    await callback.message.answer(f"Отдых: {seconds} секунд", reply_markup=rest_keyboard())
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "rest:add30")
async def rest_add(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    exercise = exercise_from_state(data)
    seconds = int(data.get("current_rest_seconds") or exercise.rest_seconds) + 30
    await state.update_data(current_rest_seconds=seconds)
    await callback.message.answer(f"Отдых увеличен: {seconds} секунд", reply_markup=rest_keyboard())
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "rest:skip")
async def rest_skip(callback: CallbackQuery, timer_service: TimerService) -> None:
    timer_service.cancel(callback.message.chat.id, callback.from_user.id)
    await callback.message.answer("Отдых пропущен. Когда готов — переходи дальше.", reply_markup=after_result_keyboard())
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "workout:next")
async def next_exercise(callback: CallbackQuery, state: FSMContext, timer_service: TimerService, config: Config) -> None:
    timer_service.cancel(callback.message.chat.id, callback.from_user.id)
    data = await state.get_data()
    phase = data.get("phase")
    next_index = int(data.get("index", 0)) + 1
    await state.update_data(index=next_index, current_rest_seconds=0)
    if phase == "warmup" and next_index >= len(get_warmup()):
        await state.set_state(WorkoutStates.warmup_confirm)
        await callback.message.answer(
            "Разминка завершена? Готов перейти к основной части?",
            reply_markup=warmup_confirm_keyboard(),
        )
    elif phase == "main" and next_index >= len(get_workout(data["workout_type"])):
        await _finish_workout(callback.message, state, config)
    else:
        await _show_current_exercise(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.after_result, F.data == "workout:finish")
@router.callback_query(WorkoutStates.waiting_result, F.data == "workout:finish")
async def finish_early(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    await _finish_workout(callback.message, state, config)
    await callback.answer()


@router.callback_query(WorkoutStates.warmup_confirm, F.data == "warmup:repeat")
async def warmup_repeat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(phase="warmup", index=0)
    await callback.message.answer("Повторяем разминку спокойно и без спешки.")
    await _show_current_exercise(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.warmup_confirm, F.data.in_({"warmup:done", "warmup:skip"}))
async def warmup_done(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(phase="main", index=0, current_rest_seconds=0)
    await callback.message.answer("Переходим к основной части. Работаем чисто, без гонки за весом.")
    await _show_current_exercise(callback.message, state)
    await callback.answer()


@router.callback_query(WorkoutStates.summary, F.data == "summary:save")
async def save_summary(
    callback: CallbackQuery,
    state: FSMContext,
    google_api: GoogleSheetsAPI,
    timer_service: TimerService,
) -> None:
    timer_service.cancel(callback.message.chat.id, callback.from_user.id)
    data = await state.get_data()
    saved = await google_api.save_workout_bundle(data["session"], data.get("results", []))
    await state.clear()
    if saved:
        await callback.message.answer("Тренировка сохранена в Google Sheets. Отличная работа.", reply_markup=main_menu_keyboard())
    else:
        await callback.message.answer(
            "Не удалось сохранить в Google Sheets. Я временно сохранил тренировку локально.",
            reply_markup=main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(WorkoutStates.summary, F.data == "summary:note")
async def summary_note(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.waiting_general_note)
    await callback.message.answer("Напиши общую заметку к тренировке.")
    await callback.answer()


@router.message(WorkoutStates.waiting_general_note)
async def save_general_note(message: Message, state: FSMContext) -> None:
    note = (message.text or "").strip()
    data = await state.get_data()
    session = dict(data["session"])
    session["general_notes"] = note
    await state.update_data(session=session)
    await state.set_state(WorkoutStates.summary)
    await message.answer(format_workout_summary(session, data.get("results", [])), reply_markup=summary_keyboard())


@router.callback_query(WorkoutStates.summary, F.data == "summary:edit")
async def summary_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.waiting_edit_number)
    await callback.message.answer("Номер упражнения в списке, которое нужно изменить?")
    await callback.answer()


@router.message(WorkoutStates.waiting_edit_number)
async def edit_number(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    results = data.get("results", [])
    try:
        number = int((message.text or "").strip())
    except ValueError:
        await message.answer("Нужен номер из списка.")
        return
    if number < 1 or number > len(results):
        await message.answer(f"Номер должен быть от 1 до {len(results)}.")
        return
    await state.update_data(edit_index=number - 1)
    await state.set_state(WorkoutStates.waiting_edit_result)
    await message.answer("Новый результат для этого упражнения?")


@router.message(WorkoutStates.waiting_edit_result)
async def edit_result(message: Message, state: FSMContext, config: Config) -> None:
    ok, text, error = validate_result_input(message.text)
    if not ok:
        await message.answer(error)
        return
    data = await state.get_data()
    results = list(data.get("results", []))
    idx = int(data["edit_index"])
    results[idx]["actual_result"] = "skipped" if is_skip_result(text) else text
    results[idx]["status"] = "skipped" if is_skip_result(text) else "completed"
    results[idx]["weight_used"] = extract_weight_used(text)
    results[idx]["completed_at"] = current_time_hhmm(config.default_timezone)
    results[idx] = enrich_result_with_decision(results[idx])
    await state.update_data(results=results)
    await state.set_state(WorkoutStates.summary)
    await message.answer(format_workout_summary(data["session"], results), reply_markup=summary_keyboard())


@router.callback_query(WorkoutStates.summary, F.data == "summary:cancel")
async def summary_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Тренировка отменена и не сохранена.", reply_markup=main_menu_keyboard())
    await callback.answer()


async def _show_current_exercise(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    phase = data.get("phase")
    exercises = get_warmup() if phase == "warmup" else get_workout(data["workout_type"])
    index = int(data.get("index", 0))
    exercise = exercises[index]
    settings = data.get("settings", {})
    await state.update_data(current_exercise=exercise.as_dict(), pending_meta={}, pending_result_text="")
    await state.set_state(WorkoutStates.waiting_result)
    prefix = "Разминка" if phase == "warmup" else f"Workout {data['workout_type']}"
    text = f"<b>{prefix}</b>\n\n" + format_exercise(
        exercise,
        index + 1,
        len(exercises),
        show_tips=_as_bool(settings.get("Show Technique Tips", True)),
        show_timing=_as_bool(settings.get("Show Estimated Timing", True)),
    )
    await message.answer(text, reply_markup=exercise_input_keyboard())


async def _ask_pain(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WorkoutStates.waiting_pain)
    await callback.message.answer(
        "Была боль или неприятный дискомфорт?\n0 — нет, 1 — лёгкий, 2 — заметный, 3 — сильный.",
        reply_markup=pain_keyboard(),
    )
    await callback.answer()


async def _update_pending_meta(state: FSMContext, updates: dict) -> None:
    data = await state.get_data()
    meta = dict(data.get("pending_meta", {}))
    meta.update(updates)
    await state.update_data(pending_meta=meta)


async def _finalize_pending_result(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    result_text = data["pending_result_text"]
    meta = dict(data.get("pending_meta", {}))
    await _store_current_result(state, result_text, meta)
    data = await state.get_data()
    latest = data["results"][-1]
    await state.set_state(WorkoutStates.after_result)
    await message.answer(format_decision_message(latest), reply_markup=after_result_keyboard())


async def _store_current_result(state: FSMContext, result_text: str, meta: dict) -> None:
    data = await state.get_data()
    exercise = exercise_from_state(data)
    result = make_exercise_result(data["session"], exercise, result_text, data.get("timezone_name", "Asia/Jerusalem"))
    result.update(meta)
    result["planned_sets"] = exercise.planned_sets
    result["planned_reps"] = exercise.planned_reps
    if result.get("pain_level", 0):
        result["pain_or_discomfort"] = f"pain_level={result['pain_level']}"
    if "shaking" in result_text.lower() or "дрож" in result_text.lower():
        result["stop_reason"] = "shaking"
    result = enrich_result_with_decision(result)
    results = list(data.get("results", []))
    results.append(result)
    await state.update_data(results=results)


async def _finish_workout(message: Message, state: FSMContext, config: Config) -> None:
    data = await state.get_data()
    session = finalize_session(
        data["session"],
        data.get("results", []),
        config.default_timezone,
        total_exercises=len(get_workout(data["workout_type"])),
    )
    await state.update_data(session=session)
    await state.set_state(WorkoutStates.summary)
    await message.answer(format_workout_summary(session, data.get("results", [])), reply_markup=summary_keyboard())


async def _load_settings(user_id: int, google_api: GoogleSheetsAPI) -> dict:
    try:
        row = await google_api.get_settings(user_id)
    except Exception:
        row = None
    if not row:
        return {
            "Show Technique Tips": True,
            "Show Estimated Timing": True,
            "Show Timers": True,
            "Default Rest Seconds": 90,
        }
    return row


def _needs_falls_question(exercise_name: str) -> bool:
    lowered = exercise_name.lower()
    return "стойка" in lowered or "hspu" in lowered


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes", "да", "on", "вкл"}

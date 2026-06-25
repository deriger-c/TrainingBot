from __future__ import annotations

from data.exercise_program import SAFETY_WARNINGS
from models.exercise import Exercise


def format_exercise(exercise: Exercise, index: int, total: int, *, show_tips: bool = True, show_timing: bool = True) -> str:
    lines = [
        f"Упражнение {index}/{total}",
        f"<b>{exercise.name}</b>",
        "",
        f"Блок: {exercise.block}",
        f"План: {exercise.plan_label}",
        f"Отдых: {exercise.effective_rest_label}",
        f"Пример ввода: <code>{exercise.input_example}</code>",
    ]
    if show_timing:
        lines.append(f"Примерное время: {exercise.estimated_minutes} мин")
    if exercise.description:
        lines.extend(["", exercise.description])
    if show_tips and exercise.technique_tips:
        lines.append("")
        lines.append("Техника:")
        lines.extend([f"• {tip}" for tip in exercise.technique_tips[:5]])
    lines.append("")
    lines.append("Безопасность:")
    lines.append(f"• {SAFETY_WARNINGS[0]}")
    return "\n".join(lines)


def format_workout_summary(session: dict, results: list[dict]) -> str:
    completed = [item for item in results if item.get("status") != "skipped"]
    skipped = [item for item in results if item.get("status") == "skipped"]
    lines = [
        "✅ <b>Тренировка завершена</b>",
        "",
        f"Тип: {session.get('workout_type')}",
        f"Дата: {session.get('date')}",
        f"Начало: {session.get('start_time')}",
        f"Конец: {session.get('end_time')}",
        f"Длительность: {session.get('duration_minutes')} мин",
        f"Вес тела: {session.get('body_weight')} кг",
        f"Энергия: {session.get('energy_level')}",
        f"Сон: {session.get('sleep_hours')} ч",
        f"Выполнено упражнений: {len(completed)}",
        f"Пропущено упражнений: {len(skipped)}",
    ]
    if session.get("general_notes"):
        lines.append(f"Заметка: {session['general_notes']}")
    lines.extend(["", "Список упражнений:"])
    for idx, result in enumerate(results, start=1):
        status = "пропущено" if result.get("status") == "skipped" else result.get("actual_result", "")
        lines.append(f"{idx}. {result.get('exercise_name')} — {status}")
    return "\n".join(lines)


def format_history(items: list[dict]) -> str:
    if not items:
        return "История пока пустая. Первая тренировка всё исправит."
    blocks = ["📅 <b>История тренировок</b>"]
    for item in items[:10]:
        blocks.append(
            "\n".join(
                [
                    "",
                    f"Дата: {item.get('Date', item.get('date', ''))}",
                    f"Тренировка: {item.get('Workout Type', item.get('workout_type', ''))}",
                    f"Время: {item.get('Duration Minutes', item.get('duration_minutes', ''))} минут",
                    f"Упражнений: {item.get('Completed Exercises', item.get('completed_exercises', ''))}/{item.get('Total Exercises', item.get('total_exercises', ''))}",
                    f"Заметка: {item.get('General Notes', item.get('general_notes', '')) or '—'}",
                ]
            )
        )
    return "\n".join(blocks)


def format_progress(items: list[dict]) -> str:
    if not items:
        return "📈 Прогресс пока пустой. Сохрани пару тренировок, и здесь появится динамика."
    lines = ["📈 <b>Мой прогресс</b>"]
    for item in items:
        name = item.get("Exercise Name") or item.get("exercise_name") or item.get("name")
        last = item.get("Last Result") or item.get("last_result") or "—"
        best = item.get("Best Result") or item.get("best_result") or "—"
        lines.extend(["", f"<b>{name}</b>:", f"Последний результат: {last}", f"Лучший результат: {best}"])
    return "\n".join(lines)


def format_goals(items: list[dict]) -> str:
    if not items:
        return "🎯 Целей пока нет. Добавь первую цель — например стойку на 60 секунд."
    lines = ["🎯 <b>Мои цели</b>"]
    for item in items:
        goal_id = item.get("Goal ID") or item.get("goal_id")
        name = item.get("Goal Name") or item.get("goal_name")
        category = item.get("Category") or item.get("category")
        target = item.get("Target") or item.get("target")
        current = item.get("Current Result") or item.get("current_result") or "—"
        status = item.get("Status") or item.get("status") or "active"
        lines.extend(
            [
                "",
                f"<b>{name}</b>",
                f"ID: <code>{goal_id}</code>",
                f"Категория: {category}",
                f"Цель: {target}",
                f"Сейчас: {current}",
                f"Статус: {status}",
            ]
        )
    return "\n".join(lines)

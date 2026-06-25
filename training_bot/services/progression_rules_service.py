from __future__ import annotations

import re
from dataclasses import dataclass

from data.progression_rules import EXERCISE_ALIASES, PROGRESSION_RULES, RECOMMENDATION_MESSAGES


@dataclass(slots=True)
class ProgressionDecision:
    status: str
    eligible: bool
    reason: str
    recommendation: str
    next_target: str
    rpe: str


def exercise_key(name: str) -> str:
    lowered = name.lower()
    for key, aliases in EXERCISE_ALIASES.items():
        if any(alias.lower() in lowered or lowered in alias.lower() for alias in aliases):
            return key
    return "default"


def is_hold_exercise(name: str, planned_reps: str = "") -> bool:
    text = f"{name} {planned_reps}".lower()
    return any(token in text for token in ["стойка", "hold", "сек", "sec", "планка"])


def evaluate_progression(exercise_name: str, result: dict) -> ProgressionDecision:
    key = exercise_key(exercise_name)
    rule = PROGRESSION_RULES.get(key, {})
    pain_level = int(result.get("pain_level") or 0)
    technique_ok = bool(result.get("technique_ok", True))
    rir = result.get("rir")
    reserve_seconds = result.get("reserve_seconds")
    fall_count = int(result.get("fall_count") or 0)
    stop_reason = result.get("stop_reason", "")
    set_type = result.get("set_type", "")
    actual = str(result.get("actual_result", ""))

    rpe = rir_to_rpe(rir)
    next_target = str(rule.get("next_target", "Повтори тот же уровень и запиши RIR/технику."))

    if result.get("status") == "skipped":
        return ProgressionDecision(
            status="skipped",
            eligible=False,
            reason="Упражнение пропущено.",
            recommendation="Сохранили пропуск. В следующий раз вернём упражнение в план.",
            next_target=next_target,
            rpe="",
        )

    if pain_level > 0:
        return ProgressionDecision(
            status="pain_stop",
            eligible=False,
            reason=f"Боль {pain_level}/3 блокирует прогрессию.",
            recommendation=RECOMMENDATION_MESSAGES["pain_stop"],
            next_target=next_target,
            rpe=rpe,
        )

    if key in {"chest_to_wall_handstand", "hspu_progression", "elevated_pike_pushup", "scapular_handstand_shrugs"} and fall_count > 0:
        return ProgressionDecision(
            status="progression_locked",
            eligible=False,
            reason=f"Падения: {fall_count}. Усложнение стойки/HSPU заблокировано.",
            recommendation="Оставь тот же уровень. Если падений 2+, заверши блок стойки на сегодня.",
            next_target=next_target,
            rpe=rpe,
        )

    if stop_reason in {"shaking", "technique_loss", "loss_of_control"}:
        return ProgressionDecision(
            status="safe_technical_stop",
            eligible=False,
            reason="Остановка из-за дрожи или потери контроля.",
            recommendation=RECOMMENDATION_MESSAGES["safe_stop"],
            next_target=next_target,
            rpe=rpe,
        )

    if set_type == "max_test" or looks_like_max_test(actual, result.get("planned_reps", "")):
        return ProgressionDecision(
            status="max_test_nonstandard",
            eligible=False,
            reason="Это тест максимума или нестандартная схема.",
            recommendation=RECOMMENDATION_MESSAGES["max_test"],
            next_target=next_target,
            rpe="10" if set_type == "max_test" else rpe,
        )

    if not technique_ok:
        return ProgressionDecision(
            status="technique_issue",
            eligible=False,
            reason="Техника не подтверждена.",
            recommendation="Оставь тот же вес/вариант и сначала закрепи чистую технику.",
            next_target=next_target,
            rpe=rpe,
        )

    if rir in {"unknown", None, ""} and reserve_seconds in {"unknown", None, ""}:
        return ProgressionDecision(
            status="needs_more_data",
            eligible=False,
            reason="Неизвестен запас повторений/секунд.",
            recommendation="Вес пока не повышаем. В следующий раз запиши запас — это главный датчик прогрессии.",
            next_target=next_target,
            rpe="",
        )

    if _has_low_reserve(rir, reserve_seconds):
        return ProgressionDecision(
            status="keep_same",
            eligible=False,
            reason="Запас слишком маленький для повышения.",
            recommendation="Оставь тот же вес/вариант. Цель — чистые подходы с запасом минимум 2 повтора.",
            next_target=next_target,
            rpe=rpe,
        )

    if _looks_complete_at_top_range(actual, result.get("planned_sets", ""), result.get("planned_reps", "")):
        return ProgressionDecision(
            status="comparable_success",
            eligible=True,
            reason="Текущая тренировка подходит как успешная сопоставимая попытка.",
            recommendation=(
                "Отлично. Если это второе такое занятие подряд — можно повышать нагрузку. "
                "Если первое — повтори тот же уровень ещё раз."
            ),
            next_target=next_target,
            rpe=rpe,
        )

    return ProgressionDecision(
        status="keep_same",
        eligible=False,
        reason="Не выполнены все условия для повышения.",
        recommendation=RECOMMENDATION_MESSAGES["keep"],
        next_target=next_target,
        rpe=rpe,
    )


def enrich_result_with_decision(result: dict) -> dict:
    decision = evaluate_progression(str(result.get("exercise_name", "")), result)
    result = dict(result)
    result["progression_status"] = decision.status
    result["progression_eligible"] = decision.eligible
    result["progression_reason"] = decision.reason
    result["recommendation"] = decision.recommendation
    result["next_target"] = decision.next_target
    if decision.rpe:
        result["rpe"] = decision.rpe
    return result


def format_decision_message(result: dict) -> str:
    return "\n".join(
        [
            "✅ Результат сохранён",
            "",
            f"Упражнение: {result.get('exercise_name')}",
            f"Результат: {result.get('actual_result')}",
            f"Статус: {result.get('progression_status')}",
            f"Причина: {result.get('progression_reason')}",
            "",
            result.get("recommendation", ""),
            f"Следующая цель: {result.get('next_target', 'повторить уровень')}",
        ]
    )


def rir_to_rpe(rir: str | int | None) -> str:
    if rir in {None, "", "unknown"}:
        return ""
    try:
        value = int(rir)
    except (TypeError, ValueError):
        return ""
    if value >= 4:
        return "6"
    return str(10 - value)


def looks_like_max_test(actual: str, planned_reps: str) -> bool:
    upper = _planned_upper_bound(planned_reps)
    if upper <= 0:
        return False
    reps = _rep_numbers(actual)
    return bool(reps and max(reps) > upper * 1.5)


def _planned_upper_bound(planned_reps: str) -> int:
    numbers = [int(float(item.replace(",", "."))) for item in re.findall(r"\d+(?:[.,]\d+)?", planned_reps or "")]
    return max(numbers) if numbers else 0


def _has_low_reserve(rir: str | int | None, reserve_seconds: str | int | None) -> bool:
    if rir not in {None, "", "unknown"}:
        return int(rir) <= 1
    if reserve_seconds not in {None, "", "unknown"}:
        return int(reserve_seconds) <= 5
    return False


def _looks_complete_at_top_range(actual: str, planned_sets: str, planned_reps: str) -> bool:
    planned_set_count = _planned_set_count(planned_sets)
    upper = _planned_upper_bound(planned_reps)
    if planned_set_count <= 0 or upper <= 0:
        return False
    values = _rep_numbers(actual)
    if len(values) < planned_set_count:
        return False
    last_sets = values[-planned_set_count:]
    return all(value >= upper for value in last_sets)


def _rep_numbers(actual: str) -> list[int]:
    cleaned = re.sub(
        r"[+\-]?\d+(?:[.,]\d+)?\s*(kg|кг|cm|см|сек|sec|min|мин)",
        "",
        actual,
        flags=re.IGNORECASE,
    )
    return [int(float(item.replace(",", "."))) for item in re.findall(r"\d+(?:[.,]\d+)?", cleaned)]


def _planned_set_count(planned_sets: str) -> int:
    match = re.search(r"\d+", planned_sets or "")
    return int(match.group(0)) if match else 0

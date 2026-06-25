from __future__ import annotations

import re


VALID_RESULT_RE = re.compile(
    r"^(done|skip|[+\-\wа-яА-ЯёЁ .,/:%]+(?:kg|кг|sec|сек|seconds|reps|each leg|на ногу)?[+\-\wа-яА-ЯёЁ .,/:%]*)$",
    re.IGNORECASE,
)


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def validate_result_input(value: str | None) -> tuple[bool, str, str]:
    text = normalize_text(value)
    if not text:
        return False, "", "Пустой ввод. Напиши результат, например: 8/7/6/6 или done."
    if len(text) > 250:
        return False, "", "Слишком длинно. Оставь короткий результат и заметку добавь отдельно."
    if not VALID_RESULT_RE.match(text):
        return False, "", "Формат не похож на результат. Пример: +5kg 6/5/5/4, 30/28 sec, done или skip."
    return True, text, ""


def parse_float(value: str | None, *, min_value: float, max_value: float, field_name: str) -> tuple[bool, float | None, str]:
    text = normalize_text(value).replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return False, None, f"{field_name}: введи число."
    if number < min_value or number > max_value:
        return False, None, f"{field_name}: значение должно быть от {min_value:g} до {max_value:g}."
    return True, number, ""


def extract_weight_used(result: str) -> str:
    lowered = result.lower()
    match = re.search(r"([+\-]?\d+(?:[.,]\d+)?)\s*(kg|кг)", lowered)
    if match:
        return f"{match.group(1).replace(',', '.')}kg"
    if "bodyweight" in lowered or "свой вес" in lowered:
        return "bodyweight"
    return ""


def is_skip_result(result: str) -> bool:
    return normalize_text(result).lower() == "skip"

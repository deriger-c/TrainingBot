from __future__ import annotations

from data.exercise_program import KEY_EXERCISES


def filter_key_progress(items: list[dict]) -> list[dict]:
    if not items:
        return []
    by_name = {
        (item.get("Exercise Name") or item.get("exercise_name") or item.get("name")): item
        for item in items
    }
    result = []
    for key in KEY_EXERCISES:
        for name, item in by_name.items():
            if name and (key.lower() in name.lower() or name.lower() in key.lower()):
                result.append(item)
                break
    return result or items[:12]

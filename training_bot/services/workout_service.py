from __future__ import annotations

from uuid import uuid4

from models.exercise import Exercise, exercise_from_dict
from utils.time_utils import current_time_hhmm, make_session_id, minutes_between, today_iso
from utils.validators import extract_weight_used, is_skip_result


def create_session(workout_type: str, body_weight: float, sleep_hours: float, energy_level: str, timezone_name: str) -> dict:
    date = today_iso(timezone_name)
    start_time = current_time_hhmm(timezone_name)
    return {
        "session_id": make_session_id(workout_type, timezone_name),
        "date": date,
        "start_time": start_time,
        "end_time": "",
        "duration_minutes": 0,
        "workout_type": workout_type,
        "body_weight": body_weight,
        "energy_level": energy_level,
        "sleep_hours": sleep_hours,
        "status": "Started",
        "total_exercises": 0,
        "completed_exercises": 0,
        "general_notes": "",
    }


def make_exercise_result(session: dict, exercise: Exercise, actual_result: str, timezone_name: str) -> dict:
    skipped = is_skip_result(actual_result)
    result_text = "skipped" if skipped else actual_result
    return {
        "result_id": f"res-{uuid4().hex[:10]}",
        "session_id": session["session_id"],
        "date": session["date"],
        "workout_type": session["workout_type"],
        "exercise_order": exercise.order,
        "exercise_name": exercise.name,
        "block": exercise.block,
        "planned_sets": exercise.planned_sets,
        "planned_reps": exercise.planned_reps,
        "planned_rest_seconds": exercise.rest_seconds,
        "actual_result": result_text,
        "weight_used": extract_weight_used(actual_result),
        "difficulty_level": "",
        "rpe": "",
        "pain_or_discomfort": "no",
        "notes": "",
        "completed_at": current_time_hhmm(timezone_name),
        "status": "skipped" if skipped else "completed",
    }


def make_quick_result(text: str, workout_type: str, timezone_name: str) -> dict:
    date = today_iso(timezone_name)
    session_id = f"quick-{date}-{uuid4().hex[:6]}"
    if workout_type in {"A", "B"}:
        session_id = f"quick-{date}-{workout_type}"
    name, result = split_quick_result(text)
    return {
        "result_id": f"res-{uuid4().hex[:10]}",
        "session_id": session_id,
        "date": date,
        "workout_type": workout_type,
        "exercise_order": 0,
        "exercise_name": name,
        "block": "Quick Add",
        "planned_sets": "",
        "planned_reps": "",
        "planned_rest_seconds": 0,
        "actual_result": result,
        "weight_used": extract_weight_used(result),
        "difficulty_level": "",
        "rpe": "",
        "pain_or_discomfort": "no",
        "notes": "Быстрый ввод",
        "completed_at": current_time_hhmm(timezone_name),
        "status": "completed",
    }


def split_quick_result(text: str) -> tuple[str, str]:
    words = text.split()
    if len(words) == 1:
        return words[0], "done"
    for index, word in enumerate(words[1:], start=1):
        if _looks_like_result_token(word):
            return " ".join(words[:index]), " ".join(words[index:])
    return " ".join(words[:-1]), words[-1]


def _looks_like_result_token(word: str) -> bool:
    lowered = word.lower()
    return (
        lowered in {"done", "skip", "bodyweight", "plank"}
        or "/" in lowered
        or lowered.startswith("+")
        or lowered.startswith("-")
        or any(ch.isdigit() for ch in lowered)
        or "kg" in lowered
        or "кг" in lowered
    )


def finalize_session(session: dict, results: list[dict], timezone_name: str, total_exercises: int) -> dict:
    end_time = current_time_hhmm(timezone_name)
    completed = [
        item
        for item in results
        if item.get("status") != "skipped" and item.get("block") != "Warm-up"
    ]
    session = dict(session)
    session.update(
        {
            "end_time": end_time,
            "duration_minutes": minutes_between(session["start_time"], end_time, timezone_name),
            "status": "Completed",
            "total_exercises": total_exercises,
            "completed_exercises": len(completed),
        }
    )
    return session


def sheet_session_row(session: dict) -> dict:
    return {
        "Session ID": session["session_id"],
        "Date": session["date"],
        "Start Time": session["start_time"],
        "End Time": session.get("end_time", ""),
        "Duration Minutes": session.get("duration_minutes", 0),
        "Manual Reported Duration Minutes": session.get("manual_reported_duration_minutes", ""),
        "Duration Source": session.get("duration_source", ""),
        "Duration Conflict": session.get("duration_conflict", ""),
        "Workout Type": session["workout_type"],
        "Body Weight": session.get("body_weight", ""),
        "Energy Level": session.get("energy_level", ""),
        "Sleep Hours": session.get("sleep_hours", ""),
        "Status": session.get("status", ""),
        "Total Exercises": session.get("total_exercises", 0),
        "Completed Exercises": session.get("completed_exercises", 0),
        "General Notes": session.get("general_notes", ""),
    }


def sheet_result_row(result: dict) -> dict:
    return {
        "Result ID": result["result_id"],
        "Session ID": result["session_id"],
        "Date": result["date"],
        "Workout Type": result["workout_type"],
        "Exercise Order": result["exercise_order"],
        "Exercise Name": result["exercise_name"],
        "Block": result["block"],
        "Planned Sets": result.get("planned_sets", ""),
        "Planned Reps": result.get("planned_reps", ""),
        "Planned Rest Seconds": result.get("planned_rest_seconds", 0),
        "Actual Result": result.get("actual_result", ""),
        "Weight Used": result.get("weight_used", ""),
        "Difficulty Level": result.get("difficulty_level", ""),
        "RPE": result.get("rpe", ""),
        "Pain Or Discomfort": result.get("pain_or_discomfort", "no"),
        "Notes": result.get("notes", ""),
        "Completed At": result.get("completed_at", ""),
        "Status": result.get("status", ""),
        "RIR": result.get("rir", ""),
        "Reserve Seconds": result.get("reserve_seconds", ""),
        "Technique OK": result.get("technique_ok", ""),
        "Pain Level": result.get("pain_level", ""),
        "Progression Eligible": result.get("progression_eligible", ""),
        "Progression Status": result.get("progression_status", ""),
        "Progression Reason": result.get("progression_reason", ""),
        "Recommendation": result.get("recommendation", ""),
        "Next Target": result.get("next_target", ""),
        "Set Type": result.get("set_type", ""),
        "Stop Reason": result.get("stop_reason", ""),
        "Fall Count": result.get("fall_count", ""),
        "Variation": result.get("variation", ""),
        "Load Definition": result.get("load_definition", ""),
        "Comparable": result.get("comparable", ""),
    }


def sheet_progress_row(row: dict) -> dict:
    return {
        "Exercise Name": row.get("Exercise Name", row.get("exercise_name", "")),
        "Last Result": row.get("Last Result", row.get("last_result", "")),
        "Best Result": row.get("Best Result", row.get("best_result", "")),
        "Last Date": row.get("Last Date", row.get("last_date", "")),
        "Total Times Done": row.get("Total Times Done", row.get("total_times_done", 0)),
        "Notes": row.get("Notes", row.get("notes", "")),
        "Strict Max": row.get("Strict Max", row.get("strict_max", "")),
        "Progression Lock": row.get("Progression Lock", row.get("progression_lock", "")),
        "Next Target": row.get("Next Target", row.get("next_target", "")),
        "Last RIR": row.get("Last RIR", row.get("last_rir", "")),
        "Last Pain Level": row.get("Last Pain Level", row.get("last_pain_level", "")),
        "Recommendation": row.get("Recommendation", row.get("recommendation", "")),
        "Comparable Success Streak": row.get(
            "Comparable Success Streak",
            row.get("comparable_success_streak", ""),
        ),
    }


def exercise_from_state(data: dict) -> Exercise:
    return exercise_from_dict(data["current_exercise"])

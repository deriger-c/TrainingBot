from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ExerciseResult:
    result_id: str
    session_id: str
    date: str
    workout_type: str
    exercise_order: int
    exercise_name: str
    block: str
    planned_sets: str
    planned_reps: str
    planned_rest_seconds: int
    actual_result: str
    weight_used: str = ""
    difficulty_level: str = ""
    rpe: str = ""
    pain_or_discomfort: str = "no"
    notes: str = ""
    completed_at: str = ""
    status: str = "completed"

    def as_dict(self) -> dict:
        return asdict(self)

    def to_sheet_row(self) -> dict:
        return {
            "Result ID": self.result_id,
            "Session ID": self.session_id,
            "Date": self.date,
            "Workout Type": self.workout_type,
            "Exercise Order": self.exercise_order,
            "Exercise Name": self.exercise_name,
            "Block": self.block,
            "Planned Sets": self.planned_sets,
            "Planned Reps": self.planned_reps,
            "Planned Rest Seconds": self.planned_rest_seconds,
            "Actual Result": self.actual_result,
            "Weight Used": self.weight_used,
            "Difficulty Level": self.difficulty_level,
            "RPE": self.rpe,
            "Pain Or Discomfort": self.pain_or_discomfort,
            "Notes": self.notes,
            "Completed At": self.completed_at,
        }


@dataclass(slots=True)
class WorkoutSession:
    session_id: str
    date: str
    start_time: str
    end_time: str = ""
    duration_minutes: int = 0
    workout_type: str = ""
    body_weight: float = 58.0
    energy_level: str = "Normal"
    sleep_hours: float = 8.0
    status: str = "Started"
    total_exercises: int = 0
    completed_exercises: int = 0
    general_notes: str = ""
    results: list[ExerciseResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        data = asdict(self)
        data["results"] = [result.as_dict() for result in self.results]
        return data

    def to_sheet_row(self) -> dict:
        return {
            "Session ID": self.session_id,
            "Date": self.date,
            "Start Time": self.start_time,
            "End Time": self.end_time,
            "Duration Minutes": self.duration_minutes,
            "Workout Type": self.workout_type,
            "Body Weight": self.body_weight,
            "Energy Level": self.energy_level,
            "Sleep Hours": self.sleep_hours,
            "Status": self.status,
            "Total Exercises": self.total_exercises,
            "Completed Exercises": self.completed_exercises,
            "General Notes": self.general_notes,
        }


def exercise_result_from_dict(data: dict) -> ExerciseResult:
    return ExerciseResult(
        result_id=str(data["result_id"]),
        session_id=str(data["session_id"]),
        date=str(data["date"]),
        workout_type=str(data["workout_type"]),
        exercise_order=int(data["exercise_order"]),
        exercise_name=str(data["exercise_name"]),
        block=str(data["block"]),
        planned_sets=str(data.get("planned_sets", "")),
        planned_reps=str(data.get("planned_reps", "")),
        planned_rest_seconds=int(data.get("planned_rest_seconds", 0)),
        actual_result=str(data.get("actual_result", "")),
        weight_used=str(data.get("weight_used", "")),
        difficulty_level=str(data.get("difficulty_level", "")),
        rpe=str(data.get("rpe", "")),
        pain_or_discomfort=str(data.get("pain_or_discomfort", "no")),
        notes=str(data.get("notes", "")),
        completed_at=str(data.get("completed_at", "")),
        status=str(data.get("status", "completed")),
    )


def workout_session_from_dict(data: dict) -> WorkoutSession:
    results = [exercise_result_from_dict(item) for item in data.get("results", [])]
    return WorkoutSession(
        session_id=str(data["session_id"]),
        date=str(data["date"]),
        start_time=str(data["start_time"]),
        end_time=str(data.get("end_time", "")),
        duration_minutes=int(data.get("duration_minutes", 0)),
        workout_type=str(data.get("workout_type", "")),
        body_weight=float(data.get("body_weight", 58.0)),
        energy_level=str(data.get("energy_level", "Normal")),
        sleep_hours=float(data.get("sleep_hours", 8.0)),
        status=str(data.get("status", "Started")),
        total_exercises=int(data.get("total_exercises", 0)),
        completed_exercises=int(data.get("completed_exercises", 0)),
        general_notes=str(data.get("general_notes", "")),
        results=results,
    )

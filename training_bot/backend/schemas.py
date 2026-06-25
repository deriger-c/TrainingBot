from __future__ import annotations

from pydantic import BaseModel, Field


class WorkoutCreate(BaseModel):
    workout_type: str = "A"
    date: str | None = None
    start_time: str = ""
    body_weight: float | None = None
    sleep_hours: float | None = None
    energy_level: str = ""


class ExerciseSetCreate(BaseModel):
    exercise_name: str
    set_index: int = Field(default=1, ge=1)
    reps: int | None = Field(default=None, ge=0)
    weight: float | None = Field(default=None, ge=0)
    duration_seconds: int | None = Field(default=None, ge=0)
    rir: int | None = Field(default=None, ge=0, le=5)
    pain_level: int = Field(default=0, ge=0, le=3)
    technique_ok: bool = True
    raw_result: str = ""
    planned_sets: str = ""
    planned_reps: str = ""


class WorkoutFinish(BaseModel):
    notes: str = ""


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(default="", max_length=80)
    target: str = Field(default="", max_length=255)
    current_result: str = Field(default="", max_length=255)
    notes: str = ""


class AIRecommendationCreate(BaseModel):
    workout_id: int
    title: str = "AI-разбор тренировки"
    body: str
    priority: str = "normal"

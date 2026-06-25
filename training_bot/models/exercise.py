from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Exercise:
    exercise_id: str
    name: str
    workout_type: str
    block: str
    order: int
    planned_sets: str
    planned_reps: str
    rest_seconds: int
    estimated_minutes: int
    technique_tips: list[str] = field(default_factory=list)
    input_example: str = "done"
    description: str = ""
    rest_label: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def plan_label(self) -> str:
        if self.planned_sets and self.planned_reps:
            return f"{self.planned_sets}x{self.planned_reps}"
        return self.planned_reps or self.planned_sets

    @property
    def effective_rest_label(self) -> str:
        if self.rest_label:
            return self.rest_label
        return f"{self.rest_seconds} сек"


def exercise_from_dict(data: dict) -> Exercise:
    return Exercise(
        exercise_id=data["exercise_id"],
        name=data["name"],
        workout_type=data["workout_type"],
        block=data["block"],
        order=int(data["order"]),
        planned_sets=str(data.get("planned_sets", "")),
        planned_reps=str(data.get("planned_reps", "")),
        rest_seconds=int(data.get("rest_seconds", 0)),
        estimated_minutes=int(data.get("estimated_minutes", 0)),
        technique_tips=list(data.get("technique_tips", [])),
        input_example=str(data.get("input_example", "done")),
        description=str(data.get("description", "")),
        rest_label=str(data.get("rest_label", "")),
    )

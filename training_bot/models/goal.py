from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Goal:
    goal_id: str
    goal_name: str
    category: str
    target: str
    current_result: str = ""
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    def to_sheet_row(self) -> dict:
        return {
            "Goal ID": self.goal_id,
            "Goal Name": self.goal_name,
            "Category": self.category,
            "Target": self.target,
            "Current Result": self.current_result,
            "Status": self.status,
            "Created At": self.created_at,
            "Updated At": self.updated_at,
            "Notes": self.notes,
        }

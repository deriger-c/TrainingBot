from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class UserSettings:
    user_id: int
    default_body_weight: float = 58.0
    show_timers: bool = True
    show_technique_tips: bool = True
    default_rest_seconds: int = 90
    language: str = "ru"
    show_estimated_timing: bool = True

    def as_dict(self) -> dict:
        return asdict(self)

    def to_sheet_row(self) -> dict:
        return {
            "User ID": self.user_id,
            "Default Body Weight": self.default_body_weight,
            "Show Timers": self.show_timers,
            "Show Technique Tips": self.show_technique_tips,
            "Default Rest Seconds": self.default_rest_seconds,
            "Language": self.language,
            "Show Estimated Timing": self.show_estimated_timing,
        }

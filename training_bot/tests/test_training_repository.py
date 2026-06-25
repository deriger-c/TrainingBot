from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace

from services.training_repository import (
    _chart_point_label,
    _chart_point_value,
    _exercise_hint_from_set,
    _next_actions,
    _next_workout_type,
    _pending_ai_label,
    _trend_label,
)


class TrainingRepositoryDashboardTests(unittest.TestCase):
    def test_next_workout_alternates_after_completed_session(self) -> None:
        workouts = [SimpleNamespace(status="completed", workout_type="A")]

        self.assertEqual(_next_workout_type(workouts), "B")

    def test_started_workout_is_kept_as_next_workout(self) -> None:
        workouts = [SimpleNamespace(status="started", workout_type="B")]

        self.assertEqual(_next_workout_type(workouts), "B")

    def test_pain_summary_adds_safety_action(self) -> None:
        actions = _next_actions(
            None,
            "A",
            [],
            {"pain_events": 1, "completed_workouts": 1, "total_sets": 12, "range_label": "7 дней"},
        )

        self.assertEqual(actions[1]["tone"], "danger")
        self.assertIn("не повышай нагрузку", actions[1]["body"])

    def test_trend_label_prefers_pain_block(self) -> None:
        self.assertEqual(_trend_label("comparable_success", 1), "Сначала без боли")

    def test_chart_point_prefers_volume_when_weight_and_reps_exist(self) -> None:
        item = SimpleNamespace(weight=60.0, reps=8, duration_seconds=None, raw_result="60kg 8")

        self.assertEqual(_chart_point_value(item), 480.0)
        self.assertEqual(_chart_point_label(item), "60kg x 8")

    def test_chart_point_uses_duration_for_holds(self) -> None:
        item = SimpleNamespace(weight=None, reps=None, duration_seconds=40, raw_result="40 sec")

        self.assertEqual(_chart_point_value(item), 40.0)
        self.assertEqual(_chart_point_label(item), "40 sec")

    def test_pending_ai_label_uses_russian_plural_forms(self) -> None:
        self.assertEqual(_pending_ai_label(1), "1 тренировка ждёт локальный AI")
        self.assertEqual(_pending_ai_label(2), "2 тренировки ждут локальный AI")
        self.assertEqual(_pending_ai_label(5), "5 тренировок ждут локальный AI")

    def test_exercise_hint_blocks_progression_after_pain(self) -> None:
        item = SimpleNamespace(
            raw_result="40 sec",
            weight=None,
            reps=None,
            duration_seconds=40,
            pain_level=2,
            progression_status="pain_stop",
            technique_ok=True,
            rir=2,
        )
        workout = SimpleNamespace(workout_date=date(2026, 6, 25))

        hint = _exercise_hint_from_set(item, workout)

        self.assertEqual(hint["tone"], "danger")
        self.assertEqual(hint["title"], "Не повышай")
        self.assertIn("боль 2/3", hint["body"])

    def test_exercise_hint_allows_only_cautious_progression_after_success(self) -> None:
        item = SimpleNamespace(
            raw_result="30kg 10",
            weight=30.0,
            reps=10,
            duration_seconds=None,
            pain_level=0,
            progression_status="comparable_success",
            technique_ok=True,
            rir=2,
        )
        workout = SimpleNamespace(workout_date=date(2026, 6, 25))

        hint = _exercise_hint_from_set(item, workout)

        self.assertEqual(hint["tone"], "primary")
        self.assertEqual(hint["title"], "Можно готовить повышение")
        self.assertIn("Если разминка ощущается легко", hint["body"])


if __name__ == "__main__":
    unittest.main()

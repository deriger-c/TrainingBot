from __future__ import annotations

import unittest

from services.progression_rules_service import enrich_result_with_decision


class ProgressionRulesTests(unittest.TestCase):
    def test_pain_blocks_progression(self) -> None:
        result = enrich_result_with_decision(
            {
                "exercise_name": "Подтягивания",
                "actual_result": "bodyweight 6/6/6/6",
                "planned_sets": "4",
                "planned_reps": "4-6",
                "pain_level": 1,
                "rir": 3,
                "technique_ok": True,
                "status": "completed",
            }
        )

        self.assertFalse(result["progression_eligible"])
        self.assertEqual(result["progression_status"], "pain_stop")

    def test_complete_top_range_with_reserve_is_comparable_success(self) -> None:
        result = enrich_result_with_decision(
            {
                "exercise_name": "Подтягивания",
                "actual_result": "bodyweight 6/6/6/6",
                "planned_sets": "4",
                "planned_reps": "4-6",
                "pain_level": 0,
                "rir": 2,
                "technique_ok": True,
                "status": "completed",
            }
        )

        self.assertTrue(result["progression_eligible"])
        self.assertEqual(result["progression_status"], "comparable_success")
        self.assertEqual(result["rpe"], "8")


if __name__ == "__main__":
    unittest.main()

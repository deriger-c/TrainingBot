from __future__ import annotations

import unittest

from local_ai.worker import build_prompt


class LocalAIWorkerTests(unittest.TestCase):
    def test_prompt_keeps_ai_under_rule_engine(self) -> None:
        prompt = build_prompt(
            {
                "workout": {"workout_type": "A", "date": "2026-06-25"},
                "sets": [
                    {
                        "exercise_name": "Подтягивания",
                        "raw_result": "6/6/6/6",
                        "rir": 2,
                        "pain_level": 0,
                        "technique_ok": True,
                        "progression_status": "comparable_success",
                        "recommendation": "Повтори уровень ещё раз.",
                    }
                ],
            }
        )

        self.assertIn("Нельзя советовать повышение нагрузки", prompt)
        self.assertIn("rule=comparable_success", prompt)


if __name__ == "__main__":
    unittest.main()

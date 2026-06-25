from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from local_ai.worker import build_prompt, run_loop


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


class LocalAIWorkerLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_loop_continues_after_failed_cycle(self) -> None:
        stop = RuntimeError("stop test loop")
        with (
            patch("local_ai.worker.run_once", new=AsyncMock(side_effect=[RuntimeError("ollama down"), 1])) as run_once,
            patch("local_ai.worker.asyncio.sleep", new=AsyncMock(side_effect=[None, stop])),
            patch("local_ai.worker.logger.exception") as log_exception,
        ):
            with self.assertRaises(RuntimeError):
                await run_loop(60)

        self.assertEqual(run_once.await_count, 2)
        log_exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()

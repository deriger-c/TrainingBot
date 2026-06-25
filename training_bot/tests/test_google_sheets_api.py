from __future__ import annotations

import sys
import types
import unittest
from typing import Any

sys.modules.setdefault("aiohttp", types.SimpleNamespace())

from services.google_sheets_api import GoogleSheetsAPI


class RecordingGoogleSheetsAPI(GoogleSheetsAPI):
    def __init__(self) -> None:
        super().__init__("https://script.google.com/macros/s/test/exec", "secret")
        self.calls: list[tuple[str, str, dict | None]] = []
        self.backups: list[dict] = []
        self.pending: list[dict] = []

    async def _request(self, method: str, action: str, payload: dict | None = None) -> Any:
        self.calls.append((method, action, payload))
        return {"ok": True}

    async def append_local_backup(self, item: dict) -> None:
        self.backups.append(item)

    async def append_pending(self, item: dict) -> None:
        self.pending.append(item)


class GoogleSheetsAPITests(unittest.IsolatedAsyncioTestCase):
    async def test_save_workout_bundle_uses_single_bundle_request(self) -> None:
        api = RecordingGoogleSheetsAPI()
        session = {
            "session_id": "20260625-1000-A",
            "date": "2026-06-25",
            "start_time": "10:00",
            "workout_type": "A",
            "body_weight": 58,
            "energy_level": "Normal",
            "sleep_hours": 8,
        }
        results = [
            {
                "result_id": "res-1",
                "session_id": "20260625-1000-A",
                "date": "2026-06-25",
                "workout_type": "A",
                "exercise_order": 1,
                "exercise_name": "Подтягивания",
                "block": "Back",
                "actual_result": "6/6/6/6",
            }
        ]

        saved = await api.save_workout_bundle(session, results)

        self.assertTrue(saved)
        self.assertEqual(len(api.calls), 1)
        self.assertEqual(api.calls[0][1], "saveWorkoutBundle")
        self.assertEqual(api.calls[0][2]["session"]["Session ID"], "20260625-1000-A")
        self.assertEqual(api.calls[0][2]["results"][0]["Result ID"], "res-1")
        self.assertEqual(api.pending, [])


if __name__ == "__main__":
    unittest.main()

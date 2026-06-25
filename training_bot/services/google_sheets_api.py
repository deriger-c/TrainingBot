from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import aiohttp

from services.workout_service import sheet_progress_row, sheet_result_row, sheet_session_row

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LOCAL_BACKUP_PATH = DATA_DIR / "local_backup.json"
PENDING_PATH = DATA_DIR / "pending_workouts.json"


class GoogleSheetsAPI:
    def __init__(self, base_url: str, secret: str = "") -> None:
        self.base_url = base_url.strip()
        self.secret = secret.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.base_url != "your_google_apps_script_web_app_url")

    async def _request(self, method: str, action: str, payload: dict | None = None) -> Any:
        if not self.is_configured:
            raise RuntimeError("GOOGLE_SCRIPT_URL не настроен")
        params = {"action": action}
        if self.secret:
            params["secret"] = self.secret
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method.upper() == "GET":
                async with session.get(self.base_url, params=params) as response:
                    return await self._decode_response(response)
            async with session.post(self.base_url, params=params, json=payload or {}) as response:
                return await self._decode_response(response)

    async def _decode_response(self, response: aiohttp.ClientResponse) -> Any:
        text = await response.text()
        if response.status >= 400:
            raise RuntimeError(f"Google Script HTTP {response.status}: {text[:300]}")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Google Script вернул не JSON: {text[:300]}") from exc
        if isinstance(data, dict) and data.get("ok") is False:
            raise RuntimeError(str(data.get("error", "Google Script error")))
        return data

    async def save_workout_bundle(self, session: dict, results: list[dict]) -> bool:
        bundle = {"type": "workout", "session": session, "results": results}
        await self.append_local_backup(bundle)
        try:
            await self._request(
                "POST",
                "saveWorkoutBundle",
                {
                    "session": sheet_session_row(session),
                    "results": [sheet_result_row(result) for result in results],
                },
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save workout to Google Sheets: %s", exc)
            await self.append_pending(bundle)
            return False

    async def save_exercise_result(self, result: dict) -> bool:
        bundle = {"type": "exercise_result", "result": result}
        await self.append_local_backup(bundle)
        try:
            await self._request("POST", "saveExerciseResult", sheet_result_row(result))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save exercise result: %s", exc)
            await self.append_pending(bundle)
            return False

    async def save_progress_row(self, row: dict) -> bool:
        bundle = {"type": "progress_row", "row": row}
        await self.append_local_backup(bundle)
        try:
            await self._request("POST", "saveProgress", sheet_progress_row(row))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save progress row: %s", exc)
            await self.append_pending(bundle)
            return False

    async def save_progress_rows(self, rows: list[dict]) -> tuple[int, int]:
        saved = 0
        failed = 0
        for row in rows:
            if await self.save_progress_row(row):
                saved += 1
            else:
                failed += 1
        return saved, failed

    async def get_history(self) -> list[dict]:
        data = await self._request("GET", "history")
        return data.get("items", data if isinstance(data, list) else [])

    async def get_progress(self) -> list[dict]:
        data = await self._request("GET", "progress")
        return data.get("items", data if isinstance(data, list) else [])

    async def get_goals(self) -> list[dict]:
        data = await self._request("GET", "goals")
        return data.get("items", data if isinstance(data, list) else [])

    async def save_goal(self, goal: dict) -> bool:
        try:
            await self._request("POST", "saveGoal", goal)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save goal: %s", exc)
            return False

    async def update_goal(self, goal_id: str, updates: dict) -> bool:
        try:
            await self._request("POST", "updateGoal", {"goal_id": goal_id, "updates": updates})
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to update goal: %s", exc)
            return False

    async def delete_goal(self, goal_id: str) -> bool:
        try:
            await self._request("POST", "deleteGoal", {"goal_id": goal_id})
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to delete goal: %s", exc)
            return False

    async def get_settings(self, user_id: int) -> dict | None:
        data = await self._request("GET", "getSettings")
        items = data.get("items", [])
        for item in items:
            if str(item.get("User ID", item.get("user_id", ""))) == str(user_id):
                return item
        return None

    async def save_settings(self, settings: dict) -> bool:
        try:
            await self._request("POST", "saveSettings", settings)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save settings: %s", exc)
            return False

    async def sync_pending(self) -> tuple[int, int]:
        pending = await self.read_json(PENDING_PATH)
        if not pending:
            return 0, 0
        sent = 0
        failed: list[dict] = []
        for item in pending:
            try:
                if item.get("type") == "workout":
                    await self._request(
                        "POST",
                        "saveWorkoutBundle",
                        {
                            "session": sheet_session_row(item["session"]),
                            "results": [sheet_result_row(result) for result in item.get("results", [])],
                        },
                    )
                elif item.get("type") == "exercise_result":
                    await self._request("POST", "saveExerciseResult", sheet_result_row(item["result"]))
                elif item.get("type") == "progress_row":
                    await self._request("POST", "saveProgress", sheet_progress_row(item["row"]))
                sent += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Pending sync item failed: %s", exc)
                failed.append(item)
        await self.write_json(PENDING_PATH, failed)
        return sent, len(failed)

    async def append_local_backup(self, item: dict) -> None:
        await self.append_json(LOCAL_BACKUP_PATH, item)

    async def append_pending(self, item: dict) -> None:
        await self.append_json(PENDING_PATH, item)

    async def append_json(self, path: Path, item: dict) -> None:
        data = await self.read_json(path)
        data.append(item)
        await self.write_json(path, data)

    async def read_json(self, path: Path) -> list[dict]:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    async def write_json(self, path: Path, data: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

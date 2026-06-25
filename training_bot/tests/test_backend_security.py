from __future__ import annotations

import hashlib
import hmac
import json
import time
import unittest
from urllib.parse import urlencode

from fastapi import HTTPException

from backend.security import parse_and_validate_init_data


def signed_init_data(bot_token: str, user: dict, auth_date: int | None = None) -> str:
    values = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "test-query",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


class TelegramInitDataTests(unittest.TestCase):
    def test_valid_init_data_returns_user(self) -> None:
        user = parse_and_validate_init_data(
            signed_init_data("123456:token", {"id": 42, "first_name": "Denis", "username": "denis"}),
            "123456:token",
        )

        self.assertEqual(user.telegram_id, 42)
        self.assertEqual(user.first_name, "Denis")

    def test_bad_signature_is_rejected(self) -> None:
        with self.assertRaises(HTTPException):
            parse_and_validate_init_data(
                signed_init_data("123456:token", {"id": 42}) + "x",
                "123456:token",
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

from config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_access_and_script_secret(self) -> None:
        env = {
            "BOT_TOKEN": "123456:token",
            "GOOGLE_SCRIPT_URL": "https://script.google.com/macros/s/test/exec",
            "GOOGLE_SCRIPT_SECRET": "shared-secret",
            "ADMIN_USER_ID": "42",
            "DEFAULT_TIMEZONE": "Asia/Jerusalem",
        }
        with patch.dict(os.environ, env):
            config = load_config()

        self.assertEqual(config.google_script_secret, "shared-secret")
        self.assertEqual(config.admin_user_id, 42)

    def test_placeholder_admin_id_keeps_bot_open(self) -> None:
        env = {
            "BOT_TOKEN": "123456:token",
            "ADMIN_USER_ID": "your_telegram_user_id",
        }
        with patch.dict(os.environ, env):
            config = load_config()

        self.assertIsNone(config.admin_user_id)


if __name__ == "__main__":
    unittest.main()

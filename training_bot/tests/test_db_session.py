from __future__ import annotations

import unittest

from db.session import normalize_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_postgres_url_is_normalized_for_asyncpg(self) -> None:
        self.assertEqual(
            normalize_database_url("postgres://user:pass@example.com/db"),
            "postgresql+asyncpg://user:pass@example.com/db",
        )

    def test_sqlite_url_is_unchanged(self) -> None:
        self.assertEqual(
            normalize_database_url("sqlite+aiosqlite:///./data/training_bot.db"),
            "sqlite+aiosqlite:///./data/training_bot.db",
        )


if __name__ == "__main__":
    unittest.main()

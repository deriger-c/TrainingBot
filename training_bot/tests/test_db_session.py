from __future__ import annotations

import unittest

from db.session import database_connect_args, normalize_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_postgres_url_is_normalized_for_asyncpg(self) -> None:
        self.assertEqual(
            normalize_database_url("postgres://user:pass@example.com/db"),
            "postgresql+asyncpg://user:pass@example.com/db",
        )

    def test_neon_sslmode_is_moved_to_connect_args(self) -> None:
        url = "postgresql://user:pass@example.neon.tech/db?sslmode=require&channel_binding=require"

        self.assertEqual(
            normalize_database_url(url),
            "postgresql+asyncpg://user:pass@example.neon.tech/db",
        )
        self.assertEqual(database_connect_args(url), {"ssl": True})

    def test_sqlite_url_is_unchanged(self) -> None:
        self.assertEqual(
            normalize_database_url("sqlite+aiosqlite:///./data/training_bot.db"),
            "sqlite+aiosqlite:///./data/training_bot.db",
        )


if __name__ == "__main__":
    unittest.main()

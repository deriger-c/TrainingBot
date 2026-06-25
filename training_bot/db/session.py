from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import load_config
from db.base import Base


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    if not url.startswith("postgresql+asyncpg://"):
        return url

    parsed = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in {"sslmode", "channel_binding"}
    ]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def database_connect_args(url: str) -> dict:
    if not url.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
        return {}

    query = dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))
    sslmode = query.get("sslmode", "")
    if sslmode in {"require", "verify-ca", "verify-full"}:
        return {"ssl": True}
    if sslmode == "disable":
        return {"ssl": False}
    return {}


config = load_config()
engine = create_async_engine(
    normalize_database_url(config.database_url),
    pool_pre_ping=True,
    connect_args=database_connect_args(config.database_url),
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

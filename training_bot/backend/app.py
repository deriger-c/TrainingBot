from __future__ import annotations

from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from bot import set_commands
from bot_factory import build_dispatcher
from backend.schemas import AIRecommendationCreate, ExerciseSetCreate, WorkoutCreate, WorkoutFinish
from backend.security import parse_and_validate_init_data, validate_telegram_webhook_secret, validate_worker_token
from config import Config, load_config
from db import get_session, init_db
from db.models import User
from services import training_repository as repo


config = load_config()
bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dispatcher = build_dispatcher(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await set_commands(bot)
    yield
    await bot.session.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Training Bot API", version="0.1.0", lifespan=lifespan)
    allowed_origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]
    if config.miniapp_url:
        allowed_origins.append(config.miniapp_url.rstrip("/"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Telegram-Init-Data", "X-Worker-Token"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "mode": "free-cloud"}

    @app.post("/telegram/webhook")
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(
            default=None,
            alias="X-Telegram-Bot-Api-Secret-Token",
        ),
    ) -> dict:
        validate_telegram_webhook_secret(config, x_telegram_bot_api_secret_token)
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dispatcher.feed_update(bot, update)
        return {"ok": True}

    @app.get("/api/miniapp/dashboard")
    async def miniapp_dashboard(
        user: User = Depends(current_miniapp_user),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        return await repo.dashboard(db, user)

    @app.post("/api/miniapp/workouts")
    async def miniapp_create_workout(
        payload: WorkoutCreate,
        user: User = Depends(current_miniapp_user),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        workout = await repo.create_workout(db, user, payload.model_dump(exclude_none=True))
        return {"ok": True, "workout": repo._workout_payload(workout)}

    @app.post("/api/miniapp/workouts/{workout_id}/sets")
    async def miniapp_add_set(
        workout_id: int,
        payload: ExerciseSetCreate,
        user: User = Depends(current_miniapp_user),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        try:
            item = await repo.add_set(db, user, workout_id, payload.model_dump(exclude_none=True))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"ok": True, "set": repo._set_payload(item)}

    @app.post("/api/miniapp/workouts/{workout_id}/finish")
    async def miniapp_finish_workout(
        workout_id: int,
        payload: WorkoutFinish,
        user: User = Depends(current_miniapp_user),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        try:
            workout = await repo.finish_workout(db, user, workout_id, payload.notes)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"ok": True, "workout": repo._workout_payload(workout)}

    @app.get("/api/coach/pending")
    async def coach_pending(
        _: None = Depends(current_worker),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        return {"items": await repo.pending_workouts_for_ai(db)}

    @app.post("/api/coach/recommendations")
    async def coach_save_recommendation(
        payload: AIRecommendationCreate,
        _: None = Depends(current_worker),
        db: AsyncSession = Depends(get_session),
    ) -> dict:
        rec = await repo.save_ai_recommendation(db, payload.model_dump())
        return {"ok": True, "recommendation": repo._recommendation_payload(rec)}

    return app


async def current_miniapp_user(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_session),
) -> User:
    tg_user = parse_and_validate_init_data(x_telegram_init_data or "", config.bot_token)
    if config.admin_user_id is not None and tg_user.telegram_id != config.admin_user_id:
        raise HTTPException(status_code=403, detail="User is not allowed")
    return await repo.get_or_create_user(
        db,
        telegram_id=tg_user.telegram_id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
        timezone=config.default_timezone,
    )


def current_worker(x_worker_token: str | None = Header(default=None, alias="X-Worker-Token")) -> None:
    validate_worker_token(config, x_worker_token)


app = create_app()

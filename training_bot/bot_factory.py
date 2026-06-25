from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from handlers import common, goals, history, progress, quick_add, settings, start, workout
from middlewares.access_control import AccessControlMiddleware
from services.google_sheets_api import GoogleSheetsAPI
from services.timer_service import TimerService


def build_dispatcher(config: Config) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    dp["config"] = config
    dp["google_api"] = GoogleSheetsAPI(config.google_script_url, config.google_script_secret)
    dp["timer_service"] = TimerService()

    if config.admin_user_id is not None:
        access_control = AccessControlMiddleware(config.admin_user_id)
        dp.message.middleware(access_control)
        dp.callback_query.middleware(access_control)

    dp.include_router(start.router)
    dp.include_router(workout.router)
    dp.include_router(quick_add.router)
    dp.include_router(history.router)
    dp.include_router(progress.router)
    dp.include_router(goals.router)
    dp.include_router(settings.router)
    dp.include_router(common.router)

    return dp

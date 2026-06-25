from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_body_weight = State()
    waiting_rest_seconds = State()

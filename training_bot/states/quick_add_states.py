from aiogram.fsm.state import State, StatesGroup


class QuickAddStates(StatesGroup):
    waiting_text = State()
    choosing_workout = State()

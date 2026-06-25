from aiogram.fsm.state import State, StatesGroup


class GoalStates(StatesGroup):
    waiting_name = State()
    waiting_category = State()
    waiting_target = State()
    waiting_edit_id = State()
    waiting_edit_value = State()
    waiting_complete_id = State()
    waiting_delete_id = State()

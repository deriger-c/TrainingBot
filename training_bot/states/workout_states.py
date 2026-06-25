from aiogram.fsm.state import State, StatesGroup


class WorkoutStates(StatesGroup):
    waiting_body_weight = State()
    waiting_sleep_hours = State()
    waiting_energy_level = State()
    waiting_result = State()
    waiting_rir = State()
    waiting_pain = State()
    waiting_technique = State()
    waiting_falls = State()
    after_result = State()
    waiting_result_note = State()
    warmup_confirm = State()
    summary = State()
    waiting_general_note = State()
    waiting_edit_number = State()
    waiting_edit_result = State()

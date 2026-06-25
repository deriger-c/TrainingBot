from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def settings_keyboard(
    show_timers: bool = True,
    show_tips: bool = True,
    show_timing: bool = True,
) -> InlineKeyboardMarkup:
    timers = "выкл" if show_timers else "вкл"
    tips = "скрыть" if show_tips else "показать"
    timing = "скрыть" if show_timing else "показать"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить вес тела", callback_data="settings:weight")],
            [InlineKeyboardButton(text=f"Таймер отдыха: {timers}", callback_data="settings:toggle_timers")],
            [InlineKeyboardButton(text="Время отдыха по умолчанию", callback_data="settings:rest")],
            [InlineKeyboardButton(text=f"Подсказки по технике: {tips}", callback_data="settings:toggle_tips")],
            [InlineKeyboardButton(text=f"Примерный тайминг: {timing}", callback_data="settings:toggle_timing")],
        ]
    )


def quick_workout_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A", callback_data="quick:A"),
                InlineKeyboardButton(text="B", callback_data="quick:B"),
                InlineKeyboardButton(text="Без тренировки", callback_data="quick:none"),
            ]
        ]
    )

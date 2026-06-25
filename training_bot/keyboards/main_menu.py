from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


BTN_WORKOUT_A = "🏋️ Тренировка A"
BTN_WORKOUT_B = "🏋️ Тренировка B"
BTN_QUICK_ADD = "🔥 Быстрый ввод результата"
BTN_PROGRESS = "📈 Мой прогресс"
BTN_HISTORY = "📅 История тренировок"
BTN_GOALS = "🎯 Цели"
BTN_SETTINGS = "⚙️ Настройки"
BTN_HELP = "❓ Помощь"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_WORKOUT_A), KeyboardButton(text=BTN_WORKOUT_B)],
            [KeyboardButton(text=BTN_QUICK_ADD)],
            [KeyboardButton(text=BTN_PROGRESS), KeyboardButton(text=BTN_HISTORY)],
            [KeyboardButton(text=BTN_GOALS), KeyboardButton(text=BTN_SETTINGS)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )

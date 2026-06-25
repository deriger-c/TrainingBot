from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def energy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Low", callback_data="energy:Low"),
                InlineKeyboardButton(text="Normal", callback_data="energy:Normal"),
                InlineKeyboardButton(text="High", callback_data="energy:High"),
            ],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="workout:cancel")],
        ]
    )


def exercise_input_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Пропустить упражнение", callback_data="workout:skip_waiting"),
            ],
            [
                InlineKeyboardButton(text="Завершить тренировку", callback_data="workout:finish"),
                InlineKeyboardButton(text="Отменить", callback_data="workout:cancel"),
            ],
        ]
    )


def rir_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="4+", callback_data="rir:4"),
                InlineKeyboardButton(text="3", callback_data="rir:3"),
                InlineKeyboardButton(text="2", callback_data="rir:2"),
                InlineKeyboardButton(text="1", callback_data="rir:1"),
                InlineKeyboardButton(text="0", callback_data="rir:0"),
            ],
            [InlineKeyboardButton(text="Не знаю", callback_data="rir:unknown")],
        ]
    )


def reserve_seconds_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="15+ сек", callback_data="reserve:15"),
                InlineKeyboardButton(text="10 сек", callback_data="reserve:10"),
                InlineKeyboardButton(text="5 сек", callback_data="reserve:5"),
                InlineKeyboardButton(text="0 сек", callback_data="reserve:0"),
            ],
            [InlineKeyboardButton(text="Не знаю", callback_data="reserve:unknown")],
        ]
    )


def pain_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0", callback_data="pain:0"),
                InlineKeyboardButton(text="1", callback_data="pain:1"),
                InlineKeyboardButton(text="2", callback_data="pain:2"),
                InlineKeyboardButton(text="3+", callback_data="pain:3"),
            ],
        ]
    )


def technique_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, чисто", callback_data="technique:ok"),
                InlineKeyboardButton(text="Нет, были ошибки", callback_data="technique:issue"),
            ],
        ]
    )


def falls_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0", callback_data="falls:0"),
                InlineKeyboardButton(text="1", callback_data="falls:1"),
                InlineKeyboardButton(text="2+", callback_data="falls:2"),
            ],
        ]
    )


def after_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Запустить таймер", callback_data="rest:start")],
            [
                InlineKeyboardButton(text="✅ Следующее упражнение", callback_data="workout:next"),
                InlineKeyboardButton(text="📝 Добавить заметку", callback_data="workout:note"),
            ],
            [
                InlineKeyboardButton(text="↩️ Повторить ввод", callback_data="workout:retry"),
                InlineKeyboardButton(text="⏭ Пропустить упражнение", callback_data="workout:skip_last"),
            ],
            [InlineKeyboardButton(text="🏁 Завершить тренировку", callback_data="workout:finish")],
        ]
    )


def rest_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏭ Пропустить отдых", callback_data="rest:skip"),
                InlineKeyboardButton(text="➕ +30 секунд", callback_data="rest:add30"),
            ],
            [InlineKeyboardButton(text="✅ Перейти дальше", callback_data="workout:next")],
        ]
    )


def warmup_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, начать тренировку", callback_data="warmup:done")],
            [InlineKeyboardButton(text="Повторить разминку", callback_data="warmup:repeat")],
            [InlineKeyboardButton(text="Пропустить к основной части", callback_data="warmup:skip")],
        ]
    )


def summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="summary:save")],
            [
                InlineKeyboardButton(text="✏️ Изменить упражнение", callback_data="summary:edit"),
                InlineKeyboardButton(text="📝 Добавить общую заметку", callback_data="summary:note"),
            ],
            [InlineKeyboardButton(text="❌ Отменить тренировку", callback_data="summary:cancel")],
        ]
    )

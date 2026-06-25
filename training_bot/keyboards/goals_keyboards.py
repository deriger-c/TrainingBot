from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def goals_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Мои цели", callback_data="goals:list")],
            [InlineKeyboardButton(text="➕ Добавить цель", callback_data="goals:add")],
            [InlineKeyboardButton(text="✏️ Изменить цель", callback_data="goals:edit")],
            [InlineKeyboardButton(text="✅ Отметить выполненной", callback_data="goals:complete")],
            [InlineKeyboardButton(text="🗑 Удалить цель", callback_data="goals:delete")],
        ]
    )


def goals_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад к целям", callback_data="goals:menu")]]
    )

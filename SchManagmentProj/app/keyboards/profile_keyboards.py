from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from app.handlers import ItemCallback

standard_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📆 Календарь событий", callback_data=ItemCallback(callback_action="event_list",
                                                                                 data="main").pack())]])

admin_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📆 Календарь событий",
                          callback_data=ItemCallback(callback_action="event_list", data="main").pack())],
    [InlineKeyboardButton(text="📢 Объявления", callback_data="announcement_menu")],
    [InlineKeyboardButton(text="📋 Задачи", callback_data="task_menu")]])

create_profile = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="▶️ Создать профиль", callback_data="create_profile")]])

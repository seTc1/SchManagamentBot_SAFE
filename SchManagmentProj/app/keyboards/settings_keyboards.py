from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

settings_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="📝 Изменить роль аккаунта", callback_data="blank_callback")],
                     [InlineKeyboardButton(text="🔔 Вкл/выкл уведомления", callback_data="blank_callback")],
                     [InlineKeyboardButton(text="↩️ В профиль", callback_data="profile")]]
)

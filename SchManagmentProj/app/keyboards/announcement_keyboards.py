from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

announcement_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📆 Опрос о событии", callback_data="profile")],
    [InlineKeyboardButton(text="📢 Уведомление всем", callback_data="send_all_announce")],
    [InlineKeyboardButton(text="↩️ В профиль", callback_data="profile")]
])

announcement_preview_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="✅ Отправить"),
        KeyboardButton(text="✏️ Изменить")
    ],
    [
        KeyboardButton(text="❌ Отменить")
    ]
],
    resize_keyboard=True,
    one_time_keyboard=True)

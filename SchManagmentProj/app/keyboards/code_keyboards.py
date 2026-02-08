from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

pass_code = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика кодов", callback_data="view_codes")]])

select_code_type = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌐 Ученик"), KeyboardButton(text="👤 Учитель")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

select_student_distribution = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Личный"), KeyboardButton(text="🌐 Общий")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

select_class_grade = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="10"), KeyboardButton(text="11")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

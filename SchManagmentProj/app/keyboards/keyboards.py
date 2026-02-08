from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

not_founded = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Открыть профиль", callback_data="profile")]])

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Public keyboards

decline_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Подтвердить")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


def build_cancel_keyboard(text) -> ReplyKeyboardMarkup:
    if text:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"{text}")],
                [KeyboardButton(text="❌ Отменить")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return keyboard


# --- Dynamic builders ---
def make_keyboard_from_list(items: list, buttons_per_row: int = 4, include_cancel: bool = True) -> ReplyKeyboardMarkup:
    keyboard = []
    row = []
    for i, item in enumerate(items):
        row.append(KeyboardButton(text=str(item)))
        if (i + 1) % buttons_per_row == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    if include_cancel:
        keyboard.append([KeyboardButton(text="❌ Отменить")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def make_letters_keyboard(letters: list[str]) -> ReplyKeyboardMarkup:
    return make_keyboard_from_list(letters)


def make_grades_keyboard(grades: list[int]) -> ReplyKeyboardMarkup:
    return make_keyboard_from_list(grades)

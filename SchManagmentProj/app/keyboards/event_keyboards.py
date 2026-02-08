from datetime import date, timedelta
from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from app.database.models.event_models import Event
from app.handlers import ItemCallback

from app.utils.utils import weekday_names

event_creation_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Создать событие")],
        [KeyboardButton(text="🖼️ Прикрепить фото")],
        [KeyboardButton(text="✏️ Изменить")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

event_edit_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💾 Сохранить изменения")],
        [KeyboardButton(text="✏️ Изменить")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

date_start_select = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕑 Текущая дата и время")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

date_end_select = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕑 Через 1 час")],
        [KeyboardButton(text="🕑 Через 12 часов")],
        [KeyboardButton(text="🕑 Через 1 день")],
        [KeyboardButton(text="🕑 Через 3 дня")],
        [KeyboardButton(text="🕑 Через 1 неделю")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


def build_week_keyboard(start_of_week_date: date, events: List[Event],
                        can_redact: bool = False) -> InlineKeyboardMarkup:
    rows = []

    for day_num in range(7):
        day_date = start_of_week_date + timedelta(days=day_num)
        matching = [
            event for event in events
            if (getattr(event, "start_at").date() <= day_date <= getattr(event, "end_at").date())
        ]

        weekday_display = weekday_names[day_num].capitalize()
        date_display = f"{day_date.day}.{day_date.month}"

        if not matching:
            text = f"📆 {weekday_display} ({date_display}): (Нет события)"
        else:
            first_title = matching[0].title
            extra = len(matching) - 1
            extra_text = f" (+{extra})" if extra > 0 else ""
            text = f"📌 {weekday_display} ({date_display}): {first_title}{extra_text}"

        # теперь передаём индекс события в callback (по умолчанию 0)
        day_callback = ItemCallback(callback_action="event_info", data=f"{day_date.isoformat()} 0").pack()
        rows.append([InlineKeyboardButton(text=text, callback_data=day_callback)])

    next_week_callback = ItemCallback(callback_action="event_list",
                                      data=f"set {(start_of_week_date + timedelta(days=7)).isoformat()}").pack()
    prev_week_callback = ItemCallback(callback_action="event_list",
                                      data=f"set {(start_of_week_date - timedelta(days=7)).isoformat()}").pack()

    rows.append([InlineKeyboardButton(text="⬅️", callback_data=prev_week_callback),
                 InlineKeyboardButton(text="↩️ В профиль", callback_data="profile"),
                 InlineKeyboardButton(text="➡️", callback_data=next_week_callback)])

    if can_redact:
        rows.append([InlineKeyboardButton(text="✏️ Создать событие", callback_data="create_event")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_event_info_keyboard(event: Event, index: int = 0, total: int = 1,
                              day_date: date = None, can_redact: bool = False) -> InlineKeyboardMarkup:
    event_start_date = getattr(event, "start_at").date()
    start_of_week = event_start_date - timedelta(days=event_start_date.weekday())

    back_callback = ItemCallback(
        callback_action="event_list",
        data=f"set {start_of_week.isoformat()}"
    ).pack()

    rows = []

    # Navigation arrows to multiple events
    if total and total > 1 and day_date is not None:
        prev_index = (index - 1) % total
        next_index = (index + 1) % total

        prev_cb = ItemCallback(callback_action="event_info", data=f"{day_date.isoformat()} {prev_index}").pack()
        next_cb = ItemCallback(callback_action="event_info", data=f"{day_date.isoformat()} {next_index}").pack()

        rows.append([InlineKeyboardButton(text="⬅️", callback_data=prev_cb),
                     InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data="pages_count"),
                     InlineKeyboardButton(text="➡️", callback_data=next_cb)])

    # Check redact rights
    if can_redact:
        delete_callback = ItemCallback(callback_action="event_delete", data=str(getattr(event, "id"))).pack()
        redact_callback = ItemCallback(callback_action="edit_event", data=str(getattr(event, 'id'))).pack()
        hide_callback = "just_answer_callback"

        rows.append([InlineKeyboardButton(text="✏️ Редактировать событие", callback_data=redact_callback)])
        rows.append([InlineKeyboardButton(text="📥 Скрыть событие", callback_data=hide_callback)])
        rows.append([InlineKeyboardButton(text="❌ Удалить событие", callback_data=delete_callback)])

    rows.append([InlineKeyboardButton(text="↩️ Обратно", callback_data=back_callback)])
    event_info_keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    return event_info_keyboard

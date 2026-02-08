from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from app.database.models.task_models import Task
from typing import List

import asyncio

from app.database.models.user_models import ManagementType, UserRole, User
from app.database.requests.user_requests import get_existing_managers
from app.handlers import ItemCallback

from app.utils import month_names

# Static keyboards

date_end_select = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕑 Через 1 день")],
        [KeyboardButton(text="🕑 Через 7 дней")],
        [KeyboardButton(text="🕑 Через 14 дней")],
        [KeyboardButton(text="🕑 Через 21 день")],
        [KeyboardButton(text="🕑 Через 28 дней")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

task_creation_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Создать задачу")],
        [KeyboardButton(text="✏️ Изменить")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

task_edit_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💾 Сохранить изменения")],
        [KeyboardButton(text="✏️ Изменить")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# Keyboard builders

def build_task_menu_keyboard(user_object: User):
    if user_object.manager_role == ManagementType.president or user_object.role == UserRole.teacher:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Трекер задач", callback_data="task_tracker_menu")],
            [InlineKeyboardButton(text="📊 Министерский отчёт", callback_data="just_answer_callback")],
            [InlineKeyboardButton(text="↩️ Обратно", callback_data="profile")]
        ])

    else:

        report_cb = ItemCallback(callback_action="self_task_report", data=str(user_object.id)).pack()
        planer_cb = ItemCallback(callback_action="task_planer", data=str(user_object.id)).pack()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗂 Планер задач", callback_data=planer_cb)],
            [InlineKeyboardButton(text="💼 Отчёт", callback_data=report_cb)],
            [InlineKeyboardButton(text="↩️ В профиль", callback_data="profile")]
        ])

    return keyboard


def build_task_info_keyboard(task: Task, user_id) -> InlineKeyboardMarkup:
    complete_cb = ItemCallback(callback_action="complete_task", data=str(getattr(task, "id"))).pack()
    redact_cb = ItemCallback(callback_action="edit_task", data=str(getattr(task, "id"))).pack()
    delete_cb = ItemCallback(callback_action="task_delete", data=str(getattr(task, "id"))).pack()
    back_cb = ItemCallback(callback_action="task_planer", data=str(user_id)).pack()

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Завершить", callback_data=complete_cb)],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=redact_cb)],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=delete_cb)],
            [InlineKeyboardButton(text="↩️ Назад", callback_data=back_cb)]
        ]
    )


def build_completed_task_info_keyboard(task: Task, user_id) -> InlineKeyboardMarkup:
    delete_cb = ItemCallback(callback_action="task_delete", data=str(getattr(task, "id"))).pack()
    back_cb = ItemCallback(callback_action="completed_task_menu", data=str(user_id)).pack()

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить", callback_data=delete_cb)],
            [InlineKeyboardButton(text="↩️ Обратно", callback_data=back_cb)]
        ]
    )


def build_self_report_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    prev_cb = ItemCallback(callback_action="self_task_report",
                           data=f"set {prev_year}-{prev_month:02d}").pack()
    next_cb = ItemCallback(callback_action="self_task_report",
                           data=f"set {next_year}-{next_month:02d}").pack()

    rows = [[
        InlineKeyboardButton(text="⬅️", callback_data=prev_cb),
        InlineKeyboardButton(text="↩️ Обратно", callback_data="task_menu"),
        InlineKeyboardButton(text="➡️", callback_data=next_cb)]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_task_tracker_menu_keyboard(manager_objects) -> InlineKeyboardMarkup:
    rows = []

    for manager_object in manager_objects:
        if manager_object.manager_role != ManagementType.president:
            user_data_cb = ItemCallback(callback_action="task_planer", data=str(manager_object.id)).pack()
            rows.append([InlineKeyboardButton(text=f"👤 {manager_object.user_desc}", callback_data=user_data_cb)])

    rows.append([InlineKeyboardButton(text="↩️ Обратно", callback_data="task_menu")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_task_planer_keyboard(tasks: List[Task], user_id, page: int = 1,
                               page_size: int = 5, back_to: str = "task_menu") -> InlineKeyboardMarkup:
    complete_cb = ItemCallback(callback_action="completed_task_menu", data=str(user_id)).pack()

    if not tasks:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗃️ Завершённые", callback_data=complete_cb)],
            [InlineKeyboardButton(text="✏️ Создать задачу",
                                  callback_data=ItemCallback(callback_action="create_task", data=str(user_id)).pack())],
            [InlineKeyboardButton(text="↩️ Обратно", callback_data=back_to)]
        ])
        return keyboard

    total = len(tasks)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Нормализация номера страницы
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_tasks = tasks[start:end]

    rows: List[List[InlineKeyboardButton]] = []
    for task in page_tasks:
        rows.append([InlineKeyboardButton(text=f"📋 {task.title}",
                                          callback_data=ItemCallback(callback_action="task_info",
                                                                     data=str(getattr(task, "id"))).pack())])

    # Добавляем панель навигации только если страниц > 1
    if total_pages > 1:
        left_data = right_data = [str(user_id)]

        left_data.append(str(page - 1)) if page > 1 else left_data.append(str(total_pages))
        right_data.append(str(page + 1)) if page < total_pages else right_data.append("1")

        print(left_data, right_data)
        print(' '.join(left_data), ' '.join(right_data))

        left_cb = ItemCallback(callback_action="task_planer_page", data=' '.join(left_data)).pack()
        right_cb = ItemCallback(callback_action="task_planer_page", data=' '.join(right_data)).pack()

        rows.append([
            InlineKeyboardButton(text="⬅️", callback_data=left_cb),
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="pages_count"),
            InlineKeyboardButton(text="➡️", callback_data=right_cb)
        ])

    # Остальные пункты меню

    rows.append([InlineKeyboardButton(text="🗃️ Завершённые", callback_data=complete_cb)])
    rows.append([InlineKeyboardButton(text="✏️ Создать задачу",
                                      callback_data=ItemCallback(callback_action="create_task",
                                                                 data=str(user_id)).pack())])
    rows.append([InlineKeyboardButton(text="↩️ Обратно", callback_data=back_to)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_completed_task_keyboard(tasks: List[Task], user_id, page: int = 1,
                                  page_size: int = 5) -> InlineKeyboardMarkup:
    back_cb = ItemCallback(callback_action="task_planer", data=str(user_id)).pack()

    if not tasks:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="↩️ Обратно", callback_data=back_cb)]])
        return keyboard

    total = len(tasks)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    page_tasks = tasks[start:end]

    rows: List[List[InlineKeyboardButton]] = []
    for task in page_tasks:
        rows.append([InlineKeyboardButton(text=f"📋 {task.title}",
                                          callback_data=ItemCallback(callback_action="task_info",
                                                                     data=str(getattr(task, "id"))).pack())])

    if total_pages > 1:
        left_cb = ItemCallback(callback_action="completed_task_page",
                               data=str(page - 1)).pack() if page > 1 else ItemCallback(
            callback_action="completed_task_page", data=str(total_pages)).pack()
        right_cb = ItemCallback(callback_action="completed_task_page",
                                data=str(page + 1)).pack() if page < total_pages else ItemCallback(
            callback_action="completed_task_page", data="1").pack()
        rows.append([
            InlineKeyboardButton(text="⬅️", callback_data=left_cb),
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="pages_count"),
            InlineKeyboardButton(text="➡️", callback_data=right_cb)
        ])

    rows.append([InlineKeyboardButton(text="↩️ Обратно", callback_data=back_cb)])

    return InlineKeyboardMarkup(inline_keyboard=rows)

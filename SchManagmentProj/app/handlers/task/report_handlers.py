from datetime import timedelta, datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.keyboards import cancel_keyboard, build_cancel_keyboard
from app.keyboards.task_keyboards import *
from app.handlers import ItemCallback

from app.handlers.profile_handlers import cmd_profile
from app.database.requests.user_requests import get_user_by_tg_id
from app.database.requests.task_requests import (
    create_task, get_task_by_title, update_task,
    get_user_completed_tasks
)
from app.utils import try_parse_datetime, local_now, format_dt, month_names

router = Router()


@router.callback_query(ItemCallback.filter(F.callback_action == "self_task_report"))
async def callback_self_task_report(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    user_id = callback_query.from_user.id if callback_query.from_user else None
    if not user_id:
        await callback_query.answer()
        return

    data = callback_data.data.split()
    print(data)
    now = local_now()
    year = now.year
    month = now.month

    if not data:
        await callback_query.answer("Неверные данные в callback.", show_alert=True)
        return

    if data[0] == "main":
        text = await build_month_report_text(user_id, year, month)
        keyboard = build_self_report_keyboard(year, month)
    elif data[0] == "set":
        try:
            year_str, month_str = data[1].split("-")
            year = int(year_str)
            month = int(month_str)
            text = await build_month_report_text(user_id, year, month)
            keyboard = build_self_report_keyboard(year, month)
        except Exception:
            await callback_query.answer("Неверные данные в callback.", show_alert=True)

            return
    elif data[0].isdigit():
        # если в callback передан id пользователя — показываем отчёт этого пользователя
        try:
            target_user_id = int(data[0])
            text = await build_month_report_text(target_user_id, year, month)
            keyboard = build_self_report_keyboard(year, month)
        except Exception:
            await callback_query.answer("Неверные данные в callback.", show_alert=True)
            return
    else:
        await callback_query.answer("Неверный формат callback.", show_alert=True)
        return

    try:
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(text, reply_markup=keyboard)

    await callback_query.answer()


async def build_month_report_text(user_id: int, year: int, month: int) -> str:
    tasks = await get_user_completed_tasks(user_id)
    filtered = [
        task for task in tasks
        if getattr(task, "completed_at") is not None
           and getattr(task, "completed_at").year == year
           and getattr(task, "completed_at").month == month
    ]

    header = f"Ваш отчёт по задачам:\n— {month_names[month - 1]} {year} года\n"
    if not filtered:
        return header + "\nЗавершённых задач нет."

    parts = [header, "--------------------------------------"]
    for i, t in enumerate(filtered, start=1):
        title = getattr(t, "title", "") or ""
        desc = getattr(t, "description", "") or ""
        complete_desc = getattr(t, "complete_desc", "") or ""
        started = getattr(t, "created_at", None)
        completed = getattr(t, "completed_at", None)
        deadline = getattr(t, "end_at", None)

        started_str = started.date().isoformat() if started else ""
        completed_str = completed.date().isoformat() if completed else ""
        deadline_str = deadline.date().isoformat() if deadline else ""

        block = (
            f"[{i}] • {title}\n\n"
            f"• {desc}\n\n"
            f"• {complete_desc}\n\n"
            f"• Задача начата: {started_str}\n"
            f"• Задача завершена: {completed_str}\n\n"
            f"• Дедлайн задачи: {deadline_str}\n"
            "--------------------------------------"
        )
        parts.append(block)
    return "\n".join(parts)

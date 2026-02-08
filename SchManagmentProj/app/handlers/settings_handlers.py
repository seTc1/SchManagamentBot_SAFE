from datetime import datetime, timedelta, time as dt_time, date as dt_date

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import ItemCallback

from app.keyboards.settings_keyboards import settings_keyboard

from app.handlers.profile_handlers import cmd_profile

from app.database.requests.user_requests import get_user_by_tg_id
from app.database.requests.event_requests import create_event, get_event_by_name, get_events_in_range, \
    get_events_by_date

router = Router()


@router.callback_query(F.data == "settings_menu")
async def callback_settings_menu(callback_query: CallbackQuery):
    if not callback_query.message:
        await callback_query.answer()
        return
    await callback_query.message.edit_text(
        f"Настройки:",
        reply_markup=settings_keyboard
    )
    await callback_query.answer()

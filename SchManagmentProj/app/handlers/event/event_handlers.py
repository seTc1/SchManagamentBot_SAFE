from datetime import datetime, timedelta, time as dt_time, date as dt_date

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from app.database.models.user_models import UserRole, ManagementType

from app.database.requests.user_requests import get_user_by_tg_id, get_user_data
from app.handlers import ItemCallback

from app.keyboards.keyboards import confirm_keyboard, build_cancel_keyboard

from app.keyboards.event_keyboards import (
    build_week_keyboard,
    build_event_info_keyboard,
)
from app.database.requests.event_requests import get_events_in_range, get_events_by_date, soft_delete_event, \
    get_event_by_id, get_event_data

from app.handlers.event.event_creation_handlers import EventCreation

from app.utils import event_month_names, weekday_names

router = Router()


class DeleteEventStates(StatesGroup):
    waiting_for_confirmation = State()


@router.callback_query(ItemCallback.filter(F.callback_action == "event_list"))
async def callback_event_list(callback_query: CallbackQuery, callback_data: ItemCallback):
    # Error check
    if not callback_query.message:
        await callback_query.answer()
        return

    data = callback_data.data.split()
    if data[0] == "main":
        today = datetime.today()
        start_of_week_date = (today - timedelta(days=today.weekday())).date()
    elif data[0] == "set":
        try:
            start_of_week_date = dt_date.fromisoformat(data[1])
        except Exception:
            await callback_query.answer("Неверная дата в callback.", show_alert=True)
            return
    else:
        await callback_query.answer()
        return

    # Data
    user_object = await get_user_by_tg_id(callback_query.from_user.id)
    user_data = await get_user_data(user_object.id)

    start_dt = datetime.combine(start_of_week_date, dt_time.min)
    end_dt = datetime.combine(start_of_week_date + timedelta(days=6), dt_time.max)

    events = await get_events_in_range(start_dt, end_dt)

    # Role check for event creation keyboard
    if user_data["role"] in [UserRole.management, UserRole.admin, UserRole.teacher]:
        keyboard = build_week_keyboard(start_of_week_date, events, True)
    else:
        keyboard = build_week_keyboard(start_of_week_date, events, False)

    # Handler
    month_name = event_month_names[datetime.now().month - 1]
    weekday_name = weekday_names[datetime.now().weekday()]

    start_str = start_of_week_date.strftime("%d.%m.%Y")
    end_str = (start_of_week_date + timedelta(days=6)).strftime("%d.%m.%Y")
    date_text = f"Сегодня {weekday_name}, {datetime.now().day} {month_name}"

    text = (
        "💼 Расписание школьных событий на неделю\n\n"
        f"📆 {date_text}\n"
        f"📋 Показывается неделя: {start_str} - {end_str}"
    )

    try:
        # Пытаемся отредактировать текст — если сообщение было медиа (фото),
        # Telegram выдаст ошибку "there is no text in the message to edit".
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        # В случае ошибки — удаляем старое сообщение (если возможно) и отправляем новое текстовое,
        # тем самым убирая картинку.
        try:
            await callback_query.message.delete()
        except Exception:
            # Если удалить не получилось — просто отправим новое сообщение.
            pass
        await callback_query.message.answer(text, reply_markup=keyboard)

    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "event_info"))
async def callback_event_info(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    raw = callback_data.data or ""
    parts = raw.split()
    try:
        day_iso = parts[0]
        query_date = dt_date.fromisoformat(day_iso)
    except Exception:
        await callback_query.answer("Неверная дата в callback.", show_alert=True)
        return

    try:
        index = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        index = 0

    event_objects = await get_events_by_date(query_date)
    if not event_objects:
        await callback_query.answer("Событий на этот день нет.", show_alert=True)
        return

    # нормализуем индекс в пределах [0, len-1]
    total = len(event_objects)
    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    event = event_objects[index]

    # Data
    user_object = await get_user_by_tg_id(callback_query.from_user.id)
    user_data = await get_user_data(user_object.id)

    event_data = await get_event_data(event.id)

    # Role check for event creation keyboard
    if (user_data["role"] in [UserRole.admin, UserRole.teacher] or user_data["manager_role"] == ManagementType.president
            or user_data.get("id") == event_data.get("created_by")):
        keyboard = build_event_info_keyboard(event, index=index, total=total, day_date=query_date, can_redact=True)
    else:
        keyboard = build_event_info_keyboard(event, index=index, total=total, day_date=query_date, can_redact=False)

    start_at_formatted = event.start_at.strftime("%d.%m.%Y %H:%M")
    end_at_formatted = event.end_at.strftime("%d.%m.%Y %H:%M")

    caption = (
        f"📌 Название события: {event.title.capitalize()}\n\n"
        f"📃 Описание:\n{event.description.capitalize()}\n\n"
        f"⏰ Даты проведения:\n"
        f"🎉 Начало: {start_at_formatted}\n"
        f"⏱️ Окончание: {end_at_formatted}"
    )

    image_key = getattr(event, "image_storage_key", None)
    if image_key:
        try:
            await callback_query.message.edit_media(
                media=InputMediaPhoto(media=image_key, caption=caption),
                reply_markup=keyboard
            )
            await callback_query.answer()
            return
        except Exception:
            # Фото может быть недоступно по telegram id или редактирование медиа не поддержимо — fallback к тексту.
            pass

    try:
        await callback_query.message.edit_text(caption, reply_markup=keyboard)
    except TelegramBadRequest:
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(caption, reply_markup=keyboard)

    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "event_delete"))
async def callback_event_delete(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    raw = callback_data.data or ""
    try:
        event_id = int(raw)
    except Exception:
        await callback_query.answer("Неверный идентификатор события.", show_alert=True)
        return

    await state.update_data(pending_delete_event_id=event_id)
    await state.set_state(DeleteEventStates.waiting_for_confirmation)

    await callback_query.message.answer(
        "Вы действительно хотите удалить событие?",
        reply_markup=confirm_keyboard
    )

    await callback_query.answer()


@router.message(StateFilter(DeleteEventStates.waiting_for_confirmation))
async def confirm_delete_message(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    data = await state.get_data()
    event_id = data.get("pending_delete_event_id")

    if not event_id:
        await message.answer("Нет данных о событии. Отмена.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    if text == "✅ Подтвердить":
        deleted_by = message.from_user.id if message.from_user else None
        deleted_event = await soft_delete_event(event_id, deleted_by)
        if deleted_event:
            await message.answer("Событие успешно удалено.", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("Событие не найдено или уже удалено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    elif text == "❌ Отменить":
        await message.answer("Удаление отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await message.answer('Пожалуйста, дайте ответ через кнопку "✅ Подтвердить" или "❌ Отменить"')


@router.callback_query(ItemCallback.filter(F.callback_action == "edit_event"))
async def callback_edit_event(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    try:
        event_id = int(callback_data.data)
    except Exception:
        await callback_query.answer("Некорректный идентификатор события", show_alert=True)
        return

    event = await get_event_by_id(event_id)
    if not event:
        await callback_query.answer("Событие не найдено", show_alert=True)
        return

    await state.clear()
    await state.update_data(
        title=event.title,
        description=event.description or "",
        start_at=event.start_at,
        end_at=event.end_at,
        image_file_id=getattr(event, "image_storage_key", None),
        editing_event_id=event.id
    )
    await state.set_state(EventCreation.title_input)

    keyboard = build_cancel_keyboard(event.title)
    await callback_query.message.answer("Вы начали редактирование события.\n\nОтправьте исправленное название события.",
                                        reply_markup=keyboard)
    await callback_query.answer()

from datetime import timedelta, datetime

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.keyboards import cancel_keyboard, build_cancel_keyboard
from app.keyboards.task_keyboards import *

from app.handlers.profile_handlers import cmd_profile
from app.database.requests.user_requests import get_user_by_tg_id, get_president
from app.database.requests.task_requests import create_task, get_task_by_title, update_task
from app.utils import try_parse_datetime, local_now, format_dt
from app.utils.notif_sender import send_notification_by_id

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.handlers import ItemCallback

router = Router()


class TaskCreation(StatesGroup):
    title_input = State()
    description_input = State()
    end_time_input = State()
    preview = State()


@router.message(StateFilter(TaskCreation), F.text == "❌ Отменить")
async def cancel_task_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание задачи отменено", reply_markup=ReplyKeyboardRemove())
    await cmd_profile(message)


@router.message(Command("create_task"))
async def cmd_create_task(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(TaskCreation.title_input)
    await message.answer("Вы начали создание задачи.\n\nВведите название задачи.", reply_markup=cancel_keyboard)


@router.callback_query(ItemCallback.filter(F.callback_action == "create_task"))
async def callback_create_task(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return
    await cmd_create_task(callback_query.message, state)
    # cmd_create_task очищает FSM/устанавливает состояние — устанавливаем created_for после этого
    try:
        created_for_id = int(callback_data.data)
    except Exception:
        created_for_id = callback_query.from_user.id
    await state.update_data(created_for=created_for_id)
    await callback_query.answer()


@router.message(TaskCreation.title_input)
async def input_task_title(message: Message, state: FSMContext):
    title_text = (message.text or "").strip()
    if not title_text:
        await message.answer("Название не может быть пустым. Введите название задачи:")
        return

    await state.update_data(title=title_text)
    await state.set_state(TaskCreation.description_input)

    data = await state.get_data()
    desc_data = data.get("description")
    if desc_data:
        keyboard = build_cancel_keyboard(desc_data)
        await message.answer("Введите описание задачи:", reply_markup=keyboard)
    else:
        await message.answer("Введите описание задачи:", reply_markup=cancel_keyboard)


@router.message(TaskCreation.description_input)
async def input_task_description(message: Message, state: FSMContext):
    desc_text = (message.text or "").strip()
    if not desc_text:
        await message.answer("Описание не может быть пустым. Введите описание задачи:")
        return
    await state.update_data(description=desc_text)
    await state.set_state(TaskCreation.end_time_input)
    example_date = format_dt(local_now(), "%d.%m.%Y %H:%M")
    await message.answer(
        f"Введите дату и время дедлайна в формате:\n"
        f"\"дд.мм.гггг ЧЧ:ММ\" (Пример: {example_date}):",
        reply_markup=date_end_select
    )


@router.message(TaskCreation.end_time_input)
async def input_task_end(message: Message, state: FSMContext):
    end_text = (message.text or "").strip()
    parsed_end = try_parse_datetime(end_text)

    now_utc = local_now().replace(microsecond=0)
    if end_text == "🕑 Через 1 день":
        parsed_end = now_utc + timedelta(days=1)
    elif end_text == "🕑 Через 7 дней":
        parsed_end = now_utc + timedelta(days=7)
    elif end_text == "🕑 Через 14 дней":
        parsed_end = now_utc + timedelta(days=14)
    elif end_text == "🕑 Через 21 день":
        parsed_end = now_utc + timedelta(days=21)
    elif end_text == "🕑 Через 28 дней":
        parsed_end = now_utc + timedelta(days=28)

    example_date_str = format_dt(now_utc, "%d.%m.%Y %H:%M")
    if not parsed_end:
        await message.answer(
            f"Не удалось распознать дату. Используйте формат 'дд.мм.гггг ЧЧ:ММ' (Пример: {example_date_str}).\n"
            f"Попробуйте ещё раз:")
        return

    if isinstance(parsed_end, type(local_now())):
        parsed_end = parsed_end.replace(microsecond=0)

    if parsed_end <= now_utc:
        await message.answer("Дедлайн должен быть в будущем. Введите корректную дату и время дедлайна:")
        return

    await state.update_data(end_at=parsed_end)

    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    end_at = data.get("end_at")

    end_str = format_dt(end_at, "%d.%m.%Y %H:%M") if hasattr(end_at, "tzinfo") else str(end_at)

    preview_text = (
        f"📋 Название задачи: {title}\n\n"
        f"{description}\n\n"
        f"💼 Дедлайн задачи: {end_str}"
    )

    await message.answer("Предпросмотр задачи:")
    if data.get("editing_task_id"):
        await message.answer(preview_text, reply_markup=task_edit_keyboard)
    else:
        await message.answer(preview_text, reply_markup=task_creation_keyboard)
    await state.set_state(TaskCreation.preview)


@router.message(
    StateFilter(TaskCreation.preview),
    F.text.in_({"✅ Создать задачу", "💾 Сохранить изменения"})
)
async def preview_confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    end_at = data.get("end_at")
    editing_id = data.get("editing_task_id")

    creator_user_object = await get_user_by_tg_id(message.from_user.id)
    president_object = await get_president()

    if not title or not end_at:
        await message.answer("Нет данных. Начните заново.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    user_object = await get_user_by_tg_id(message.from_user.id)
    if not user_object:
        await message.answer("Не удалось получить данные пользователя. Попробуйте позже.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    compilation = {
        "title": title,
        "description": description,
        "created_by": user_object.id,
        "created_for": data.get("created_for", user_object.id),
        "created_at": local_now().replace(microsecond=0),
        "end_at": end_at,
    }

    if editing_id:
        # обновление существующей задачи
        updated_task = await update_task(editing_id, {"title": title, "description": description, "end_at": end_at})
        await state.clear()
        if not updated_task:
            await message.answer("Ошибка при обновлении задачи. Проверьте данные.", reply_markup=ReplyKeyboardRemove())
            return
        await message.answer("✅ Задача успешно обновлена!",
                             reply_markup=ReplyKeyboardRemove())
        return

    created_task = await create_task(compilation)
    await state.clear()

    if (not created_task or not getattr(created_task, "title", None) or
            not getattr(created_task, "end_at", None)):
        await message.answer("Ошибка при создании задачи. Проверьте введённые данные.",
                             reply_markup=ReplyKeyboardRemove())
        return

    if creator_user_object != user_object:
        notif_text = f"✏️ {user_object.user_desc} создал задачу."
        task_cb = ItemCallback(callback_action="task_info", data=str(getattr(created_task, "id"))).pack()
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Открыть задачу", callback_data=task_cb)]
        ])
        await send_notification_by_id(president_object.id, notif_text, reply_markup=markup)
    await message.answer(f"✅ Задача успешно создана!",
                         reply_markup=ReplyKeyboardRemove())


@router.message(StateFilter(TaskCreation.preview), F.text == "✏️ Изменить")
async def preview_edit(message: Message, state: FSMContext):
    await state.set_state(TaskCreation.title_input)
    data = await state.get_data()
    keyboard = build_cancel_keyboard(data.get("title"))
    await message.answer("Отправьте название задачи.", reply_markup=keyboard)

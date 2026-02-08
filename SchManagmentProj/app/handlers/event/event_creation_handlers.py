from datetime import timedelta

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.event_keyboards import *
from app.keyboards.keyboards import cancel_keyboard, build_cancel_keyboard

from app.handlers.profile_handlers import cmd_profile

from app.database.requests.user_requests import get_user_by_tg_id
from app.database.requests.event_requests import create_event, get_event_by_name, update_event
from app.utils import try_parse_datetime, local_now, format_dt

router = Router()


class EventCreation(StatesGroup):
    title_input = State()
    description_input = State()
    start_time_input = State()
    end_time_input = State()
    preview = State()
    awaiting_photo = State()


@router.message(StateFilter(EventCreation), F.text == "❌ Отменить")
async def cancel_event_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание события отменено", reply_markup=ReplyKeyboardRemove())
    await cmd_profile(message)


@router.message(Command("create_event"))
async def cmd_create_event(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(EventCreation.title_input)
    await message.answer("Вы начали создание события. \n\nВведите название события.", reply_markup=cancel_keyboard)


@router.callback_query(F.data == "create_event")
async def callback_create_event(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return
    await cmd_create_event(callback_query.message, state)
    await callback_query.answer()


@router.message(EventCreation.title_input)
async def input_event_title(message: Message, state: FSMContext):
    title_text = (message.text or "").strip()
    if not title_text:
        await message.answer("Название не может быть пустым. Введите название события:")
        return

    await state.update_data(title=title_text)
    await state.set_state(EventCreation.description_input)

    data = await state.get_data()
    desc_data = data.get("description")
    if desc_data:
        keyboard = build_cancel_keyboard(desc_data)
        await message.answer("Введите описание события:", reply_markup=keyboard)
    else:
        await message.answer("Введите описание события:", reply_markup=cancel_keyboard)


@router.message(EventCreation.description_input)
async def input_event_description(message: Message, state: FSMContext):
    desc_text = (message.text or "").strip()
    if not desc_text:
        await message.answer("Описание не может быть пустым. Введите Описание события:")
        return
    await state.update_data(description=desc_text)
    await state.set_state(EventCreation.start_time_input)
    example_date = format_dt(local_now(), "%d.%m.%Y %H:%M")
    await message.answer(
        f"Введите дату и время начала события в формате:\n"
        f"\"дд.мм.гггг ЧЧ:ММ\" (Пример: {example_date}):",
        reply_markup=date_start_select
    )


@router.message(EventCreation.start_time_input)
async def input_event_start(message: Message, state: FSMContext):
    start_text = (message.text or "").strip()
    example_date_str = format_dt(local_now(), "%d.%m.%Y %H:%M")
    parsed_start = try_parse_datetime(start_text)

    if start_text == "🕑 Текущая дата и время":
        parsed_start = local_now().replace(microsecond=0)

    if not parsed_start:
        await message.answer(
            f"Не удалось распознать дату. Используйте формат 'дд.мм.гггг ЧЧ:ММ' (Пример: {example_date_str}).\n"
            f"Попробуйте ещё раз:")
        return

    # Гарантируем, что в состоянии хранится datetime (без микросекунд)
    if isinstance(parsed_start, type(local_now())):
        parsed_start = parsed_start.replace(microsecond=0)

    await state.update_data(start_at=parsed_start)
    await state.set_state(EventCreation.end_time_input)
    await message.answer("Введите дату и время окончания события в том же формате:", reply_markup=date_end_select)


@router.message(EventCreation.end_time_input)
async def input_event_end(message: Message, state: FSMContext):
    end_text = (message.text or "").strip()
    parsed_end = try_parse_datetime(end_text)

    data = await state.get_data()
    start_date = data.get("start_at")
    # Быстрые кнопки
    if end_text == "🕑 Через 1 час":
        parsed_end = start_date + timedelta(hours=1)
    elif end_text == "🕑 Через 12 часов":
        parsed_end = start_date + timedelta(hours=12)
    elif end_text == "🕑 Через 1 день":
        parsed_end = start_date + timedelta(days=1)
    elif end_text == "🕑 Через 3 дня":
        parsed_end = start_date + timedelta(days=3)
    elif end_text == "🕑 Через 1 неделю":
        parsed_end = start_date + timedelta(weeks=1)

    example_date_str = format_dt(local_now().replace(microsecond=0), "%d.%m.%Y %H:%M")
    if not parsed_end:
        await message.answer(
            f"Не удалось распознать дату. Используйте формат 'дд.мм.гггг ЧЧ:ММ' (Пример: {example_date_str}).\n"
            f"Попробуйте ещё раз:")
        return

    if isinstance(parsed_end, type(local_now())):
        parsed_end = parsed_end.replace(microsecond=0)

    data = await state.get_data()
    start_at = data.get("start_at")
    if not start_at:
        await message.answer("В системе отсутствует дата начала. Начните создание заново.")
        await state.clear()
        return

    # Если start_at — строка (редкий случай), пробуем распарсить
    if isinstance(start_at, str):
        parsed_start_fallback = try_parse_datetime(start_at)
        if parsed_start_fallback:
            start_at = parsed_start_fallback.replace(microsecond=0)
        else:
            await message.answer("Некорректный формат даты начала в состоянии. Начните создание заново.")
            await state.clear()
            return

    if parsed_end <= start_at:
        await message.answer("Дата окончания должна быть позже даты начала. Введите корректную дату окончания:")
        return

    await state.update_data(end_at=parsed_end)

    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    start_at = data.get("start_at")

    start_str = format_dt(start_at, "%d.%m.%Y %H:%M") if isinstance(start_at, type(local_now())) or hasattr(start_at,
                                                                                                            "tzinfo") else str(
        start_at)
    end_str = format_dt(parsed_end, "%d.%m.%Y %H:%M") if isinstance(parsed_end, type(local_now())) or hasattr(
        parsed_end, "tzinfo") else str(parsed_end)

    await message.answer("Предпросмотр события:")

    preview_text = (
        f"📌 Название события: {title.capitalize()}\n\n"
        f"📃 Описание:\n{description.capitalize()}\n\n"
        f"⏰ Даты проведения:\n"
        f"🎉 Начало: {start_str}\n"
        f"⏱️ Окончание: {end_str}"
    )

    data = await state.get_data()
    image_file_id = data.get("image_file_id")

    if data.get("editing_event_id"):
        keyboard = event_edit_keyboard
    else:
        keyboard = event_creation_keyboard

    if image_file_id:
        await message.answer_photo(photo=image_file_id, caption=preview_text, reply_markup=keyboard)
    else:
        await message.answer(preview_text, reply_markup=keyboard)
    await state.set_state(EventCreation.preview)


@router.message(StateFilter(EventCreation.preview), F.text.in_({"✅ Создать событие", "💾 Сохранить изменения"}))
async def preview_confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    start_at = data.get("start_at")
    end_at = data.get("end_at")
    editing_id = data.get("editing_event_id")

    if not title or not start_at or not end_at:
        await message.answer("Нет данных для создания события. Начните создание заново.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    user_object = await get_user_by_tg_id(message.from_user.id)
    if not user_object:
        await message.answer("Не удалось получить данные пользователя. Попробуйте позже.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    if editing_id:
        # обновление существующего события
        updated_event = await update_event(editing_id, {
            "title": title,
            "description": description,
            "start_at": start_at,
            "end_at": end_at,
            "image_storage_key": data.get("image_file_id")
        })
        await state.clear()
        if not updated_event:
            await message.answer("Ошибка при обновлении события. Проверьте данные.", reply_markup=ReplyKeyboardRemove())
            return
        start_str = format_dt(updated_event.start_at, "%d.%m.%Y %H:%M")
        end_str = format_dt(updated_event.end_at, "%d.%m.%Y %H:%M")
        await message.answer(f"✅ Событие успешно обновлено!\nНачало: {start_str}\nОкончание: {end_str}",
                             reply_markup=ReplyKeyboardRemove())
        return

    compilation = {
        "title": title,
        "description": description,
        "created_by": user_object.id,
        "created_at": local_now().replace(microsecond=0),
        "start_at": start_at,
        "end_at": end_at,
        "image_storage_key": data.get("image_file_id"),
    }

    created_event = await create_event(compilation)
    await state.clear()

    if (not created_event or not getattr(created_event, "title", None) or
            not getattr(created_event, "start_at", None) or not getattr(created_event, "end_at", None)):
        await message.answer("Ошибка при создании события. Проверьте введённые данные.",
                             reply_markup=ReplyKeyboardRemove())
        return

    start_str = format_dt(created_event.start_at, "%d.%m.%Y %H:%M")
    end_str = format_dt(created_event.end_at, "%d.%m.%Y %H:%M")
    await message.answer(f"Событие '{created_event.title}' успешно создано.\nНачало: {start_str}\nОкончание: {end_str}",
                         reply_markup=ReplyKeyboardRemove())


@router.message(StateFilter(EventCreation.preview), F.text == "✏️ Изменить")
async def preview_edit(message: Message, state: FSMContext):
    await state.set_state(EventCreation.title_input)
    data = await state.get_data()
    keyboard = build_cancel_keyboard(data.get("title"))
    await message.answer("Отправьте исправленное название события.", reply_markup=keyboard)


@router.message(StateFilter(EventCreation.preview), F.text == "🖼️ Прикрепить фото")
async def preview_attach_photo(message: Message, state: FSMContext):
    await state.set_state(EventCreation.awaiting_photo)
    await message.answer(
        "Отправьте фото для события:",
        reply_markup=event_creation_keyboard)


@router.message(StateFilter(EventCreation.awaiting_photo), F.photo)
async def receive_event_photo(message: Message, state: FSMContext):
    photos = message.photo or []
    if not photos:
        await message.answer("Фото не обнаружено. Отправьте изображение в виде снимка/файла.")
        return
    file_id = photos[-1].file_id
    await state.update_data(image_file_id=file_id)

    data = await state.get_data()
    title = data.get("title", "")
    description = data.get("description", "")
    start_at = data.get("start_at")
    end_at = data.get("end_at")

    start_str = format_dt(start_at, "%d.%m.%Y %H:%M") if hasattr(start_at, "tzinfo") else str(start_at)
    end_str = format_dt(end_at, "%d.%m.%Y %H:%M") if hasattr(end_at, "tzinfo") else str(end_at)

    preview_text = (
        f"{title.capitalize()}\n\n"
        f"📌 Название события: {title.capitalize()}\n\n"
        f"📃 Описание:\n{description.capitalize()}\n\n"
        f"⏰ Даты проведения:\n"
        f"🎉 Начало: {start_str}\n"
        f"⏱️ Окончание: {end_str}"
    )

    await message.answer_photo(photo=file_id, caption=preview_text, reply_markup=event_creation_keyboard)
    await state.set_state(EventCreation.preview)

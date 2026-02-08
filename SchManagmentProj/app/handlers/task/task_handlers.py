from aiogram import Router, F
from aiogram.types import CallbackQuery, ReplyKeyboardRemove, Message

from app.database.models.user_models import ManagementType, UserRole
from app.database.requests.task_requests import *
from app.database.requests.user_requests import get_user_data
from app.handlers.profile_handlers import cmd_profile
from app.keyboards.keyboards import decline_keyboard, confirm_keyboard, build_cancel_keyboard, cancel_keyboard
from app.keyboards.task_keyboards import *
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from app.handlers.task.task_creation_handlers import TaskCreation
from app.handlers import ItemCallback

router = Router()


class CompleteTaskStates(StatesGroup):
    waiting_for_description = State()


class DeleteTaskStates(StatesGroup):
    waiting_for_confirmation = State()


@router.message(StateFilter(CompleteTaskStates), F.text == "❌ Отменить")
async def cancel_event_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Завершение задачи отменено", reply_markup=ReplyKeyboardRemove())
    await cmd_profile(message)


# ===== Menu
@router.callback_query(F.data == "task_menu")
async def callback_task_menu(callback_query: CallbackQuery):
    if not callback_query.message:
        await callback_query.answer()
        return

    user_object = await get_user_by_tg_id(callback_query.from_user.id)
    keyboard = build_task_menu_keyboard(user_object)

    await callback_query.message.edit_text(
        f"Меню задач:",
        reply_markup=keyboard
    )
    await callback_query.answer()


# callback action
@router.callback_query(ItemCallback.filter(F.callback_action == "task_planer"))
async def callback_task_planer(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    callback_user_object = await get_user_by_tg_id(callback_query.from_user.id)
    tasks = await get_user_active_tasks(int(callback_data.data))
    if callback_user_object.manager_role == ManagementType.president or callback_user_object.role in (
    UserRole.teacher, UserRole.admin):
        back_to = "task_tracker_menu"
    else:
        back_to = "task_menu"

    keyboard = build_task_planer_keyboard(tasks, int(callback_data.data), page=1, back_to=back_to)

    if callback_user_object.id == int(callback_data.data):
        await callback_query.message.edit_text(
            f"🗂 Меню планера задач:",
            reply_markup=keyboard
        )
    else:
        user_data = await get_user_data(int(callback_data.data))
        await callback_query.message.edit_text(
            f"🗂 Меню планера задач:\n\n"
            f"👤 {user_data.get('user_desc')}",
            reply_markup=keyboard
        )
    await callback_query.answer()


# callback action
@router.callback_query(ItemCallback.filter(F.callback_action == "completed_task_menu"))
async def callback_completed_task_menu(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    callback_user_object = await get_user_by_tg_id(callback_query.from_user.id)
    tasks = await get_user_completed_tasks(int(callback_data.data))
    keyboard = build_completed_task_keyboard(tasks, int(callback_data.data), page=1)

    if callback_user_object.id == int(callback_data.data):
        await callback_query.message.edit_text(
            f"🗃 Меню завершённых задач:",
            reply_markup=keyboard
        )
    else:
        user_data = await get_user_data(int(callback_data.data))
        await callback_query.message.edit_text(
            f"🗃 Меню завершённых задач:\n\n"
            f"👤 {user_data.get('user_desc')}",
            reply_markup=keyboard
        )
    await callback_query.answer()


@router.callback_query(F.data == "task_tracker_menu")
async def callback_task_tracker_menu(callback_query: CallbackQuery):
    if not callback_query.message:
        await callback_query.answer()
        return

    stats = await get_tasks_tracker_stats()

    text = (
        "📋 Меню трекинга задач:\n\n"
        "<blockquote>"
        "Данные о задачах:\n\n"
        f"├ Всего задач поставлено: {stats['total']}\n"
        f"├ Всего задач завершено: {stats['completed']}\n"
        "│\n"
        f"├ Задач поставлено за месяц: {stats['month_total']}\n"
        f"├ Задач завершено за месяц: {stats['month_completed']}\n"
        "</blockquote>"
    )

    manager_objects = await get_existing_managers()
    keyboard = build_task_tracker_menu_keyboard(manager_objects)

    await callback_query.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()


# Task panels and pages
@router.callback_query(ItemCallback.filter(F.callback_action == "task_info"))
async def callback_task_info(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    try:
        task_id = int(callback_data.data)
    except Exception:
        await callback_query.answer("Некорректный идентификатор задачи", show_alert=True)
        return

    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.answer("Задача не найдена", show_alert=True)
        return

    if not task.is_completed:
        keyboard = build_task_info_keyboard(task, task.created_for)
    else:
        keyboard = build_completed_task_info_keyboard(task, task.created_for)

    end_at_formatted = task.end_at.strftime("%d.%m.%Y %H:%M")
    created_at_formatted = task.created_at.strftime("%d.%m.%Y %H:%M")

    def _plural_days(n: int) -> str:
        n = abs(n) % 100
        if 11 <= n <= 19:
            return "дней"
        i = n % 10
        if i == 1:
            return "день"
        if 2 <= i <= 4:
            return "дня"
        return "дней"

    today = datetime.now().date()
    # Расчёты по датам (чтобы избежать проблем с часовыми поясами)
    try:
        created_date = task.created_at.date()
    except Exception:
        created_date = task.created_at  # fallback если объект уже date
    try:
        end_date = task.end_at.date()
    except Exception:
        end_date = task.end_at

    days_passed = (today - created_date).days
    days_left = (end_date - today).days

    # Формируем текст сообщения
    text = (
        f"📋 Название задачи: {task.title}\n\n"
        f"{task.description or 'Без описания'}\n\n"
        f"🕑 Задача создана: {created_at_formatted}\n"
        f"⏳ Прошло дней с начала: {days_passed}\n\n"
        f"💼 Дедлайн задачи: {end_at_formatted}\n"
    )

    if not task.is_completed:
        if days_left < 0:
            text += f"⛔ Дедлайн прошёл: {end_at_formatted}\n"
        elif days_left == 0:
            text += "‼️ Конец дедлайна: СЕГОДНЯ\n"
        elif 1 <= days_left <= 3:
            text += f"❗️ Конец дедлайна через: {days_left} {_plural_days(days_left)}\n"
        else:  # days_left >= 4
            text += f"📌 Конец дедлайна через: {days_left} {_plural_days(days_left)}\n"
    else:
        # Для завершённой задачи добавляем информацию о времени завершения
        if task.completed_at:
            completed_at_formatted = task.completed_at.strftime("%d.%m.%Y %H:%M")
            if task.completed_at <= task.end_at:
                text += f"\n✅ Задача завершена вовремя: {completed_at_formatted}\n"
            else:
                text += f"\n❌ Задача завершена не вовремя: {completed_at_formatted}\n"

        # Если есть описание завершения — показываем
        if getattr(task, "complete_desc", None):
            text += f"\n📝 Описание завершения:\n{task.complete_desc}\n"

    await callback_query.message.edit_text(
        text=text,
        reply_markup=keyboard
    )
    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "task_planer_page"))
async def callback_task_planer_page(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    data = callback_data.data.split()
    try:
        page = int(data[1])
    except Exception:
        page = 1

    callback_user_object = await get_user_by_tg_id(callback_query.from_user.id)
    tasks = await get_user_active_tasks(int(data[0]))

    if callback_user_object.manager_role == ManagementType.president or callback_user_object.role in (
    UserRole.teacher, UserRole.admin):
        back_to = "task_tracker_menu"
    else:
        back_to = "task_menu"

    keyboard = build_task_planer_keyboard(tasks, int(data[0]), page=page, back_to=back_to)

    if callback_user_object.id == int(data[0]):
        await callback_query.message.edit_text(
            f"🗂 Меню планера задач:",
            reply_markup=keyboard
        )
    else:
        user_data = await get_user_data(int(data[0]))
        await callback_query.message.edit_text(
            f"🗂 Меню планера задач:\n\n"
            f"👤 {user_data.get('user_desc')}",
            reply_markup=keyboard
        )
    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "completed_task_page"))
async def callback_completed_task_page(callback_query: CallbackQuery, callback_data: ItemCallback):
    if not callback_query.message:
        await callback_query.answer()
        return

    try:
        page = int(callback_data.data)
    except Exception:
        page = 1

    tasks = await get_user_completed_tasks(callback_query.from_user.id)
    keyboard = build_completed_task_keyboard(tasks, page=page)

    await callback_query.message.edit_text(
        f"🗃 Меню завершённых задач:",
        reply_markup=keyboard
    )
    await callback_query.answer()


# Task actions
@router.callback_query(ItemCallback.filter(F.callback_action == "complete_task"))
async def callback_complete_task(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    data = callback_data.data
    task_id = int(data)

    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.answer("❌ Задача не найдена", show_alert=True)
        return

    await state.update_data(task_id=task_id)
    await state.set_state(CompleteTaskStates.waiting_for_description)

    await callback_query.message.answer(
        text=f'📝 Вы собираетесь завершить задачу "{task.title}". Для этого введите описание завершения задачи, где вы подведёте итоги к завершению этой задачи:',
        reply_markup=decline_keyboard
    )

    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "task_delete"))
async def callback_task_delete(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    try:
        task_id = int(callback_data.data)
    except Exception:
        await callback_query.answer("❌ Некорректный идентификатор задачи", show_alert=True)
        return

    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.answer("🚫 Задача не найдена", show_alert=True)
        return

    await state.update_data(pending_delete_task_id=task_id)
    await state.set_state(DeleteTaskStates.waiting_for_confirmation)

    await callback_query.message.answer(
        "Вы действительно хотите удалить задачу?",
        reply_markup=confirm_keyboard
    )

    await callback_query.answer()


@router.callback_query(ItemCallback.filter(F.callback_action == "edit_task"))
async def callback_edit_task(callback_query: CallbackQuery, callback_data: ItemCallback, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    try:
        task_id = int(callback_data.data)
    except Exception:
        await callback_query.answer("Некорректный идентификатор задачи", show_alert=True)
        return

    task = await get_task_by_id(task_id)
    if not task:
        await callback_query.answer("Задача не найдена", show_alert=True)
        return

    # Инициализируем FSM данными задачи
    await state.clear()
    await state.update_data(title=task.title, description=task.description or "", end_at=task.end_at,
                            editing_task_id=task.id)
    await state.set_state(TaskCreation.title_input)

    keyboard = build_cancel_keyboard(task.title)
    await callback_query.message.answer("Вы начали редактирование задачи.\n\nОтправьте исправленное название задачи.",
                                        reply_markup=keyboard)
    await callback_query.answer()


# Handle action confirm
@router.message(StateFilter(CompleteTaskStates.waiting_for_description))
async def handle_complete_description(message: Message, state: FSMContext):
    if message.text == "❌ Отменить":
        await message.answer("❌ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    description = (message.text or "").strip()
    if not description:
        await message.answer("Описание не может быть пустым.")
        return

    data = await state.get_data()
    task_id = data.get("task_id")

    if not task_id:
        await message.answer("❌ Ошибка состояния.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    task = await set_task_completed(task_id)
    if not task:
        await message.answer("❌ Задача не найдена или уже завершена.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await update_task_complete_desc(task_id, description)
    await message.answer("✅ Задача успешно завершена.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(StateFilter(DeleteTaskStates.waiting_for_confirmation))
async def confirm_delete_task(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    data = await state.get_data()
    task_id = data.get("pending_delete_task_id")

    if not task_id:
        await message.answer("Нет данных о задаче. Отмена.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    print(text)
    if text == "✅ Подтвердить":
        deleted_by = message.from_user.id if message.from_user else None
        deleted_task = await soft_delete_task(task_id, deleted_by)
        if deleted_task:
            await message.answer("Задача успешно удалена.", reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("Задача не найдена или уже удалена.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return
    elif text == "❌ Отменить":
        await message.answer("Удаление отменено.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    await message.answer('Пожалуйста, дайте ответ через кнопку "✅ Подтвердить" или "❌ Отменить"')

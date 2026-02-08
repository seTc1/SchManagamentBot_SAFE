from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError

from app.keyboards.announcement_keyboards import announcement_menu, announcement_preview_kb
from app.keyboards.keyboards import cancel_keyboard
from app.database.requests.user_requests import get_users_for_announce
from app.handlers.profile_handlers import cmd_profile

router = Router()


class AnnouncementCreation(StatesGroup):
    waiting_for_content = State()
    preview = State()


@router.callback_query(F.data == "announcement_menu")
async def callback_announcement_menu(callback_query: CallbackQuery):
    if not callback_query.message:
        await callback_query.answer()
        return
    await callback_query.message.edit_text(
        f"Меню создания объявлений:",
        reply_markup=announcement_menu
    )
    await callback_query.answer()


@router.callback_query(F.data == "send_all_announce")
async def callback_send_all_announcement(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.message:
        await callback_query.answer()
        return

    await state.set_state(AnnouncementCreation.waiting_for_content)
    await callback_query.answer()
    await callback_query.message.answer(
        "Напишите текст объявления. Можно прикрепить фото.",
        reply_markup=cancel_keyboard
    )


@router.message(StateFilter(AnnouncementCreation), F.text == "❌ Отменить")
async def cancel_code_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание объявления отменено.", reply_markup=ReplyKeyboardRemove())
    await cmd_profile(message)


@router.message(StateFilter(AnnouncementCreation.waiting_for_content))
async def receive_announcement_content(message: Message, state: FSMContext):
    # Сохраняем идентификаторы сообщения для копирования
    await state.update_data(
        announcement_from_chat_id=message.chat.id,
        announcement_message_id=message.message_id
    )

    # Копируем само сообщение (1 в 1) назад автору
    try:
        await message.copy_to(chat_id=message.chat.id)
    except Exception:
        # На всякий случай — если copy не сработал, отправим простую ссылку/текст
        await state.clear()
        await message.answer("Не удалось точно скопировать сообщение для предпросмотра. Проверьте содержимое.",
                             reply_markup=ReplyKeyboardRemove())

    # Показываем inline-кнопки для подтверждения/редактирования/отмены
    await message.answer(
        "Вот так пользователи увидят ваше объявление. Подтвердите отправку или отредактируйте объявление.",
        reply_markup=announcement_preview_kb)
    await state.set_state(AnnouncementCreation.preview)


@router.message(StateFilter(AnnouncementCreation.preview), F.text == "✏️ Изменить")
async def announce_edit(message: Message, state: FSMContext):
    await state.set_state(AnnouncementCreation.waiting_for_content)
    if message:
        await message.answer("Отправьте исправленное объявление.",
                                            reply_markup=cancel_keyboard)


@router.message(StateFilter(AnnouncementCreation.preview), F.text == "✅ Отправить")
async def announce_send(message: Message, state: FSMContext):
    data = await state.get_data()
    from_chat_id = data.get("announcement_from_chat_id")
    message_id = data.get("announcement_message_id")

    if not from_chat_id or not message_id:
        await message.answer("Нет данных для отправки объявления. Попробуйте заново.",
                                            reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Получаем список всех пользователей
    user_ids = await get_users_for_announce()
    if not user_ids:
        await message.answer(
            "В базе нет пользователей для рассылки. (как вообще возможно получить эту ошибку лол)",
            reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    bot = message.bot
    sent_count = 0
    failed = []

    # Рассылка с простой обработкой RetryAfter
    for tg_id in user_ids:
        try:
            # Копируем сообщение (сохраняет тип/медиа/подписи)
            await bot.copy_message(chat_id=tg_id, from_chat_id=from_chat_id, message_id=message_id)
            sent_count += 1
        except TelegramRetryAfter as e:
            # Если получили лимит, ждём и повторяем попытку
            wait_for = getattr(e, "retry_after", None) or 1
            await asyncio.sleep(wait_for)
            try:
                await bot.copy_message(chat_id=tg_id, from_chat_id=from_chat_id, message_id=message_id)
                sent_count += 1
            except Exception as ex:
                failed.append((tg_id, str(ex)))
        except TelegramAPIError as e:
            # Любая ошибка API — сохраняем для отчёта
            failed.append((tg_id, str(e)))
        except Exception as e:
            failed.append((tg_id, str(e)))

        # Небольшая пауза, чтобы снизить риск достижения лимитов
        await asyncio.sleep(0.05)

    # Отчёт автору
    total = len(user_ids)
    failed_count = len(failed)
    success_count = sent_count

    report_lines = [
        f"Рассылка завершена.",
        f"Всего пользователей в базе: {total}",
        f"Отправлено успешно: {success_count}",
        f"Не доставлено: {failed_count}",
    ]
    if failed_count > 0:
        # Покажем первые 10 ошибок для удобства
        preview_failures = failed[:10]
        report_lines.append("Примеры ошибок (tg_id: ошибка):")
        for uid, err in preview_failures:
            report_lines.append(f"{uid}: {err}")

    await message.answer("\n".join(report_lines), reply_markup=ReplyKeyboardRemove())
    await state.clear()

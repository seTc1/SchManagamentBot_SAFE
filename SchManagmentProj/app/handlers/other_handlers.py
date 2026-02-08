from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.handlers import ItemCallback
from app.keyboards.keyboards import not_founded

router = Router()


@router.callback_query(F.data == "pages_count")
async def create_profile(callback: CallbackQuery):
    await callback.answer("Кол-во страниц", show_alert=False)


@router.message(Command("test"))
async def cmd_info(message: Message):
    from app.utils.notif_sender import send_notification_by_id
    from app.database.requests.user_requests import get_user_by_tg_id
    user_object = await get_user_by_tg_id(message.chat.id)
    await send_notification_by_id(user_object.id, "привет чувак")


@router.message(Command("send"))
async def cmd_send(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /send <tg_id> <сообщение>")
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("tg_id должен быть числом")
        return
    text_to_send = parts[2].strip()
    try:
        await message.bot.send_message(target_id, text_to_send)
    except Exception as exc:
        await message.answer(f"Ошибка при отправке: {exc}")
    else:
        await message.answer("Сообщение отправлено.")


@router.callback_query(F.data == "just_answer_callback")
async def blank_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "blank_callback")
async def blank_callback(callback: CallbackQuery):
    print("Инициация 'blank_callback'")
    print(callback)
    await callback.message.answer_photo(
        "AgACAgIAAxkBAAIJTmke8ZZ_SovbpvIpMzMH1hDMHnV0AAJ3DWsbPff4SKUis7K1B5m2AQADAgADeQADNgQ",
        caption="Эта функция ещё не реализована. Попробуйте позже.",
        reply_markup=not_founded)
    await callback.answer()

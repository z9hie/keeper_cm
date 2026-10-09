import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import init_db, save_user, get_user

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Я KeeperCM — хранитель чата.\n"
        "Пока я маленький, но скоро научусь многому."
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 **Команды KeeperCM:**\n\n"
        "/start — приветствие\n"
        "/help — это сообщение\n"
        "/ping — проверить скорость\n"
        "/id — узнать свой ID и ID чата\n"
        "/info — инфа о тебе\n"
        "/me — твоя статистика",
        parse_mode="Markdown"
    )

async def main():
    await init_db()          # ← новая строка
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

@router.message(Command("ping"))
async def cmd_ping(message: Message):
    start = time.perf_counter()
    sent = await message.answer("🏓 Pong...")
    elapsed = (time.perf_counter() - start) * 1000
    await sent.edit_text(f"🏓 Pong! `{elapsed:.0f} ms`", parse_mode="Markdown")


@router.message(Command("id"))
async def cmd_id(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    await message.answer(
        f"👤 Твой ID: `{user_id}`\n"
        f"💬 ID чата: `{chat_id}`",
        parse_mode="Markdown"
    )


@router.message(Command("info"))
async def cmd_info(message: Message):
    u = message.from_user
    text = (
        f"👤 Имя: {u.full_name}\n"
        f"🔗 Username: @{u.username}" if u.username else f"👤 Имя: {u.full_name}\n🔗 Username: нет\n"
    )
    # не запутайся с f-string выше — если что упростим
    text = f"👤 Имя: {u.full_name}\n"
    text += f"🔗 Username: @{u.username}\n" if u.username else "🔗 Username: нет\n"
    text += f"🆔 ID: `{u.id}`\n"
    text += f"🌐 Язык: {u.language_code}\n"
    text += f"⭐ Premium: {'да' if u.is_premium else 'нет'}\n"
    text += f"🤖 Бот: {'да' if u.is_bot else 'нет'}"
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("me"))
async def cmd_me(message: Message):
    user = await get_user(message.from_user.id)
    if user is None:
        await message.answer("Я тебя ещё не знаю. Напиши что-нибудь!")
        return

    first_seen = user["first_seen"][:10]  # только дата
    text = (
        f"📊 **Твоя статистика**\n\n"
        f"👤 {user['first_name']}\n"
        f"🆔 `{user['user_id']}`\n"
        f"💬 Сообщений: **{user['message_count']}**\n"
        f"📅 Первое сообщение: {first_seen}"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message()
async def track_user(message: Message):
    """Ловит любое сообщение и сохраняет юзера."""
    if message.from_user is None:
        return
    if message.from_user.is_bot:
        return  # ботов не считаем

    await save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

if __name__ == "__main__":
    asyncio.run(main())
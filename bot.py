import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message

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
        "/info — инфа о тебе",
        parse_mode="Markdown"
    )

async def main():
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

if __name__ == "__main__":
    asyncio.run(main())
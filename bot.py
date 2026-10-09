import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from filters import IsModerator, IsAdmin
from database import init_db, save_user, get_user
from database import save_chat, set_role, remove_role, get_role, get_chat_roles

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
        "/setrole — установить роль\n"
        "/unsetrole — снять роль\n"
        "/roles — просмотр ролей\n"
        "/myrole — посмотреть свою роль",
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

@router.message(Command("setrole"), IsAdmin())
async def cmd_setrole(message: Message):
    if message.reply_to_message is None:
        await message.answer("Ответь на сообщение юзера, которому даёшь роль.")
        return

    # парсим аргумент: /setrole moderator
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: `/setrole moderator` (в reply)", parse_mode="Markdown")
        return

    role = parts[1].strip().lower()
    if role not in ("moderator", "admin"):
        await message.answer("Роль может быть: `moderator` или `admin`", parse_mode="Markdown")
        return

    target = message.reply_to_message.from_user
    if target.is_bot:
        await message.answer("Ботам роли не выдаём.")
        return

    await set_role(message.chat.id, target.id, role, message.from_user.id)
    await message.answer(f"✅ {target.full_name} теперь **{role}**", parse_mode="Markdown")


@router.message(Command("unsetrole"), IsAdmin())
async def cmd_unsetrole(message: Message):
    if message.reply_to_message is None:
        await message.answer("Ответь на сообщение юзера.")
        return

    target = message.reply_to_message.from_user
    await remove_role(message.chat.id, target.id)
    await message.answer(f"✅ Роль снята с {target.full_name}")


@router.message(Command("roles"))
async def cmd_roles(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("Команда только для групп.")
        return

    roles = await get_chat_roles(message.chat.id)
    if not roles:
        await message.answer("В этом чате нет назначенных ролей.")
        return

    text = "👥 **Роли в чате:**\n\n"
    for r in roles:
        name = r["first_name"] or "Без имени"
        username = f" (@{r['username']})" if r["username"] else ""
        emoji = "🛡" if r["role"] == "admin" else "⚔️"
        text += f"{emoji} {name}{username} — {r['role']}\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("myrole"))
async def cmd_myrole(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("Команда только для групп.")
        return

    role = await get_role(message.chat.id, message.from_user.id)
    if role is None:
        role = "user (по умолчанию)"
    await message.answer(f"Твоя роль здесь: **{role}**", parse_mode="Markdown")

@router.message()
async def track_user(message: Message):
    if message.from_user is None or message.from_user.is_bot:
        return

    await save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    # сохраняем чат если это группа/супергруппа
    if message.chat.type in ("group", "supergroup"):
        await save_chat(message.chat.id, message.chat.title or "Без названия")

if __name__ == "__main__":
    asyncio.run(main())
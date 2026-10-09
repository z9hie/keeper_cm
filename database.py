import aiosqlite
from datetime import datetime

DB_PATH = "keeper.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                first_seen TEXT,
                last_seen TEXT,
                message_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def save_user(user_id: int, username: str | None, first_name: str):
    """Создаёт юзера если нет, обновляет last_seen и +1 к счётчику."""
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        # проверяем есть ли юзер
        async with db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            exists = await cursor.fetchone()

        if exists:
            await db.execute(
                """UPDATE users
                   SET username = ?, first_name = ?, last_seen = ?,
                       message_count = message_count + 1
                   WHERE user_id = ?""",
                (username, first_name, now, user_id),
            )
        else:
            await db.execute(
                """INSERT INTO users
                   (user_id, username, first_name, first_seen, last_seen, message_count)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (user_id, username, first_name, now, now),
            )
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()
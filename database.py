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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                added_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                chat_id INTEGER,
                user_id INTEGER,
                role TEXT,
                assigned_by INTEGER,
                assigned_at TEXT,
                PRIMARY KEY (chat_id, user_id)
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

async def save_chat(chat_id: int, title: str):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO chats (chat_id, title, added_at)
               VALUES (?, ?, ?)""",
            (chat_id, title, now),
        )
        # обновляем title если сменился
        await db.execute(
            "UPDATE chats SET title = ? WHERE chat_id = ?",
            (title, chat_id),
        )
        await db.commit()


async def set_role(chat_id: int, user_id: int, role: str, assigned_by: int):
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO roles
               (chat_id, user_id, role, assigned_by, assigned_at)
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, user_id, role, assigned_by, now),
        )
        await db.commit()


async def remove_role(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM roles WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        await db.commit()


async def get_role(chat_id: int, user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role FROM roles WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_chat_roles(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT r.*, u.first_name, u.username
               FROM roles r
               LEFT JOIN users u ON u.user_id = r.user_id
               WHERE r.chat_id = ?
               ORDER BY r.role""",
            (chat_id,),
        ) as cursor:
            return await cursor.fetchall()
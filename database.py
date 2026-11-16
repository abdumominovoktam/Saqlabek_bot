import json
import logging
import time
from typing import Any
import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """aiosqlite orqali asinxron ma'lumotlar bazasi boshqaruvi."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Jadvallar va indekslarni yaratish."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")

            # 1. Akkaunt ulanishlari jadvali (business_connection)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    business_connection_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    user_chat_id INTEGER NOT NULL,
                    is_enabled INTEGER NOT NULL DEFAULT 1,
                    can_reply INTEGER NOT NULL DEFAULT 0,
                    can_read_messages INTEGER NOT NULL DEFAULT 1,
                    rights_json TEXT,
                    updated_at INTEGER NOT NULL
                );
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_connections_user_id
                ON connections(user_id);
            """)

            # 2. Xabarlar kesh jadvali (business_message)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_connection_id TEXT NOT NULL,
                    chat_id INTEGER NOT NULL,
                    chat_title TEXT,
                    chat_username TEXT,
                    message_id INTEGER NOT NULL,
                    sender_id INTEGER,
                    sender_name TEXT,
                    sender_username TEXT,
                    is_outgoing INTEGER NOT NULL DEFAULT 0,
                    content_type TEXT NOT NULL,
                    text TEXT,
                    file_id TEXT,
                    file_unique_id TEXT,
                    has_protected_content INTEGER NOT NULL DEFAULT 0,
                    sent_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    UNIQUE(business_connection_id, chat_id, message_id)
                );
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_lookup
                ON messages(business_connection_id, chat_id, message_id);
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_sent_at
                ON messages(sent_at);
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_chat_id
                ON messages(chat_id);
            """)
            await db.commit()
            logger.info("Ma'lumotlar bazasi jadvallari va indekslari muvaffaqiyatli ishga tushirildi.")

    async def save_or_update_connection(
        self,
        business_connection_id: str,
        user_id: int,
        user_chat_id: int,
        is_enabled: bool,
        can_reply: bool,
        can_read_messages: bool,
        rights_json: str | None = None
    ) -> None:
        """Ulanish holatini bazaga yozish yoki yangilash."""
        now = int(time.time())
        query = """
            INSERT INTO connections (
                business_connection_id,
                user_id,
                user_chat_id,
                is_enabled,
                can_reply,
                can_read_messages,
                rights_json,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(business_connection_id) DO UPDATE SET
                user_id = excluded.user_id,
                user_chat_id = excluded.user_chat_id,
                is_enabled = excluded.is_enabled,
                can_reply = excluded.can_reply,
                can_read_messages = excluded.can_read_messages,
                rights_json = excluded.rights_json,
                updated_at = excluded.updated_at;
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                query,
                (
                    business_connection_id,
                    user_id,
                    user_chat_id,
                    1 if is_enabled else 0,
                    1 if can_reply else 0,
                    1 if can_read_messages else 0,
                    rights_json,
                    now,
                ),
            )
            await db.commit()

    async def disable_connection(self, business_connection_id: str) -> None:
        """Ulanish uzilganda uni nofaol holatga keltirish."""
        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE connections SET is_enabled = 0, updated_at = ? WHERE business_connection_id = ?",
                (now, business_connection_id),
            )
            await db.commit()

    async def get_connection(self, business_connection_id: str) -> dict[str, Any] | None:
        """Ulanish ID bo'yicha ma'lumot olish."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM connections WHERE business_connection_id = ? LIMIT 1",
                (business_connection_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_active_connection_by_user(self, user_id: int) -> dict[str, Any] | None:
        """Foydalanuvchining faol ulanishini topish."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM connections WHERE user_id = ? AND is_enabled = 1 ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_latest_connection_by_user(self, user_id: int) -> dict[str, Any] | None:
        """Foydalanuvchining eng oxirgi ulanishini topish (faol yoki nofaol)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM connections WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (user_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def save_message(
        self,
        business_connection_id: str,
        chat_id: int,
        chat_title: str | None,
        chat_username: str | None,
        message_id: int,
        sender_id: int | None,
        sender_name: str | None,
        sender_username: str | None,
        is_outgoing: bool,
        content_type: str,
        text: str | None,
        file_id: str | None,
        file_unique_id: str | None,
        has_protected_content: bool,
        sent_at: int
    ) -> None:
        """Xabarni keshga yozish yoki yangilash."""
        now = int(time.time())
        query = """
            INSERT INTO messages (
                business_connection_id,
                chat_id,
                chat_title,
                chat_username,
                message_id,
                sender_id,
                sender_name,
                sender_username,
                is_outgoing,
                content_type,
                text,
                file_id,
                file_unique_id,
                has_protected_content,
                sent_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(business_connection_id, chat_id, message_id) DO UPDATE SET
                chat_title = excluded.chat_title,
                chat_username = excluded.chat_username,
                sender_name = excluded.sender_name,
                sender_username = excluded.sender_username,
                content_type = excluded.content_type,
                text = excluded.text,
                file_id = excluded.file_id,
                file_unique_id = excluded.file_unique_id,
                has_protected_content = excluded.has_protected_content,
                sent_at = excluded.sent_at;
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                query,
                (
                    business_connection_id,
                    chat_id,
                    chat_title,
                    chat_username,
                    message_id,
                    sender_id,
                    sender_name,
                    sender_username,
                    1 if is_outgoing else 0,
                    content_type,
                    text,
                    file_id,
                    file_unique_id,
                    1 if has_protected_content else 0,
                    sent_at,
                    now,
                ),
            )
            await db.commit()

    async def get_message(
        self,
        business_connection_id: str,
        chat_id: int,
        message_id: int
    ) -> dict[str, Any] | None:
        """Muayyan xabarni olish."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM messages
                WHERE business_connection_id = ? AND chat_id = ? AND message_id = ?
                LIMIT 1
                """,
                (business_connection_id, chat_id, message_id),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_messages_by_ids(
        self,
        business_connection_id: str,
        chat_id: int,
        message_ids: list[int]
    ) -> list[dict[str, Any]]:
        """O'chirilgan xabarlarni xronologik tartibda olish."""
        if not message_ids:
            return []
        placeholders = ",".join("?" for _ in message_ids)
        query = f"""
            SELECT * FROM messages
            WHERE business_connection_id = ? AND chat_id = ? AND message_id IN ({placeholders})
            ORDER BY sent_at ASC, message_id ASC
        """
        params = [business_connection_id, chat_id, *message_ids]
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_message_text(
        self,
        business_connection_id: str,
        chat_id: int,
        message_id: int,
        new_text: str | None
    ) -> None:
        """Tahrirlangan xabar matnini yangilash."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE messages
                SET text = ?
                WHERE business_connection_id = ? AND chat_id = ? AND message_id = ?
                """,
                (new_text, business_connection_id, chat_id, message_id),
            )
            await db.commit()

    async def get_message_count_for_user(self, user_id: int) -> int:
        """Foydalanuvchi akkauntiga tegishli jami keshlangan xabarlar soni."""
        query = """
            SELECT COUNT(*) FROM messages m
            INNER JOIN connections c ON m.business_connection_id = c.business_connection_id
            WHERE c.user_id = ?
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def delete_old_messages(self, retention_days: int) -> int:
        """Belgilangan kunlardan eski xabarlarni o'chirish (tozalash)."""
        cutoff_time = int(time.time()) - (retention_days * 86400)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM messages WHERE sent_at < ?",
                (cutoff_time,),
            )
            deleted_count = cursor.rowcount
            await db.commit()
            if deleted_count > 0:
                logger.info(f"Avtomatik tozalash: {deleted_count} ta eski xabar bazadan o'chirildi.")
            return deleted_count

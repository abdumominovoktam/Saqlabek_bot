import asyncio
import os
import sys
from pathlib import Path
import time
from datetime import datetime, timezone

# Loyiha ildiz katalogini sys.path ga qo'shish
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Chat,
    Message,
    PhotoSize,
    User,
    Video,
    Voice,
    VideoNote,
    BusinessConnection,
    BusinessBotRights,
    BusinessMessagesDeleted,
)

from config import Config
from database import Database
from handlers.business import business_router
from handlers.user import user_router
from utils.formatter import (
    format_chat_label,
    format_deleted_message,
    format_edited_message,
    format_timestamp,
    format_user_label,
    format_view_once_media,
)
from utils.media import extract_media_info


async def run_tests():
    print("================== TEST BOSHLANDI ==================")
    test_db_path = "test_saqlabek.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # 1. Database testlari
    db = Database(test_db_path)
    await db.init_db()
    print("✅ DB init_db muvaffaqiyatli")

    # Connection saqlash
    await db.save_or_update_connection(
        business_connection_id="conn_123",
        user_id=111,
        user_chat_id=111,
        is_enabled=True,
        can_reply=True,
        can_read_messages=True,
        rights_json='{"can_read_messages": true}'
    )
    conn = await db.get_connection("conn_123")
    assert conn is not None
    assert conn["user_id"] == 111
    assert conn["is_enabled"] == 1
    assert conn["can_read_messages"] == 1
    print("✅ DB save_or_update_connection va get_connection muvaffaqiyatli")

    active_conn = await db.get_active_connection_by_user(111)
    assert active_conn is not None
    assert active_conn["business_connection_id"] == "conn_123"
    print("✅ DB get_active_connection_by_user muvaffaqiyatli")

    # Xabar saqlash
    now_ts = int(time.time())
    await db.save_message(
        business_connection_id="conn_123",
        chat_id=222,
        chat_title="Ali Do'stim",
        chat_username="ali_dev",
        message_id=501,
        sender_id=222,
        sender_name="Ali Valiyev",
        sender_username="ali_dev",
        is_outgoing=False,
        content_type="text",
        text="Salom, bu sinov xabari!",
        file_id=None,
        file_unique_id=None,
        has_protected_content=False,
        sent_at=now_ts
    )

    msg = await db.get_message("conn_123", 222, 501)
    assert msg is not None
    assert msg["text"] == "Salom, bu sinov xabari!"
    assert msg["sender_name"] == "Ali Valiyev"
    print("✅ DB save_message va get_message muvaffaqiyatli")

    # Tahrirlash testi
    await db.update_message_text("conn_123", 222, 501, "Salom, yangilangan xabar!")
    msg_edited = await db.get_message("conn_123", 222, 501)
    assert msg_edited["text"] == "Salom, yangilangan xabar!"
    print("✅ DB update_message_text muvaffaqiyatli")

    # O'chirilgan xabarlarni xronologik olish
    await db.save_message(
        business_connection_id="conn_123",
        chat_id=222,
        chat_title="Ali Do'stim",
        chat_username="ali_dev",
        message_id=502,
        sender_id=222,
        sender_name="Ali Valiyev",
        sender_username="ali_dev",
        is_outgoing=False,
        content_type="photo",
        text="Mana bu rasm!",
        file_id="photo_file_id_xyz",
        file_unique_id="unique_123",
        has_protected_content=True,
        sent_at=now_ts + 10
    )

    del_msgs = await db.get_messages_by_ids("conn_123", 222, [502, 501])
    assert len(del_msgs) == 2
    assert del_msgs[0]["message_id"] == 501  # Xronologik oldinroq
    assert del_msgs[1]["message_id"] == 502
    print("✅ DB get_messages_by_ids (xronologik tartib) muvaffaqiyatli")

    total_count = await db.get_message_count_for_user(111)
    assert total_count == 2
    print(f"✅ DB get_message_count_for_user ({total_count} ta) muvaffaqiyatli")

    # Ulanishni uzish
    await db.disable_connection("conn_123")
    conn_disabled = await db.get_connection("conn_123")
    assert conn_disabled["is_enabled"] == 0
    active_after = await db.get_active_connection_by_user(111)
    assert active_after is None
    print("✅ DB disable_connection muvaffaqiyatli")

    # 2. Formatter testlari
    dt_str = format_timestamp(now_ts)
    assert "." in dt_str and ":" in dt_str
    print(f"✅ Formatter format_timestamp: {dt_str}")

    u_label = format_user_label("Sherzod", "sher_dev")
    assert u_label == "Sherzod (@sher_dev)"

    v_text = format_view_once_media(
        sender_name="Sherzod",
        sender_username="sher_dev",
        sent_at=now_ts,
        media_type="Rasm (Photo)",
        caption="Maxfiy rasm"
    )
    assert "Vaqtinchalik media saqlandi" in v_text
    assert "Sherzod" in v_text
    print("✅ Formatter format_view_once_media muvaffaqiyatli")

    d_text = format_deleted_message(
        chat_title="Guruh 1",
        chat_username="group1",
        sender_name="Alisher",
        sender_username="alisher_99",
        sent_at=now_ts - 60,
        deleted_at=now_ts,
        content_text="O'chirilgan matn"
    )
    assert "Xabar o‘chirildi" in d_text
    assert "O'chirilgan matn" in d_text
    print("✅ Formatter format_deleted_message muvaffaqiyatli")

    e_text = format_edited_message(
        chat_title="Do'st",
        chat_username=None,
        sender_name="Jasur",
        sender_username=None,
        sent_at=now_ts - 100,
        edit_at=now_ts,
        old_text="Eski gap",
        new_text="Yangi gap"
    )
    assert "Xabar tahrirlandi" in e_text
    assert "Eski matn" in e_text
    assert "Yangi matn" in e_text
    print("✅ Formatter format_edited_message muvaffaqiyatli")

    # 3. Media ekstraksiya testlari
    fake_photo_msg = Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        photo=[
            PhotoSize(file_id="p1", file_unique_id="u1", width=100, height=100),
            PhotoSize(file_id="p2", file_unique_id="u2", width=800, height=800),
        ],
        has_protected_content=True
    )
    info_p = extract_media_info(fake_photo_msg)
    assert info_p["content_type"] == "photo"
    assert info_p["file_id"] == "p2"
    assert info_p["is_view_once"] is True
    print("✅ extract_media_info (photo view-once) muvaffaqiyatli")

    fake_voice_msg = Message(
        message_id=2,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        voice=Voice(file_id="v1", file_unique_id="uv1", duration=5),
        has_protected_content=True
    )
    info_v = extract_media_info(fake_voice_msg)
    assert info_v["content_type"] == "voice"
    assert info_v["is_view_once"] is True
    print("✅ extract_media_info (voice view-once) muvaffaqiyatli")

    fake_vn_msg = Message(
        message_id=3,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        video_note=VideoNote(file_id="vn1", file_unique_id="uvn1", length=240, duration=10),
        has_protected_content=False
    )
    info_vn = extract_media_info(fake_vn_msg)
    assert info_vn["content_type"] == "video_note"
    assert info_vn["is_view_once"] is False
    print("✅ extract_media_info (video_note regular) muvaffaqiyatli")

    # 4. Dispatcher va Router yangilanish turlari tekshiruvi
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(business_router)
    used_updates = dp.resolve_used_update_types()
    assert "business_connection" in used_updates
    assert "business_message" in used_updates
    assert "deleted_business_messages" in used_updates
    assert "edited_business_message" in used_updates
    assert "message" in used_updates
    print(f"✅ dp.resolve_used_update_types(): {used_updates}")

    # Tozalash
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    print("================== BARCHA TESTLAR MUVAFFAQITYATLI O'TDI! ==================")


if __name__ == "__main__":
    asyncio.run(run_tests())

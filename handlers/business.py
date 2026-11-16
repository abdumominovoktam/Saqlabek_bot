import json
import logging
import time
from aiogram import Bot, Router
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message
from config import config
from database import Database
from utils.formatter import (
    format_chat_label,
    format_deleted_message,
    format_edited_message,
    format_timestamp,
    format_user_label,
)
from utils.media import (
    extract_media_info,
    save_and_forward_view_once_media,
    send_deleted_media,
)

logger = logging.getLogger(__name__)
business_router = Router(name="business_events")


# ==========================================
# 1. Ulanishni boshqarish (business_connection)
# ==========================================
@business_router.business_connection()
async def on_business_connection(
    event: BusinessConnection,
    bot: Bot,
    db: Database
) -> None:
    """
    Foydalanuvchi botni akkauntiga ulaganda yoki uzganda chaqiriladi.
    """
    try:
        user_id = event.user.id
        user_chat_id = event.user_chat_id
        is_enabled = bool(event.is_enabled)
        can_reply = bool(event.can_reply)

        # Ruxsatlar (rights) holati
        rights_dict = event.rights.model_dump() if event.rights else None
        rights_json = json.dumps(rights_dict) if rights_dict else None
        can_read = event.rights.can_read_messages if event.rights else True

        # Bazaga ulanish ma'lumotlarini saqlash / yangilash
        await db.save_or_update_connection(
            business_connection_id=event.id,
            user_id=user_id,
            user_chat_id=user_chat_id,
            is_enabled=is_enabled,
            can_reply=can_reply,
            can_read_messages=can_read,
            rights_json=rights_json,
        )

        logger.info(
            f"Business connection yangilandi: ID={event.id}, user_id={user_id}, "
            f"enabled={is_enabled}, can_read={can_read}"
        )

        if is_enabled:
            if can_read:
                welcome_text = (
                    "✅ <b>Bot akkauntingizga muvaffaqiyatli ulandi!</b>\n\n"
                    "Endi barcha o‘chirilgan va tahrirlangan xabarlar hamda "
                    "vaqtinchalik (bir martalik) medialar darhol shu yerga yuboriladi.\n\n"
                    f"🆔 <b>Ulanish ID:</b> <code>{event.id}</code>\n"
                    "⚙️ Holatni tekshirish uchun: /status"
                )
                await bot.send_message(chat_id=user_chat_id, text=welcome_text, parse_mode="HTML")
            else:
                warning_text = (
                    "⚠️ <b>DIQQAT! Ruxsat yetarli emas!</b>\n\n"
                    "Bot akkauntingizga ulandi, lekin <b>«Xabarlarni o‘qish» (Read messages)</b> "
                    "ruxsati yoqilmagan!\n\n"
                    "Bot o‘chirilgan/tahrirlangan xabarlar va bir martalik medialarni "
                    "saqlay olishi uchun Telegram Sozlamalaridagi chat-bot boshqaruviga kirib, "
                    "<b>xabarlarni o‘qish ruxsatini yoqing</b>."
                )
                await bot.send_message(chat_id=user_chat_id, text=warning_text, parse_mode="HTML")
        else:
            await db.disable_connection(event.id)
            disconnect_text = (
                "🔴 <b>Ulanish to‘xtatildi:</b>\n"
                f"Sizning Telegram akkauntingiz bilan bot o‘rtasidagi ulanish (ID: <code>{event.id}</code>) uzildi.\n\n"
                "Qayta ulash uchun Telegram Sozlamalari orqali botni qayta qo‘shishingiz mumkin."
            )
            try:
                await bot.send_message(chat_id=user_chat_id, text=disconnect_text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Uzilish xabarini yuborishda xatolik: {e}")

    except Exception as e:
        logger.error(f"business_connection handlerda xatolik: {e}", exc_info=True)


# ==========================================
# 2. Xabarlarni keshlash va bir martalik media saqlash (business_message)
# ==========================================
@business_router.business_message()
async def on_business_message(
    message: Message,
    bot: Bot,
    db: Database
) -> None:
    """
    Har bir yangi kiruvchi va chiquvchi biznes xabarni keshga yozish
    hamda bir martalik (view-once) medialarni darhol saqlab olish.
    """
    try:
        conn_id = message.business_connection_id
        if not conn_id:
            return

        connection = await db.get_connection(conn_id)

        # Chiquvchi (akkaunt egasi yozgan) xabar ekanligini aniqlash
        is_outgoing = False
        user_chat_id = None
        if connection:
            is_outgoing = bool(message.from_user and message.from_user.id == connection["user_id"])
            user_chat_id = connection["user_chat_id"]

        # Media ma'lumotlarini aniqlash
        media_info = extract_media_info(message)
        has_protected = bool(message.has_protected_content)

        # 1. BIR MARTALIK (VIEW-ONCE) MEDIALARNI SAQLASH
        # Agar suhbatdosh bir martalik yoki protected media yuborgan bo'lsa
        if media_info["is_view_once"] and user_chat_id and not is_outgoing:
            logger.info(
                f"Bir martalik ({media_info['media_type_name']}) media aniqlandi! "
                f"Chat: {message.chat.id}, Muallif: {message.from_user.id if message.from_user else 'None'}"
            )
            await save_and_forward_view_once_media(
                bot=bot,
                message=message,
                user_chat_id=user_chat_id,
                media_info=media_info
            )

        # 2. XABARNI BAZADA KESHLASH
        chat_title = message.chat.title or (
            f"{message.chat.first_name or ''} {message.chat.last_name or ''}".strip() or "Shaxsiy chat"
        )
        chat_username = message.chat.username

        sender_id = message.from_user.id if message.from_user else None
        sender_name = message.from_user.full_name if message.from_user else None
        sender_username = message.from_user.username if message.from_user else None

        text_content = message.text or message.caption
        sent_at = int(message.date.timestamp())

        await db.save_message(
            business_connection_id=conn_id,
            chat_id=message.chat.id,
            chat_title=chat_title,
            chat_username=chat_username,
            message_id=message.message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_username=sender_username,
            is_outgoing=is_outgoing,
            content_type=media_info["content_type"],
            text=text_content,
            file_id=media_info["file_id"],
            file_unique_id=media_info["file_unique_id"],
            has_protected_content=has_protected,
            sent_at=sent_at,
        )

    except Exception as e:
        logger.error(f"business_message handlerda xatolik: {e}", exc_info=True)


# ==========================================
# 3. O'chirilgan xabarlarni tiklash (deleted_business_messages)
# ==========================================
@business_router.deleted_business_messages()
async def on_deleted_business_messages(
    event: BusinessMessagesDeleted,
    bot: Bot,
    db: Database
) -> None:
    """
    Xabar(lar) o'chirilganda ularni bazadan topib, akkaunt egasiga yuborish.
    """
    try:
        conn_id = event.business_connection_id
        connection = await db.get_connection(conn_id)
        if not connection:
            logger.warning(f"O'chirilgan xabarlar uchun connection ({conn_id}) topilmadi!")
            return

        user_chat_id = connection["user_chat_id"]
        chat_id = event.chat.id
        now_ts = int(time.time())

        # Xabarlarni xronologik tartibda bazadan olish
        sorted_ids = sorted(event.message_ids)
        cached_messages = await db.get_messages_by_ids(
            business_connection_id=conn_id,
            chat_id=chat_id,
            message_ids=sorted_ids
        )
        cached_map = {m["message_id"]: m for m in cached_messages}

        for msg_id in sorted_ids:
            cached_msg = cached_map.get(msg_id)

            if cached_msg:
                # O'z xabarlari o'chirilganda bildirishnoma sozlamasi tekshiruvi
                if cached_msg["is_outgoing"] and not config.NOTIFY_OWN_DELETED_MESSAGES:
                    logger.debug(f"Akkaunt egasining o'z xabari ({msg_id}) o'chirildi, sozlamaga ko'ra o'tkazib yuborildi.")
                    continue

                notification_text = format_deleted_message(
                    chat_title=cached_msg["chat_title"],
                    chat_username=cached_msg["chat_username"],
                    sender_name=cached_msg["sender_name"],
                    sender_username=cached_msg["sender_username"],
                    sent_at=cached_msg["sent_at"],
                    deleted_at=now_ts,
                    content_text=cached_msg["text"],
                    content_type=cached_msg["content_type"]
                )

                content_type = cached_msg["content_type"]
                file_id = cached_msg["file_id"]

                # Agar xabarda media mavjud bo'lsa
                if file_id and content_type != "text":
                    sent = await send_deleted_media(
                        bot=bot,
                        user_chat_id=user_chat_id,
                        content_type=content_type,
                        file_id=file_id,
                        caption=notification_text
                    )
                    if not sent:
                        # Media Telegram CDN dan o'chirilgan bo'lsa, matnli xabarni ogohlantirish bilan yuboramiz
                        fallback_text = (
                            notification_text +
                            "\n\n⚠️ <i>(Media fayl Telegram serveridan butunlay o‘chirilgan bo‘lishi mumkin)</i>"
                        )
                        await bot.send_message(
                            chat_id=user_chat_id,
                            text=fallback_text,
                            parse_mode="HTML"
                        )
                else:
                    # Oddiy matnli xabar
                    await bot.send_message(
                        chat_id=user_chat_id,
                        text=notification_text,
                        parse_mode="HTML"
                    )

            else:
                # Xabar bot ulanishidan oldin yuborilgan yoki keshda mavjud emas
                chat_title = event.chat.title or (
                    f"{event.chat.first_name or ''} {event.chat.last_name or ''}".strip() or "Shaxsiy chat"
                )
                chat_label = format_chat_label(chat_title, event.chat.username)
                not_cached_text = (
                    "🗑️ <b>Xabar o‘chirildi (Keshda topilmadi)</b>\n"
                    f"💬 <b>Chat:</b> {chat_label}\n"
                    f"🆔 <b>Xabar ID:</b> <code>#{msg_id}</code>\n"
                    f"🗑️ <b>O‘chirilgan:</b> {format_timestamp(now_ts)}\n"
                    "⚠️ <i>Ushbu xabar bot ulanishidan oldin yuborilgan yoki saqlanmagan.</i>"
                )
                await bot.send_message(
                    chat_id=user_chat_id,
                    text=not_cached_text,
                    parse_mode="HTML"
                )

    except Exception as e:
        logger.error(f"deleted_business_messages handlerda xatolik: {e}", exc_info=True)


# ==========================================
# 4. Tahrirlangan xabarlarni kuzatish (edited_business_message)
# ==========================================
@business_router.edited_business_message()
async def on_edited_business_message(
    message: Message,
    bot: Bot,
    db: Database
) -> None:
    """
    Xabar tahrirlanganda eski va yangi matnni solishtirib, akkaunt egasiga yuborish.
    """
    try:
        conn_id = message.business_connection_id
        if not conn_id:
            return

        connection = await db.get_connection(conn_id)
        if not connection:
            return

        user_chat_id = connection["user_chat_id"]
        chat_id = message.chat.id
        msg_id = message.message_id

        # Bazadagi eski xabarni qidirish
        cached_msg = await db.get_message(
            business_connection_id=conn_id,
            chat_id=chat_id,
            message_id=msg_id
        )

        new_text = message.text or message.caption or ""
        edit_at = message.edit_date or int(time.time())

        chat_title = message.chat.title or (
            f"{message.chat.first_name or ''} {message.chat.last_name or ''}".strip() or "Shaxsiy chat"
        )
        chat_username = message.chat.username

        sender_name = message.from_user.full_name if message.from_user else "Noma'lum"
        sender_username = message.from_user.username if message.from_user else None

        if cached_msg:
            old_text = cached_msg["text"] or ""
            sent_at = cached_msg["sent_at"]

            # Agar matn haqiqatda o'zgargan bo'lsa
            if old_text != new_text:
                notification_text = format_edited_message(
                    chat_title=chat_title,
                    chat_username=chat_username,
                    sender_name=sender_name,
                    sender_username=sender_username,
                    sent_at=sent_at,
                    edit_at=edit_at,
                    old_text=old_text,
                    new_text=new_text
                )

                await bot.send_message(
                    chat_id=user_chat_id,
                    text=notification_text,
                    parse_mode="HTML"
                )

                # Bazadagi matnni yangilab qo'yish
                await db.update_message_text(
                    business_connection_id=conn_id,
                    chat_id=chat_id,
                    message_id=msg_id,
                    new_text=new_text
                )
        else:
            # Agar xabar oldin keshlanmagan bo'lsa, uni hozir saqlab qo'yamiz
            is_outgoing = bool(message.from_user and message.from_user.id == connection["user_id"])
            media_info = extract_media_info(message)
            await db.save_message(
                business_connection_id=conn_id,
                chat_id=chat_id,
                chat_title=chat_title,
                chat_username=chat_username,
                message_id=msg_id,
                sender_id=message.from_user.id if message.from_user else None,
                sender_name=sender_name,
                sender_username=sender_username,
                is_outgoing=is_outgoing,
                content_type=media_info["content_type"],
                text=new_text,
                file_id=media_info["file_id"],
                file_unique_id=media_info["file_unique_id"],
                has_protected_content=bool(message.has_protected_content),
                sent_at=int(message.date.timestamp()),
            )

    except Exception as e:
        logger.error(f"edited_business_message handlerda xatolik: {e}", exc_info=True)

import io
import logging
from typing import Any
from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, Message
from utils.formatter import format_view_once_media

logger = logging.getLogger(__name__)


def extract_media_info(message: Message) -> dict[str, Any]:
    """
    Xabardagi media turini, file_id va yuklab olish uchun mos ob'ektni aniqlash.
    Qo'llab-quvvatlanadi: photo, video, video_note, voice, audio, document, sticker, animation.
    """
    info = {
        "content_type": "text",
        "media_type_name": "Matn",
        "file_id": None,
        "file_unique_id": None,
        "file_obj": None,
        "filename": None,
        "is_view_once": False,
    }

    # Bir martalik (view-once) yoki vaqtinchalik xususiyatlarni tekshirish
    is_protected = bool(message.has_protected_content)

    if message.photo:
        photo = message.photo[-1]  # Eng yuqori sifatli rasm
        info.update({
            "content_type": "photo",
            "media_type_name": "Rasm (Photo)",
            "file_id": photo.file_id,
            "file_unique_id": photo.file_unique_id,
            "file_obj": photo,
            "filename": f"photo_{photo.file_unique_id}.jpg",
            "is_view_once": is_protected or getattr(photo, "is_view_once", False),
        })
    elif message.video:
        video = message.video
        info.update({
            "content_type": "video",
            "media_type_name": "Video",
            "file_id": video.file_id,
            "file_unique_id": video.file_unique_id,
            "file_obj": video,
            "filename": video.file_name or f"video_{video.file_unique_id}.mp4",
            "is_view_once": is_protected or getattr(video, "is_view_once", False),
        })
    elif message.video_note:
        vn = message.video_note
        info.update({
            "content_type": "video_note",
            "media_type_name": "Dumaloq video (Video note)",
            "file_id": vn.file_id,
            "file_unique_id": vn.file_unique_id,
            "file_obj": vn,
            "filename": f"video_note_{vn.file_unique_id}.mp4",
            "is_view_once": is_protected or getattr(vn, "is_view_once", False),
        })
    elif message.voice:
        voice = message.voice
        info.update({
            "content_type": "voice",
            "media_type_name": "Ovozli xabar (Voice)",
            "file_id": voice.file_id,
            "file_unique_id": voice.file_unique_id,
            "file_obj": voice,
            "filename": f"voice_{voice.file_unique_id}.ogg",
            "is_view_once": is_protected or getattr(voice, "is_view_once", False),
        })
    elif message.audio:
        audio = message.audio
        info.update({
            "content_type": "audio",
            "media_type_name": "Audio / Musiqa",
            "file_id": audio.file_id,
            "file_unique_id": audio.file_unique_id,
            "file_obj": audio,
            "filename": audio.file_name or f"audio_{audio.file_unique_id}.mp3",
            "is_view_once": False,
        })
    elif message.document:
        doc = message.document
        info.update({
            "content_type": "document",
            "media_type_name": "Hujjat (Document)",
            "file_id": doc.file_id,
            "file_unique_id": doc.file_unique_id,
            "file_obj": doc,
            "filename": doc.file_name or f"doc_{doc.file_unique_id}.bin",
            "is_view_once": False,
        })
    elif message.sticker:
        sticker = message.sticker
        info.update({
            "content_type": "sticker",
            "media_type_name": "Stiker (Sticker)",
            "file_id": sticker.file_id,
            "file_unique_id": sticker.file_unique_id,
            "file_obj": sticker,
            "filename": f"sticker_{sticker.file_unique_id}.webp",
            "is_view_once": False,
        })
    elif message.animation:
        anim = message.animation
        info.update({
            "content_type": "animation",
            "media_type_name": "GIF / Animatsiya",
            "file_id": anim.file_id,
            "file_unique_id": anim.file_unique_id,
            "file_obj": anim,
            "filename": anim.file_name or f"animation_{anim.file_unique_id}.mp4",
            "is_view_once": False,
        })

    return info


async def download_media_bytes(bot: Bot, file_obj: Any) -> bytes | None:
    """Faylni xotiraga (RAM) yuklab olib, bayt ko'rinishida qaytarish."""
    try:
        buffer = io.BytesIO()
        await bot.download(file_obj, destination=buffer)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Faylni yuklab olishda xatolik: {e}", exc_info=True)
        return None


async def save_and_forward_view_once_media(
    bot: Bot,
    message: Message,
    user_chat_id: int,
    media_info: dict[str, Any]
) -> bool:
    """
    Bir martalik / vaqtinchalik mediani Telegram serveridan o'chib ketishidan oldin
    darhol yuklab olib, BufferedInputFile orqali akkaunt egasiga yuborish.
    """
    file_obj = media_info.get("file_obj")
    if not file_obj:
        return False

    sender_name = message.from_user.full_name if message.from_user else "Noma'lum"
    sender_username = message.from_user.username if message.from_user else None
    caption_text = message.caption or message.text

    notification_text = format_view_once_media(
        sender_name=sender_name,
        sender_username=sender_username,
        sent_at=message.date,
        media_type=media_info["media_type_name"],
        caption=caption_text
    )

    try:
        # Faylni xotiraga bayt ko'rinishida yuklab olish
        file_bytes = await download_media_bytes(bot, file_obj)
        if not file_bytes:
            # Faylni yuklab bo'lmadi, foydalanuvchiga matnli ogohlantirish yuboramiz
            await bot.send_message(
                chat_id=user_chat_id,
                text=notification_text + "\n\n⚠️ <i>(Fayl baytlarini Telegramdan yuklab bo'lmadi)</i>",
                parse_mode="HTML"
            )
            return False

        filename = media_info.get("filename") or "media_file.bin"
        input_file = BufferedInputFile(file_bytes, filename=filename)
        content_type = media_info["content_type"]

        # Caption uzunligi 1024 belgidan oshmasligini nazorat qilish
        short_caption = notification_text[:1020] + "..." if len(notification_text) > 1024 else notification_text

        if content_type == "photo":
            await bot.send_photo(
                chat_id=user_chat_id,
                photo=input_file,
                caption=short_caption,
                parse_mode="HTML"
            )
        elif content_type == "video":
            await bot.send_video(
                chat_id=user_chat_id,
                video=input_file,
                caption=short_caption,
                parse_mode="HTML"
            )
        elif content_type == "voice":
            await bot.send_voice(
                chat_id=user_chat_id,
                voice=input_file,
                caption=short_caption,
                parse_mode="HTML"
            )
        elif content_type == "video_note":
            # Dumaloq videoga caption ulab bo'lmaydi, alohida yuboriladi
            await bot.send_video_note(
                chat_id=user_chat_id,
                video_note=input_file
            )
            await bot.send_message(
                chat_id=user_chat_id,
                text=notification_text,
                parse_mode="HTML"
            )
        else:
            await bot.send_document(
                chat_id=user_chat_id,
                document=input_file,
                caption=short_caption,
                parse_mode="HTML"
            )

        logger.info(f"Vaqtinchalik media muvaffaqiyatli saqlandi va foydalanuvchiga ({user_chat_id}) yuborildi.")
        return True

    except Exception as e:
        logger.error(f"Vaqtinchalik mediani yuborishda xatolik: {e}", exc_info=True)
        try:
            await bot.send_message(
                chat_id=user_chat_id,
                text=notification_text + f"\n\n⚠️ <i>(Mediani yuborishda xatolik yuz berdi: {html.escape(str(e))})</i>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return False


async def send_deleted_media(
    bot: Bot,
    user_chat_id: int,
    content_type: str,
    file_id: str | None,
    caption: str
) -> bool:
    """O'chirilgan xabardagi mediani akkaunt egasiga file_id orqali yuborish."""
    if not file_id:
        return False

    short_caption = caption[:1020] + "..." if len(caption) > 1024 else caption

    try:
        if content_type == "photo":
            await bot.send_photo(chat_id=user_chat_id, photo=file_id, caption=short_caption, parse_mode="HTML")
        elif content_type == "video":
            await bot.send_video(chat_id=user_chat_id, video=file_id, caption=short_caption, parse_mode="HTML")
        elif content_type == "voice":
            await bot.send_voice(chat_id=user_chat_id, voice=file_id, caption=short_caption, parse_mode="HTML")
        elif content_type == "video_note":
            await bot.send_video_note(chat_id=user_chat_id, video_note=file_id)
            await bot.send_message(chat_id=user_chat_id, text=caption, parse_mode="HTML")
        elif content_type == "audio":
            await bot.send_audio(chat_id=user_chat_id, audio=file_id, caption=short_caption, parse_mode="HTML")
        elif content_type == "document":
            await bot.send_document(chat_id=user_chat_id, document=file_id, caption=short_caption, parse_mode="HTML")
        elif content_type == "sticker":
            await bot.send_sticker(chat_id=user_chat_id, sticker=file_id)
            await bot.send_message(chat_id=user_chat_id, text=caption, parse_mode="HTML")
        elif content_type == "animation":
            await bot.send_animation(chat_id=user_chat_id, animation=file_id, caption=short_caption, parse_mode="HTML")
        else:
            return False
        return True
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logger.warning(f"O'chirilgan mediani file_id orqali yuborib bo'lmadi ({e.message})")
        return False
    except Exception as e:
        logger.error(f"O'chirilgan mediani yuborishda kutilmagan xatolik: {e}")
        return False

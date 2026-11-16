from datetime import datetime, timezone
import html
from zoneinfo import ZoneInfo
from config import config

# Konfiguratsiyadagi vaqt zonasi
try:
    TZ = ZoneInfo(config.TIMEZONE)
except Exception:
    TZ = ZoneInfo("Asia/Tashkent")


def escape_html(text: str | None) -> str:
    """
    Telegram HTML formati uchun xavfsiz escape qilish.
    quote=False qilinadi, chunki Telegramda ' va " belgilarini o'zgartirish shart emas
    va apostrof (o'zbek tilidagi tutuq belgisi) buzilmasligi ta'minlanadi.
    """
    if not text:
        return ""
    return html.escape(str(text), quote=False)


def format_timestamp(ts: int | float | datetime | None) -> str:
    """Unix timestamp yoki datetime ob'ektini DD.MM.YYYY HH:MM formatiga o'girish."""
    if ts is None:
        return "Noma'lum"

    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(TZ)
    elif isinstance(ts, datetime):
        if ts.tzinfo is None:
            dt = ts.replace(tzinfo=timezone.utc).astimezone(TZ)
        else:
            dt = ts.astimezone(TZ)
    else:
        return str(ts)

    return dt.strftime("%d.%m.%Y %H:%M")


def format_user_label(name: str | None, username: str | None) -> str:
    """Foydalanuvchi ism-familiyasi va usernamesini chiroyli formatlash."""
    safe_name = escape_html(name or "Noma'lum foydalanuvchi")
    if username:
        safe_username = escape_html(username.lstrip("@"))
        return f"{safe_name} (@{safe_username})"
    return safe_name


def format_chat_label(title: str | None, username: str | None) -> str:
    """Chat nomi va usernamesini chiroyli formatlash."""
    safe_title = escape_html(title or "Shaxsiy chat")
    if username:
        safe_username = escape_html(username.lstrip("@"))
        return f"{safe_title} (@{safe_username})"
    return safe_title


def format_view_once_media(
    sender_name: str | None,
    sender_username: str | None,
    sent_at: int | float | datetime | None,
    media_type: str,
    caption: str | None = None
) -> str:
    """Bir martalik / vaqtinchalik media saqlanganda xabar matni."""
    sender_str = format_user_label(sender_name, sender_username)
    date_str = format_timestamp(sent_at)
    safe_caption = escape_html(caption) if caption else "Yo‘q"

    return (
        "🕒 <b>Vaqtinchalik media saqlandi</b>\n"
        f"👤 <b>Kimdan:</b> {sender_str}\n"
        f"📅 <b>Yuborilgan:</b> {date_str}\n"
        f"📎 <b>Turi:</b> {escape_html(media_type)}\n"
        f"📝 <b>Izoh:</b> {safe_caption}"
    )


def format_deleted_message(
    chat_title: str | None,
    chat_username: str | None,
    sender_name: str | None,
    sender_username: str | None,
    sent_at: int | float | datetime | None,
    deleted_at: int | float | datetime | None,
    content_text: str | None = None,
    content_type: str = "text"
) -> str:
    """O'chirilgan xabar haqida bildirishnoma matni."""
    chat_str = format_chat_label(chat_title, chat_username)
    sender_str = format_user_label(sender_name, sender_username)
    sent_str = format_timestamp(sent_at)
    deleted_str = format_timestamp(deleted_at)

    text_display = escape_html(content_text) if content_text else "<i>(Matnsiz media yoki fayl)</i>"

    return (
        "🗑️ <b>Xabar o‘chirildi</b>\n"
        f"💬 <b>Chat:</b> {chat_str}\n"
        f"👤 <b>Muallif:</b> {sender_str}\n"
        f"📅 <b>Yuborilgan:</b> {sent_str}\n"
        f"🗑️ <b>O‘chirilgan:</b> {deleted_str}\n"
        f"📝 <b>Matn:</b> {text_display}"
    )


def format_edited_message(
    chat_title: str | None,
    chat_username: str | None,
    sender_name: str | None,
    sender_username: str | None,
    sent_at: int | float | datetime | None,
    edit_at: int | float | datetime | None,
    old_text: str | None,
    new_text: str | None
) -> str:
    """Tahrirlangan xabar haqida bildirishnoma matni."""
    chat_str = format_chat_label(chat_title, chat_username)
    sender_str = format_user_label(sender_name, sender_username)
    sent_str = format_timestamp(sent_at)
    edit_str = format_timestamp(edit_at)

    safe_old_text = escape_html(old_text) if old_text else "<i>(Bo‘sh)</i>"
    safe_new_text = escape_html(new_text) if new_text else "<i>(Bo‘sh)</i>"

    return (
        "✏️ <b>Xabar tahrirlandi</b>\n"
        f"💬 <b>Chat:</b> {chat_str}\n"
        f"👤 <b>Kimdan:</b> {sender_str}\n"
        f"📅 <b>Yuborilgan:</b> {sent_str} | ✏️ <b>Tahrirlangan:</b> {edit_str}\n\n"
        f"❌ <b>Eski matn:</b>\n{safe_old_text}\n\n"
        f"✅ <b>Yangi matn:</b>\n{safe_new_text}"
    )

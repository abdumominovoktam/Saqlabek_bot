import logging
from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from config import config
from database import Database
from utils.formatter import format_timestamp

logger = logging.getLogger(__name__)
user_router = Router(name="user_commands")


@user_router.message(CommandStart())
async def handle_start(message: Message, bot: Bot, db: Database) -> None:
    """
    /start buyrug'i: Ulanish holati va botni akkauntga ulash bo'yicha batafsil qo'llanma.
    """
    user_id = message.from_user.id if message.from_user else 0
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "Bot"

    # Bazadan ulanish holatini tekshirish
    connection = await db.get_active_connection_by_user(user_id)
    if connection:
        status_line = (
            "🟢 <b>Akkaunt holati: Ulangan va faol</b>\n"
            f"🆔 <b>Ulanish ID:</b> <code>{connection['business_connection_id']}</code>\n"
        )
    else:
        status_line = "🔴 <b>Akkaunt holati: Ulanmagan</b>\n"

    guide_text = (
        f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        f"{status_line}\n"
        "Men shaxsiy Telegram akkauntingizga ulanib, <b>o‘chirilgan xabarlar</b>, "
        "<b>tahrirlangan xabarlar</b> va <b>vaqtinchalik (bir martalik) medialarni</b> "
        "saqlab beruvchi rasmiy <i>Telegram Chat Automation / Business</i> yordamchisiman.\n\n"
        "Akkauntingiz bloklanish xavfi mutlaqo yo‘q (Userbot emas, rasmiy Bot API orqali ishlaydi).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📖 <b>BOTNI AKKAUNTGA ULASH QO‘LLANMASI:</b>\n\n"
        "🔹 <b>1. Oddiy (bepul) Telegram akkauntlar uchun:</b>\n"
        "1️⃣ Telegram <b>Sozlamalar (Settings)</b> menyusiga kiring.\n"
        "2️⃣ <b>Chat Automation</b> (Chat avtomatizatsiyasi) bandini tanlang.\n"
        f"3️⃣ Bot usernamesini qidiring: <code>@{bot_username}</code>\n"
        "4️⃣ <b>«Xabarlarni o‘qish» (Read messages)</b> ruxsatini yoqing va tasdiqlang.\n\n"
        "🔹 <b>2. Telegram Premium akkauntlar uchun:</b>\n"
        "1️⃣ Telegram <b>Sozlamalar (Settings)</b> menyusiga kiring.\n"
        "2️⃣ <b>Telegram Business</b> bo‘limini oching.\n"
        "3️⃣ <b>Chat-botlar (Chatbots)</b> menyusiga kiring.\n"
        f"4️⃣ Bot usernamesini kiriting: <code>@{bot_username}</code>\n"
        "5️⃣ Ruxsatlarni (ayniqsa xabarlarni o‘qishni) yoqib, ulashni yakunlang.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Ulanish o‘rnatilgach, bot sizga darhol bildirishnoma yuboradi.</i>\n\n"
        "📊 Holatni tekshirish uchun: /status"
    )

    await message.answer(guide_text, parse_mode="HTML")


@user_router.message(Command("status"))
async def handle_status(message: Message, bot: Bot, db: Database) -> None:
    """
    /status buyrug'i: Joriy ulanish diagnostikasi va saqlangan xabarlar statistikasi.
    """
    user_id = message.from_user.id if message.from_user else 0
    active_conn = await db.get_active_connection_by_user(user_id)
    latest_conn = await db.get_latest_connection_by_user(user_id)

    total_cached = await db.get_message_count_for_user(user_id)

    if active_conn:
        conn_status = "🟢 Faol (Ulangan)"
        conn_id = f"<code>{active_conn['business_connection_id']}</code>"
        can_read = "✅ Ruxsat berilgan" if active_conn.get("can_read_messages") else "❌ Berilmagan (ogohlantirish!)"
        can_reply = "✅ Yoqilgan" if active_conn.get("can_reply") else "❌ O'chirilgan"
        updated_time = format_timestamp(active_conn.get("updated_at"))
    elif latest_conn:
        conn_status = "🔴 Nofaol (Uzilgan)"
        conn_id = f"<code>{latest_conn['business_connection_id']}</code>"
        can_read = "Noma'lum"
        can_reply = "Noma'lum"
        updated_time = format_timestamp(latest_conn.get("updated_at"))
    else:
        conn_status = "🔴 Hech qachon ulanmagan"
        conn_id = "Mavjud emas"
        can_read = "Mavjud emas"
        can_reply = "Mavjud emas"
        updated_time = "Yo'q"

    own_deleted_pref = (
        "✅ Bildirishnoma yuboriladi"
        if config.NOTIFY_OWN_DELETED_MESSAGES
        else "❌ E'tiborga olinmaydi (faqat suhbatdosh o'chirganlari)"
    )

    response_text = (
        "📊 <b>BOT VA AKKAUNT HOLATI:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name} (ID: <code>{user_id}</code>)\n"
        f"🔌 <b>Ulanish holati:</b> {conn_status}\n"
        f"🆔 <b>Ulanish ID:</b> {conn_id}\n"
        f"👁️ <b>Xabarlarni o‘qish ruxsati:</b> {can_read}\n"
        f"💬 <b>Javob berish huquqi:</b> {can_reply}\n"
        f"🕒 <b>Oxirgi yangilanish:</b> {updated_time}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📈 <b>STATISTIKA VA SOZLAMALAR:</b>\n"
        f"📦 <b>Keshlangan xabarlar:</b> <b>{total_cached:,}</b> ta\n"
        f"🗑️ <b>O‘z xabarlaringiz o‘chirilganda:</b> {own_deleted_pref}\n"
        f"⏳ <b>Xabarlar saqlanish muddati:</b> {config.RETENTION_DAYS} kun\n"
        f"🌐 <b>Vaqt zonasi:</b> <code>{config.TIMEZONE}</code>"
    )

    await message.answer(response_text, parse_mode="HTML")

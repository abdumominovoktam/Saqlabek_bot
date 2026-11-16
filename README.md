# 🛡️ Saqlabek Bot — Telegram Shaxsiy Akkaunt Uchun Anti-Delete, Edit-Tracker va View-Once Media Saqlovchi Bot

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.32+-green.svg)](https://docs.aiogram.dev/)
[![Telegram Bot API 10.0+](https://img.shields.io/badge/Bot%20API-10.0+-blueviolet.svg)](https://core.telegram.org/bots/api)
[![Database](https://img.shields.io/badge/Database-aiosqlite-lightgrey.svg)](https://github.com/omnilib/aiosqlite)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Saqlabek Bot** — shaxsiy Telegram akkauntingizga to‘g‘ridan-to‘g‘ri ulanadigan, suhbatdoshlaringiz tomonidan **o‘chirilgan xabarlar**, **tahrirlangan xabarlar** hamda **bir martalik (vaqtinchalik / view-once) medialarni** Telegram serverlaridan o‘chib ketishidan oldin tutib olib, bot chatiga xavfsiz saqlab beruvchi zamonaviy va mukammal tizim.

---

## ⚡ Asosiy Arxitektura va Xavfsizlik

1. **Akkaunt bloklanish xavfi mutlaqo yo‘q (0% xavf):**
   - Ushbu bot bloklanish xavfi yuqori bo‘lgan **Userbot (Telethon / Pyrogram)** tizimlariga asoslanmagan.
   - U Telegramning rasmiy **Bot API 10.0+ (`Secretary Mode` / `Business Mode` / `Chat Automation`)** mexanizmi orqali ishlaydi.
2. **Ham Bepul (Oddiy), ham Telegram Premium akkauntlar uchun:**
   - Telegram Bot API 10.0+ orqali barcha foydalanuvchilar — **oddiy (bepul) akkauntlar** (`Settings -> Chatni avtomatlashtirish`) va **Telegram Premium akkauntlar** (`Settings -> Telegram Business -> Chat-botlar`) botdan teng foydalana oladi.
3. **Kafolatlangan yangilanishlar:**
   - Bot `dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())` orqali `business_connection`, `business_message`, `edited_business_message` va `deleted_business_messages` yangilanishlarini kechikishsiz qabul qiladi.

---

## ✨ Bot Imkoniyatlari

### 1. 🕒 Bir martalik / Vaqtinchalik medialarni saqlash (View-Once Saver)
- Suhbatdoshingiz bir martalik yoki taymerli rasm (`photo`), video (`video`), dumaloq video (`video_note`) yoki ovozli xabar (`voice`) yuborganda, bot uni **zudlik bilan xotiraga (RAM) bayt ko‘rinishida yuklab oladi** (`bot.download(...)`).
- `BufferedInputFile` orqali fayl darhol sizning bot chatiga jo‘natiladi. Suhbatdosh xabarni o‘chirsa yoki vaqt tugasa ham fayl sizda qoladi.

```
🕒 Vaqtinchalik media saqlandi
👤 Kimdan: Alisher Valiyev (@alisher_dev)
📅 Yuborilgan: 16.11.2026 09:30
📎 Turi: Rasm (Photo)
📝 Izoh: Maxfiy rasm
```

### 2. 🗑️ O‘chirilgan xabarlarni tiklash (Anti-Delete)
- Kiruvchi va chiquvchi barcha xabarlar `aiosqlite` da keshlanadi.
- Qo‘llab-quvvatlanadigan turlar: matn, rasm, video, dumaloq video, ovozli xabar, audio, hujjat, stiker, GIF.
- Xabar o‘chirilganda xronologik tartibda tiklanadi va media fayli bilan birga yuboriladi.
- `NOTIFY_OWN_DELETED_MESSAGES` orqali o‘zingiz o‘chirgan xabarlar haqida bildirishnoma kelishini boshqarish mumkin.

```
🗑️ Xabar o‘chirildi
💬 Chat: Jasur Do'stim (@jasur_tg)
👤 Muallif: Jasur Do'stim
📅 Yuborilgan: 16.11.2026 08:45
🗑️ O‘chirilgan: 16.11.2026 09:15
📝 Matn: Ertaga soat 10:00 da uchrashamiz!
```

### 3. ✏️ Tahrirlangan xabarlarni solishtirish (Edit-Tracker)
- Xabar o‘zgartirilganda eski va yangi matn solishtirilib, qanday tahrir qilingani ko‘rsatiladi:

```
✏️ Xabar tahrirlandi
💬 Chat: Ishchi Guruh
👤 Kimdan: Sardor (@sardor_work)
📅 Yuborilgan: 16.11.2026 08:00 | ✏️ Tahrirlangan: 16.11.2026 09:20

❌ Eski matn:
Bugun hisobot topshirilmaydi.

✅ Yangi matn:
Bugun soat 14:00 gacha hisobotni albatta jo'natinglar!
```

### 4. 🔌 Ulanish va Diagnostika (`/start`, `/status`)
- `/start` — ulanish holatini (`🟢 Ulangan` yoki `🔴 Ulanmagan`) ko‘rsatadi va akkauntga ulash bo‘yicha qo‘llanma beradi.
- `/status` — ulanish ID, ruxsatlar, saqlangan xabarlar soni va server diagnostikasini ko‘rsatadi.

### 5. 🧹 Avtomatik fon tozalash (Retention Purge)
- Fon vazifasi har 24 soatda avtomatik ishlab, `RETENTION_DAYS` (standart 30 kun) dan eski xabarlarni tozalab boradi.

---

## 🛠️ @BotFather Orqali Sozlash (Juda Muhim Qadam!)

Botni yaratgandan so‘ng, agar uni to‘g‘ridan-to‘g‘ri Telegram sozlamalariga ulamoqchi bo‘lsangiz, Telegram quyidagi xatolikni ko‘rsatadi:
> ⚠️ **«Afsus: Bu bot hali Kotib rejimini qo‘llab-quvvatlamaydi»** *(yoki inglizcha: This bot does not support Secretary/Business mode yet)*

### Buni 1 daqiqada yoqish tartibi:
1. Telegramda **[@BotFather](https://t.me/BotFather)** botiga kiring.
2. `/mybots` buyrug‘ini yuboring va o‘z botingizni tanlang.
3. **`Bot Settings`** tugmasini bosing.
4. **`Secretary Mode`** *(yoki ba'zi interfeyslarda `Business Mode`)* tugmasini bosing.
5. **`Turn on`** *(yoqish)* tugmasini bosing.
6. BotFather tasdiqlash xabarini yuboradi: `Secretary mode was enabled for @...`

Endi botingiz to‘liq tayyor!

---

## 📲 Botni Shaxsiy Akkauntga Ulash

### A) Oddiy (bepul) Telegram akkauntlar uchun:
1. Telegram ilovasida **Sozlamalar (Settings)** bo‘limiga kiring.
2. **Chatni avtomatlashtirish (Chat Automation)** bandini oching.
3. Botingiz usernamesini (`@bot_username`) kiriting.
4. **«Xabarlarni o‘qish» (Read messages)** ruxsatini yoqing va saqlang.

### B) Telegram Premium akkauntlar uchun:
1. Telegram ilovasida **Sozlamalar (Settings)** bo‘limiga kiring.
2. **Telegram Business** bo‘limiga kiring.
3. **Chat-botlar (Chatbots)** menyusini oching.
4. Botingiz usernamesini (`@bot_username`) kiritib, ruxsatlarni tasdiqlang.

---

## 🚀 O‘rnatish va Ishga Tushirish

### 1. Repositoryni klonlash yoki yuklab olish:
```bash
git clone https://github.com/<sizning_username>/Saqlabek_bot.git
cd Saqlabek_bot
```

### 2. Virtual muhit yaratish va faollashtirish:
```bash
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 3. Kutubxonalarni o‘rnatish:
```bash
pip install -r requirements.txt
```

### 4. `.env` faylini yaratish:
`.env.example` nusxasini olib, `.env` fayli yarating:
```ini
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DB_PATH=saqlabek.db
TIMEZONE=Asia/Tashkent
NOTIFY_OWN_DELETED_MESSAGES=False
RETENTION_DAYS=30
CLEANUP_INTERVAL_HOURS=24
```

### 5. Botni ishga tushirish:
```bash
python bot.py
```

### 6. Testlarni tekshirish:
```bash
python tests/test_saqlabek.py
```

---

## 📤 Loyihani GitHub ga Yuklash

Loyihani o‘zingizning GitHub hisobingizga yuklash uchun quyidagi buyruqlarni ketma-ket bajaring:

```bash
# 1. Git omborini yaratish
git init

# 2. Barcha fayllarni indeksga qo'shish (.gitignore dagi .env va kesh fayllar avtomatik chetlatiladi)
git add .

# 3. Ilk commitni yaratish
git commit -m "feat: initial commit - Saqlabek anti-delete and view-once saver bot"

# 4. Asosiy tarmoqni main ga o'tkazish
git branch -M main

# 5. O'zingizning GitHub repository manzilingizni ulash
git remote add origin https://github.com/<sizning_username>/Saqlabek_bot.git

# 6. GitHub ga yuklash
git push -u origin main
```

---

## 📄 Litsenziya

Ushbu loyiha [MIT Litsenziyasi](LICENSE) asosida tarqatiladi.

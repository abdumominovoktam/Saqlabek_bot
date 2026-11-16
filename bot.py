import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import Database
from handlers.business import business_router
from handlers.user import user_router

# Log tizimini sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SaqlabekBot")


async def periodic_cleanup_task(db: Database, interval_hours: int, retention_days: int) -> None:
    """
    Har interval_hours soatda bazadagi retention_days dan eski xabarlarni
    avtomatik tozalovchi fon vazifasi.
    """
    logger.info(
        f"Fon tozalash vazifasi boshlandi: har {interval_hours} soatda "
        f"{retention_days} kundan eski xabarlar tozalanadi."
    )
    while True:
        try:
            deleted_count = await db.delete_old_messages(retention_days)
            if deleted_count > 0:
                logger.info(f"Avtomatik tozalash yakunlandi: {deleted_count} ta eski xabar tozalandi.")
        except asyncio.CancelledError:
            logger.info("Fon tozalash vazifasi to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Fon tozalash vazifasida xatolik: {e}", exc_info=True)

        await asyncio.sleep(interval_hours * 3600)


async def main() -> None:
    """Botning asosiy kirish nuqtasi."""
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Konfiguratsiya xatosi: {e}")
        sys.exit(1)

    # Ma'lumotlar bazasini initsializatsiya qilish
    db = Database(config.DB_PATH)
    await db.init_db()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Database ob'ektini handlerlarga uzatish (dependency injection)
    dp["db"] = db

    # Routerlarni ulash
    dp.include_router(user_router)
    dp.include_router(business_router)

    # Qabul qilinadigan yangilanish turlarini avtomatik aniqlash
    allowed_updates = dp.resolve_used_update_types()
    logger.info(f"Qabul qilinadigan Telegram yangilanish turlari: {allowed_updates}")

    # Bot haqida ma'lumot olish
    bot_user = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_user.username} (ID: {bot_user.id})")

    # Fon tozalash vazifasini ishga tushirish
    cleanup_task = asyncio.create_task(
        periodic_cleanup_task(
            db=db,
            interval_hours=config.CLEANUP_INTERVAL_HOURS,
            retention_days=config.RETENTION_DAYS,
        )
    )

    try:
        # Pollingni barcha business va oddiy yangilanishlar bilan boshlash
        await dp.start_polling(
            bot,
            allowed_updates=allowed_updates,
            skip_updates=False,
        )
    finally:
        logger.info("Bot to'xtatilmoqda...")
        cleanup_task.cancel()
        await asyncio.gather(cleanup_task, return_exceptions=True)
        await bot.session.close()
        logger.info("Bot sessiyasi yopildi. Xayr!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")

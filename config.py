import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def str_to_bool(value: str | None, default: bool = False) -> bool:
    """Satrli qiymatni mantiqiy (bool) turga xavfsiz o'girish."""
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes", "y", "t", "on")


class Config:
    """Ilova sozlamalari klassi."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

    DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "saqlabek.db")).strip()

    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent").strip()

    NOTIFY_OWN_DELETED_MESSAGES: bool = str_to_bool(
        os.getenv("NOTIFY_OWN_DELETED_MESSAGES", "False"),
        default=False
    )

    RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30").strip() or 30)

    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24").strip() or 24)

    @classmethod
    def validate(cls) -> None:
        """Asosiy sozlamalar to'g'riligini tekshirish."""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            raise ValueError(
                "BOT_TOKEN topilmadi yoki noto'g'ri ko'rsatilgan! "
                ".env fayliga @BotFather bergan tokenni kiriting."
            )


config = Config()

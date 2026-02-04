import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/indie_fantrax")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    ACCESS_CODE: str = os.getenv("ACCESS_CODE", "music123")
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/London")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "sen0r1ta")


settings = Settings()

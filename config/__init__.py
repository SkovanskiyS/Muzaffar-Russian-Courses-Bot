from dotenv import load_dotenv
import os

class Settings:
    load_dotenv()

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ADMIN_IDS = os.getenv("ADMIN_IDS")

settings = Settings()
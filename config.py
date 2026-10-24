import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN is missing from environment variables!")
    raise ValueError("BOT_TOKEN is required to run the bot.")

OWNER_ID = int(os.getenv("OWNER_ID", 0))
DB_NAME = "superguard.db"

# config.py
from dotenv import load_dotenv
import os

TELEGRAM_BOT_TOKEN = '8058688084:AAG0LreV_E0vaQPqEW9QC9-TYRCDgp4lyp4'
ADMIN_ID = 123456789  # your Telegram user ID for order alerts


load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")



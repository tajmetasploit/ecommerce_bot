# handlers/start.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

main_menu = [
    ['🛍 Products', '🛒 Cart'],
    ['📞 Contact']
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\nWelcome to our store.\nChoose an option:",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

def register_start_handlers(app):
    app.add_handler(CommandHandler("start", start))

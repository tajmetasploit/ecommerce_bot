# bot.py
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.products import register_product_handlers
from handlers.cart import register_cart_handlers

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
     
    register_start_handlers(app)
    register_product_handlers(app)
    register_cart_handlers(app)
    register_cart_handlers(app)

    app.run_polling()

if __name__ == '__main__':
    main()

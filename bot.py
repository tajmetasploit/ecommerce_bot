import asyncio
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.products import register_product_handlers
from handlers.cart import register_cart_handlers
from database import connect_db, disconnect_db

async def main():
    await connect_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    register_start_handlers(app)
    register_product_handlers(app)
    register_cart_handlers(app)

    # Run polling until stopped (Ctrl+C etc)
    await app.run_polling()

    await disconnect_db()

if __name__ == '__main__':
    asyncio.run(main())

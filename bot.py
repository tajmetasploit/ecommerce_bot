from telegram.ext import ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.products import register_product_handlers
from handlers.cart import register_cart_handlers
from database import connect_db, disconnect_db, create_tables
import asyncio


async def on_startup(app):
    await connect_db()
    await create_tables()
    print("Database connected and tables created.")


async def on_shutdown(app):
    await disconnect_db()
    print("Database disconnected.")


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(on_startup).build()


    # Register handlers
    register_start_handlers(app)
    register_product_handlers(app)
    register_cart_handlers(app)

    # Add startup and shutdown callbacks
    app.post_init.append(on_startup)
    app.post_shutdown.append(on_shutdown)

    app.run_polling()


if __name__ == '__main__':
    main()

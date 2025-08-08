from telegram.ext import ApplicationBuilder
from config import TELEGRAM_BOT_TOKEN
from handlers.start import register_start_handlers
from handlers.products import register_product_handlers
from handlers.cart import register_cart_handlers
from database import connect_db, disconnect_db, create_tables


"""async def on_startup(app):
    await connect_db()
    await create_tables()
    print("✅ Database connected and tables created.")


async def on_shutdown(app):
    await disconnect_db()
    print("❌ Database disconnected.")
"""

async def on_startup(app):
    await connect_db()

async def on_shutdown(app):
    await disconnect_db()

def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(on_startup)        # set startup callback here
        .post_shutdown(on_shutdown)  # set shutdown callback here
        .build()
    )

    # Register handlers
    register_start_handlers(app)
    register_product_handlers(app)
    register_cart_handlers(app)

    app.run_polling()


if __name__ == '__main__':
    main()


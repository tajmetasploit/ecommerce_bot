import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from database import add_to_cart  # async function now!
from database import get_all_products
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes


# Load products once
with open('data/products.json', 'r') as f:
    PRODUCTS = json.load(f)


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = await get_all_products()

    if not products:
        await update.message.reply_text("No products available right now.")
        return

    for product in products:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("View Details", callback_data=f"product_{product['id']}")]
        ])
        try:
            await update.message.reply_photo(
                photo=product['photo'],  # must be a valid URL
                caption=f"🛍 {product['name']}\n💵 ${product['price']}",
                reply_markup=keyboard
            )
        except Exception as e:
            await update.message.reply_text(
                f"{product['name']} - unable to load image.\n💵 ${product['price']}"
            )
            print(f"Error sending photo for product {product['id']} ({product['photo']}): {e}")

async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data.replace("product_", "")

    products = await get_all_products()
    product = next((p for p in products if str(p["id"]) == product_id), None)

    if product:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Add to Cart 🛒", callback_data=f"addcart_{product['id']}")]
        ])

        await query.message.reply_text(
            f"📦 *{product['name']}*\n\n{product['description']}\n\n💵 *${product['price']}*",
            parse_mode='Markdown',
            reply_markup=keyboard
        )


async def add_to_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    product_id = query.data.replace("addcart_", "")

    # Call async DB function to add to cart
    await add_to_cart(user_id, int(product_id), quantity=1)

    await query.answer("Added to cart ✅", show_alert=True)

def register_product_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛍 Products"), show_products))
    app.add_handler(CallbackQueryHandler(show_product_details, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(add_to_cart_callback, pattern="^addcart_"))

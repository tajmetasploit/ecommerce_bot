# handlers/products.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import add_to_cart

# Load products once
with open('data/products.json', 'r') as f:
    PRODUCTS = json.load(f)

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for product in PRODUCTS:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("View Details", callback_data=f"product_{product['id']}")]
        ])
        await update.message.reply_photo(
            photo=product['photo'],
            caption=f"🛍 {product['name']}\n💵 ${product['price']}",
            reply_markup=keyboard
        )


async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data.replace("product_", "")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)

    if product:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Add to Cart 🛒", callback_data=f"addcart_{product['id']}")]
        ])

        await query.message.reply_text(
            f"📦 *{product['name']}*\n\n{product['description']}\n\n💵 *${product['price']}*",
            parse_mode='Markdown',
            reply_markup=keyboard
        )


def register_product_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛍 Products"), show_products))
    app.add_handler(CallbackQueryHandler(show_product_details, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(add_to_cart_callback, pattern="^addcart_"))


async def add_to_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    product_id = query.data.replace("addcart_", "")
    add_to_cart(user_id, product_id)
    await query.answer("Added to cart ✅", show_alert=True)

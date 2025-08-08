from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import stripe
import os
from database import get_cart, clear_cart, remove_from_cart_db  # async DB funcs
import json
from telegram import Update
from telegram.ext import ContextTypes

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Set your Stripe secret key in env variable

with open('data/products.json', 'r') as f:
    PRODUCTS = json.load(f)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = await get_cart(user_id)  # async

    if not cart:
        await update.message.reply_text("Your cart is empty 🛒")
        return

    text = "🛒 Your Cart:\n\n"
    total = 0
    buttons = []

    for item in cart:
        # item = {'product_id': int, 'quantity': int}
        product = next((p for p in PRODUCTS if str(p["id"]) == str(item['product_id'])), None)
        if product:
            line = f"{product['name']} — ${product['price']} x {item['quantity']}\n"
            text += line
            total += product['price'] * item['quantity']
            buttons.append([InlineKeyboardButton(f"Remove {product['name']}", callback_data=f"remove_{product['id']}")])

    text += f"\nTotal: ${total:.2f}"

    keyboard = InlineKeyboardMarkup(
        buttons +
        [
            [InlineKeyboardButton("Clear Cart", callback_data="clear_cart")],
            [InlineKeyboardButton("Place Order", callback_data="place_order")]
        ]
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        # If callback query triggered
        await update.callback_query.message.edit_text(text, reply_markup=keyboard)

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    product_id = query.data.replace("remove_", "")

    await remove_from_cart_db(user_id, int(product_id))  # async DB call
    await query.answer("Removed from cart")

    # Refresh cart display
    await view_cart(update, context)

async def clear_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await clear_cart(user_id)  # async DB call
    await query.answer("Cart cleared")
    await query.message.edit_text("Your cart is now empty 🛒")

def register_cart_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛒 Cart"), view_cart))
    app.add_handler(CallbackQueryHandler(remove_from_cart, pattern="^remove_"))
    app.add_handler(CallbackQueryHandler(clear_cart_callback, pattern="^clear_cart"))
    app.add_handler(MessageHandler(filters.CONTACT, contact_received))


    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(place_order_start, pattern="^place_order$")],
        states={
            1: [MessageHandler(filters.CONTACT, contact_received)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)

async def place_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Implement logic for starting the order placement (e.g., confirm order, payment options)
    await query.message.reply_text("Order placement started! (Implement your flow here)")



async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    
    # For example, save the contact info or reply back:
    await update.message.reply_text(f"Thanks for sharing your contact: {contact.phone_number}")
    
    # Here you could store the contact info to DB or proceed with further flow


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from database import get_cart, clear_cart, remove_from_cart  # all async now
import json
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

with open('data/products.json', 'r') as f:
    PRODUCTS = json.load(f)


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = await get_cart(user_id)  # await DB

    if not cart:
        await update.message.reply_text("Your cart is empty 🛒")
        return

    text = "🛒 Your Cart:\n\n"
    total = 0
    buttons = []

    for product, quantity in cart:
        text += f"{product.name} x{quantity} — ${product.price * quantity:.2f}\n"
        total += product.price * quantity
        buttons.append([InlineKeyboardButton(f"Remove {product.name}", callback_data=f"remove_{product.id}")])

    text += f"\nTotal: ${total:.2f}"

    keyboard = InlineKeyboardMarkup(
        buttons +
        [[InlineKeyboardButton("Clear Cart", callback_data="clear_cart")],
         [InlineKeyboardButton("Place Order", callback_data="place_order")]]
    )
    await update.message.reply_text(text, reply_markup=keyboard)


async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    pid = int(query.data.replace("remove_", ""))
    await remove_from_cart(user_id, pid)  # remove from DB
    await query.answer("Removed from cart")
    await view_cart(update, context)


async def clear_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await clear_cart(user_id)  # clear in DB
    await query.answer("Cart cleared")
    await query.message.reply_text("Your cart is now empty 🛒")


def register_cart_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛒 Cart"), view_cart))
    app.add_handler(CallbackQueryHandler(remove_from_cart, pattern="^remove_"))
    app.add_handler(CallbackQueryHandler(clear_cart_callback, pattern="^clear_cart"))

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
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Share Phone Number", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await query.message.reply_text("Please share your phone number to confirm the order:", reply_markup=keyboard)
    return 1


async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    if not contact:
        await update.message.reply_text("Please share your contact using the button!")
        return 1

    user_id = user.id
    cart = await get_cart(user_id)

    line_items = []
    total_amount = 0
    for product, quantity in cart:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': product.name},
                'unit_amount': int(product.price * 100),
            },
            'quantity': quantity,
        })
        total_amount += product.price * quantity

    if not line_items:
        await update.message.reply_text("Your cart is empty, please add products first.")
        return ConversationHandler.END

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='https://yourdomain.com/success',  # your URL here
            cancel_url='https://yourdomain.com/cancel',    # your URL here
            customer_email=update.effective_user.email or None,
            metadata={
                'user_id': str(user_id),
                'contact_phone': contact.phone_number
            }
        )
    except Exception as e:
        await update.message.reply_text(f"Payment error: {e}")
        return ConversationHandler.END

    await clear_cart(user_id)

    await update.message.reply_text(
        f"Thank you! Your order total is ${total_amount:.2f}.\n"
        f"Please pay using this link:\n{checkout_session.url}"
    )

    return ConversationHandler.END

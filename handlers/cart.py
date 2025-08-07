# handlers/cart.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from database import get_cart, clear_cart
import json
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Set your secret key in env variable

with open('data/products.json', 'r') as f:
    PRODUCTS = json.load(f)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(user_id)

    if not cart:
        await update.message.reply_text("Your cart is empty 🛒")
        return

    text = "🛒 Your Cart:\n\n"
    total = 0
    buttons = []

    for pid in cart:
        product = next((p for p in PRODUCTS if p["id"] == pid), None)
        if product:
            text += f"{product['name']} — ${product['price']}\n"
            total += product['price']
            buttons.append([InlineKeyboardButton(f"Remove {product['name']}", callback_data=f"remove_{pid}")])

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
    pid = query.data.replace("remove_", "")
    cart = get_cart(user_id)
    if pid in cart:
        cart.remove(pid)
    await query.answer("Removed from cart")
    await view_cart(update, context)  # update cart display

async def clear_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    clear_cart(user_id)
    await query.answer("Cart cleared")
    await update.message.reply_text("Your cart is now empty 🛒")


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

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🛒 Cart"), view_cart))
    app.add_handler(CallbackQueryHandler(remove_from_cart, pattern="^remove_"))
    app.add_handler(CallbackQueryHandler(clear_cart_callback, pattern="^clear_cart"))
    app.add_handler(conv_handler)



async def place_order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Ask user to share contact info (phone)
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Share Phone Number", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await query.message.reply_text("Please share your phone number to confirm the order:", reply_markup=keyboard)
    return 1  # State 1 = waiting contact


async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    if not contact:
        await update.message.reply_text("Please share your contact using the button!")
        return 1

    user_id = user.id
    cart = get_cart(user_id)

    # Prepare line items for Stripe
    line_items = []
    total_amount = 0
    for pid in cart:
        product = next((p for p in PRODUCTS if p["id"] == pid), None)
        if product:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': product['name']},
                    'unit_amount': int(product['price'] * 100),  # amount in cents
                },
                'quantity': 1,
            })
            total_amount += product['price']

    if not line_items:
        await update.message.reply_text("Your cart is empty, please add products first.")
        return ConversationHandler.END

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='https://yourdomain.com/success',  # replace with your URL
            cancel_url='https://yourdomain.com/cancel',    # replace with your URL
            customer_email=update.effective_user.email or None,
            metadata={
                'user_id': str(user_id),
                'contact_phone': contact.phone_number
            }
        )
    except Exception as e:
        await update.message.reply_text(f"Payment error: {e}")
        return ConversationHandler.END

    clear_cart(user_id)

    await update.message.reply_text(
        f"Thank you! Your order total is ${total_amount:.2f}.\n"
        f"Please pay using this link:\n{checkout_session.url}"
    )

    return ConversationHandler.END

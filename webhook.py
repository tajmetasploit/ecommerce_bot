import os
import stripe
from flask import Flask, request, jsonify
from telegram import Bot

app = Flask(__name__)

# Set your secret keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

stripe.api_key = STRIPE_SECRET_KEY
bot = Bot(token='8058688084:AAG0LreV_E0vaQPqEW9QC9-TYRCDgp4lyp4')

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        return jsonify({"error": "Invalid signature"}), 400

    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        telegram_user_id = session['metadata'].get('user_id')

        message = (
            f"✅ Payment received from user ID {telegram_user_id}!\n"
            f"Amount: ${session['amount_total'] / 100:.2f}"
        )

        try:
            bot.send_message(chat_id=int(telegram_user_id), text="🎉 Your payment was successful! Thank you!")
            bot.send_message(chat_id=123456789, text=message)  # Optional: notify yourself
        except Exception as e:
            print("Failed to send Telegram message:", e)

    return jsonify(success=True)

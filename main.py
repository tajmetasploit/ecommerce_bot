import os
import stripe
from flask import Flask, request, jsonify
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()  # load .env file in Replit

app = Flask(__name__)

# Load keys from environment
STRIPE_SECRET_KEY = os.environ["STRIPE_SECRET_KEY"]
STRIPE_WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = os.environ.get("ADMIN_ID")  # Optional

stripe.api_key = STRIPE_SECRET_KEY
bot = Bot(token=TELEGRAM_BOT_TOKEN)

@app.route("/")
def index():
    return "Stripe Webhook Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")

        # Send messages
        bot.send_message(chat_id=user_id, text="🎉 Your payment was successful!")
        if ADMIN_ID:
            bot.send_message(chat_id=ADMIN_ID, text=f"✅ Payment received from user {user_id}.")

    return jsonify({"status": "success"})

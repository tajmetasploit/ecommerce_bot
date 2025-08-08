# database.py
import os
from databases import Database

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:BIePlnsvfFRTrKvtATsiPzuqoGKTFZHj@metro.proxy.rlwy.net:23356/railway"
)

database = Database(DATABASE_URL)

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    photo_url TEXT,
    stock INTEGER DEFAULT 0
);
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL
);
"""

CREATE_CART_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1
);
"""

CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status TEXT DEFAULT 'pending',
    total_amount NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def create_tables():
    await database.execute(CREATE_PRODUCTS_TABLE)
    await database.execute(CREATE_USERS_TABLE)
    await database.execute(CREATE_CART_ITEMS_TABLE)
    await database.execute(CREATE_ORDERS_TABLE)

async def connect_db():
    await database.connect()
    await create_tables()

async def disconnect_db():
    await database.disconnect()

async def get_or_create_user(telegram_id: int) -> int:
    query = "SELECT id FROM users WHERE telegram_id = :telegram_id"
    user = await database.fetch_one(query=query, values={"telegram_id": telegram_id})
    if user:
        return user["id"]
    else:
        insert_query = "INSERT INTO users (telegram_id) VALUES (:telegram_id) RETURNING id"
        user_id = await database.fetch_val(insert_query, values={"telegram_id": telegram_id})
        return user_id

async def add_to_cart(telegram_id: int, product_id: int):
    user_id = await get_or_create_user(telegram_id)
    query = """
        SELECT id, quantity FROM cart_items
        WHERE user_id = :user_id AND product_id = :product_id
    """
    item = await database.fetch_one(query=query, values={"user_id": user_id, "product_id": product_id})

    if item:
        update_query = """
            UPDATE cart_items SET quantity = quantity + 1 WHERE id = :id
        """
        await database.execute(update_query, values={"id": item["id"]})
    else:
        insert_query = """
            INSERT INTO cart_items (user_id, product_id, quantity) VALUES (:user_id, :product_id, 1)
        """
        await database.execute(insert_query, values={"user_id": user_id, "product_id": product_id})

async def get_cart(telegram_id: int):
    user_id = await get_or_create_user(telegram_id)
    query = """
        SELECT p.id, p.name, p.price, p.photo_url, ci.quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = :user_id
    """
    rows = await database.fetch_all(query=query, values={"user_id": user_id})
    return rows

async def clear_cart(telegram_id: int):
    user_id = await get_or_create_user(telegram_id)
    query = "DELETE FROM cart_items WHERE user_id = :user_id"
    await database.execute(query=query, values={"user_id": user_id})

async def remove_cart_item(telegram_id: int, product_id: int):
    user_id = await get_or_create_user(telegram_id)
    # First check quantity
    query = "SELECT quantity, id FROM cart_items WHERE user_id = :user_id AND product_id = :product_id"
    item = await database.fetch_one(query=query, values={"user_id": user_id, "product_id": product_id})

    if item:
        if item["quantity"] > 1:
            update_query = "UPDATE cart_items SET quantity = quantity - 1 WHERE id = :id"
            await database.execute(update_query, values={"id": item["id"]})
        else:
            delete_query = "DELETE FROM cart_items WHERE id = :id"
            await database.execute(delete_query, values={"id": item["id"]})

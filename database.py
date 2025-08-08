from databases import Database
import asyncpg

DATABASE_URL = "postgresql://postgres:BIePlnsvfFRTrKvtATsiPzuqoGKTFZHj@metro.proxy.rlwy.net:23356/railway"
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
    if not database.is_connected:
        await database.connect()

async def disconnect_db():
    if database.is_connected:
        await database.disconnect()


async def add_user_if_not_exists(telegram_id: int):
    """Add user to users table if not exists"""
    query = "INSERT INTO users (telegram_id) VALUES (:telegram_id) ON CONFLICT (telegram_id) DO NOTHING"
    await database.execute(query, values={"telegram_id": telegram_id})


async def add_to_cart(user_telegram_id: int, product_id: int, quantity: int = 1):
    await connect_db()
    # Ensure user exists
    await add_user_if_not_exists(user_telegram_id)

    # Get user internal id
    query_user = "SELECT id FROM users WHERE telegram_id = :telegram_id"
    user = await database.fetch_one(query_user, values={"telegram_id": user_telegram_id})
    user_id = user["id"]

    # Check if product already in cart
    query_check = """
    SELECT id, quantity FROM cart_items
    WHERE user_id = :user_id AND product_id = :product_id
    """
    cart_item = await database.fetch_one(query_check, values={"user_id": user_id, "product_id": product_id})

    if cart_item:
        # Update quantity
        new_quantity = cart_item["quantity"] + quantity
        query_update = """
        UPDATE cart_items SET quantity = :quantity WHERE id = :id
        """
        await database.execute(query_update, values={"quantity": new_quantity, "id": cart_item["id"]})
    else:
        # Insert new item
        query_insert = """
        INSERT INTO cart_items (user_id, product_id, quantity) VALUES (:user_id, :product_id, :quantity)
        """
        await database.execute(query_insert, values={"user_id": user_id, "product_id": product_id, "quantity": quantity})


async def get_cart(user_telegram_id: int):
    await connect_db()
    query_user = "SELECT id FROM users WHERE telegram_id = :telegram_id"
    user = await database.fetch_one(query_user, values={"telegram_id": user_telegram_id})
    if not user:
        return []

    user_id = user["id"]

    query = """
    SELECT product_id, quantity FROM cart_items
    WHERE user_id = :user_id
    """
    rows = await database.fetch_all(query, values={"user_id": user_id})
    return [{"product_id": row["product_id"], "quantity": row["quantity"]} for row in rows]


async def remove_from_cart(user_telegram_id: int, product_id: int):
    await connect_db()
    query_user = "SELECT id FROM users WHERE telegram_id = :telegram_id"
    user = await database.fetch_one(query_user, values={"telegram_id": user_telegram_id})
    if not user:
        return
    user_id = user["id"]

    query = """
    DELETE FROM cart_items
    WHERE user_id = :user_id AND product_id = :product_id
    """
    await database.execute(query, values={"user_id": user_id, "product_id": product_id})


async def clear_cart(user_telegram_id: int):
    await connect_db()
    query_user = "SELECT id FROM users WHERE telegram_id = :telegram_id"
    user = await database.fetch_one(query_user, values={"telegram_id": user_telegram_id})
    if not user:
        return
    user_id = user["id"]

    query = """
    DELETE FROM cart_items WHERE user_id = :user_id
    """
    await database.execute(query, values={"user_id": user_id})

async def remove_from_cart_db(user_id: int, product_id: int):
    query = """
    DELETE FROM cart_items
    WHERE user_id = (SELECT id FROM users WHERE telegram_id = $1)
      AND product_id = $2
    """
    await database.execute(query, user_id, int(product_id))


async def get_all_products():
    conn = await connect_db()
    rows = await conn.fetch("SELECT id, name, description, price, photo_url, stock FROM products")
    await conn.close()

    products = []
    for row in rows:
        products.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "price": row["price"],
            "photo": row["photo_url"],  # map DB column to 'photo' for Telegram
            "stock": row["stock"]
        })
    return products

import databases
import sqlalchemy

DATABASE_URL = "postgresql://postgres:BIePlnsvfFRTrKvtATsiPzuqoGKTFZHj@metro.proxy.rlwy.net:23356/railway"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define tables with SQLAlchemy for better integration (optional but recommended)
products = sqlalchemy.Table(
    "products", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.Text),
    sqlalchemy.Column("price", sqlalchemy.Numeric(10, 2), nullable=False),
    sqlalchemy.Column("photo_url", sqlalchemy.String),
    sqlalchemy.Column("stock", sqlalchemy.Integer, default=0),
)

users = sqlalchemy.Table(
    "users", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("telegram_id", sqlalchemy.BigInteger, unique=True, nullable=False),
)

cart_items = sqlalchemy.Table(
    "cart_items", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE")),
    sqlalchemy.Column("product_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id", ondelete="CASCADE")),
    sqlalchemy.Column("quantity", sqlalchemy.Integer, default=1),
)

orders = sqlalchemy.Table(
    "orders", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("status", sqlalchemy.String, default="pending"),
    sqlalchemy.Column("total_amount", sqlalchemy.Numeric(10, 2)),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)

# Create an engine for table creation (sync)
engine = sqlalchemy.create_engine(DATABASE_URL)

def create_tables():
    metadata.create_all(engine)

async def connect_db():
    await database.connect()

async def disconnect_db():
    await database.disconnect()

# Async cart functions example

async def add_to_cart(user_telegram_id: int, product_id: int, quantity: int = 1):
    # Ensure user exists or create user
    query_user = users.select().where(users.c.telegram_id == user_telegram_id)
    user = await database.fetch_one(query_user)
    if not user:
        query_insert = users.insert().values(telegram_id=user_telegram_id)
        user_id = await database.execute(query_insert)
    else:
        user_id = user.id

    # Check if cart item exists
    query_cart = cart_items.select().where(
        (cart_items.c.user_id == user_id) & (cart_items.c.product_id == product_id)
    )
    cart_item = await database.fetch_one(query_cart)
    if cart_item:
        # Update quantity
        query_update = cart_items.update().where(cart_items.c.id == cart_item.id).values(
            quantity=cart_item.quantity + quantity
        )
        await database.execute(query_update)
    else:
        # Insert new cart item
        query_insert = cart_items.insert().values(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        await database.execute(query_insert)

async def get_cart(user_telegram_id: int):
    query_user = users.select().where(users.c.telegram_id == user_telegram_id)
    user = await database.fetch_one(query_user)
    if not user:
        return []

    query = (
        cart_items.join(products, cart_items.c.product_id == products.c.id)
        .select()
        .with_only_columns(
            [products.c.id, products.c.name, products.c.price, cart_items.c.quantity]
        )
        .where(cart_items.c.user_id == user.id)
    )
    # Above is SQLAlchemy Core select statement, databases doesn't support join().select() directly
    # So let's do it with raw SQL for simplicity:

    sql = """
    SELECT p.id, p.name, p.price, ci.quantity
    FROM cart_items ci
    JOIN products p ON ci.product_id = p.id
    WHERE ci.user_id = :user_id
    """

    rows = await database.fetch_all(sql, values={"user_id": user.id})
    return rows

async def clear_cart(user_telegram_id: int):
    query_user = users.select().where(users.c.telegram_id == user_telegram_id)
    user = await database.fetch_one(query_user)
    if user:
        query_delete = cart_items.delete().where(cart_items.c.user_id == user.id)
        await database.execute(query_delete)

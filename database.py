import os
from tortoise import Tortoise, fields, models, run_async

DATABASE_URL = os.getenv("DATABASE_URL")

# Define your models here or in a separate models.py file

class Product(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    price = fields.FloatField()
    photo_url = fields.CharField(max_length=255, null=True)

class CartItem(models.Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    product = fields.ForeignKeyField('models.Product', related_name='cart_items')
    quantity = fields.IntField(default=1)

async def init_db():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['database']}  # adjust if models in separate file
    )
    await Tortoise.generate_schemas()

# Cart operations using database

async def add_to_cart(user_id: int, product_id: int):
    # Check if the product is already in cart
    existing = await CartItem.filter(user_id=user_id, product_id=product_id).first()
    if existing:
        existing.quantity += 1
        await existing.save()
    else:
        await CartItem.create(user_id=user_id, product_id=product_id, quantity=1)

async def get_cart(user_id: int):
    items = await CartItem.filter(user_id=user_id).prefetch_related('product')
    return [(item.product, item.quantity) for item in items]

async def clear_cart(user_id: int):
    await CartItem.filter(user_id=user_id).delete()

# To test DB connection & models
if __name__ == "__main__":
    async def run():
        await init_db()
        # Add test product or cart items here if you want
    run_async(run())

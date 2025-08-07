# database.py
user_carts = {}

def add_to_cart(user_id, product_id):
    if user_id not in user_carts:
        user_carts[user_id] = []
    user_carts[user_id].append(product_id)

def get_cart(user_id):
    return user_carts.get(user_id, [])

def clear_cart(user_id):
    if user_id in user_carts:
        user_carts[user_id] = []

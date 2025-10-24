def update_cart(context, product=None, operation="add", product_id=None):
    cart = context.user_data.get("cart", [])
    cart_total = context.user_data.get("cart_total", 0)
    
    if operation == "add" and product:
        cart.append(product)
        cart_total += product["price"]
    elif operation == "remove" and product_id is not None:
        if 0 <= product_id < len(cart):
            removed_product = cart.pop(product_id)
            cart_total -= removed_product["price"]
    elif operation == "clear":
        cart = []
        cart_total = 0
    
    context.user_data["cart"] = cart
    context.user_data["cart_total"] = cart_total
    return cart_total

async def show_cart(update, context):
    cart = context.user_data.get("cart", [])
    cart_total = context.user_data.get("cart_total", 0)
    
    if not cart:
        await update.message.reply_text("Корзина пуста")
        return
    
    cart_text = "Ваша корзина:\n\n"
    for i, product in enumerate(cart, 1):
        cart_text += f"{i}. {product['name']} - {product['price']} руб.\n"
    
    cart_text += f"\nИтог: {cart_total} руб."
    
    cart_text += "\n\nКоманды для управления корзиной:\n"
    cart_text += "• 'убрать 1' - удалить товар №1\n"
    cart_text += "• 'очистить корзину' - удалить все товары\n"
    cart_text += "• 'заказать' - оформить заказ\n"
    cart_text += "• 'назад' - продолжить покупки\n"
    cart_text += "• 'поговорить' - пообщаться со мной"
    
    await update.message.reply_text(cart_text)

async def handle_cart_commands(update, context, current_state):
    user_message = update.message.text.lower().strip()
    
    if user_message == "корзина":
        await show_cart(update, context)
        return current_state
    
    elif user_message.startswith("убрать"):
        try:
            parts = user_message.split()
            if len(parts) >= 2:
                product_num = int(parts[1]) - 1
                cart = context.user_data.get("cart", [])
                
                if 0 <= product_num < len(cart):
                    removed_product = cart[product_num]
                    update_cart(context, operation="remove", product_id=product_num)
                    
                    await update.message.reply_text(
                        f"Товар '{removed_product['name']}' удален из корзины\n"
                        f"Корзина: {context.user_data.get('cart_total', 0)} руб."
                    )
                    await show_cart(update, context)
                else:
                    await update.message.reply_text("Неверный номер товара")
            else:
                await update.message.reply_text("Используйте: убрать <номер товара>")
        except ValueError:
            await update.message.reply_text("Используйте: убрать <номер товара>")
        
        return current_state
    
    elif user_message in ["очистить корзину", "очистить"]:
        update_cart(context, operation="clear")
        await update.message.reply_text("Корзина очищена")
        return current_state
    
    elif user_message == "заказать":
        cart = context.user_data.get("cart", [])
        if not cart:
            await update.message.reply_text("Корзина пуста. Добавьте товары перед заказом.")
            return current_state
        
        await update.message.reply_text("Напишите адрес доставки:")
        from config import GET_ADDRESS
        return GET_ADDRESS
    
    return None
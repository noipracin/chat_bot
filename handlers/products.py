import os
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from config import CHOOSE_CATEGORY, VIEW_PRODUCTS, PRODUCT_DETAIL, MAIN_MENU, CHATTING
from data.products import PRODUCT_CATEGORIES
from utils.helpers import contains_blacklisted_words, detect_intent
from utils.validation import handle_cart_commands, update_cart

logger = logging.getLogger(__name__)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = context.user_data.get("user_name", "")
    
    cart_total = context.user_data.get("cart_total", 0)
    cart_info = f" (в корзине: {cart_total} руб.)" if cart_total > 0 else ""
    
    categories_text = (
        f"Хорошо, {user_name}, выбирай категорию{cart_info}:\n\n"
        "1. Карандаши, ручки и письменные принадлежности\n"
        "2. Для рисования и творчества\n" 
        "3. Бумага, тетради и блокноты\n"
        "4. Иная продукция и аксессуары\n\n"
        "Напиши номер категории или 'назад' для возврата:"
    )
    
    await update.message.reply_text(categories_text)

async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE, category_key: str):
    category = PRODUCT_CATEGORIES.get(category_key)
    if not category:
        await update.message.reply_text("Категория не найдена")
        return
    
    # Отправляем фотографии товаров категории
    media_group = []
    for i in range(1, len(category["products"]) + 1):
        product_key = str(i)
        product = category["products"].get(product_key)
        if product and os.path.exists(product["image"]):
            try:
                with open(product["image"], 'rb') as photo:
                    if len(media_group) == 0:
                        # Первое фото с подписью
                        caption = f"{category['name']}\n\n{i}. {product['name']} - {product['price']} руб."
                        media_group.append(InputMediaPhoto(media=photo, caption=caption))
                    else:
                        media_group.append(InputMediaPhoto(media=photo))
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения {product['image']}: {e}")
    
    if media_group:
        try:
            await update.message.reply_media_group(media=media_group)
        except Exception as e:
            logger.error(f"Ошибка отправки медиагруппы: {e}")
    
    # Текстовое сообщение со списком товаров
    products_text = f"{category['name']}\n\n"
    
    for i in range(1, len(category["products"]) + 1):
        product_key = str(i)
        product = category["products"].get(product_key)
        if product:
            products_text += f"{i}. **{product['name']}** - {product['price']} руб.\n"
            products_text += f"   [Ссылка на товар]({product['link']})\n\n"
    
    cart_total = context.user_data.get("cart_total", 0)
    cart_info = f"В корзине: {cart_total} руб.\n\n" if cart_total > 0 else "\n"
    
    products_text += (
        f"{cart_info}"
        "Команды:\n"
        "• Напиши номер товара для просмотра деталей\n"
        "• 'назад' - вернуться к категориям\n"
        "• 'корзина' - посмотреть корзину\n"
        "• 'поговорить' - пообщаться со мной"
    )
    
    await update.message.reply_text(products_text, parse_mode='Markdown')

async def choose_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.strip()
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу общаться с использованием таких слов. "
            "Давай вернемся к выбору товаров!"
        )
        await show_categories(update, context)
        return CHOOSE_CATEGORY
    
    cart_state = await handle_cart_commands(update, context, CHOOSE_CATEGORY)
    if cart_state is not None:
        return cart_state
    
    if user_message.lower() == "поговорить":
        await update.message.reply_text(
            "Конечно, отвлечемся от покупок! Как у тебя дела?"
        )
        return CHATTING
    
    if user_message in PRODUCT_CATEGORIES:
        context.user_data["current_category"] = user_message
        await show_category_products(update, context, user_message)
        return VIEW_PRODUCTS
    elif user_message.lower() in ["назад", "вернуться"]:
        await update.message.reply_text(
            "Возвращаемся в главное меню!\n\n"
            "Что выберешь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n"
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU
    else:
        await update.message.reply_text("Пожалуйста, выбери номер категории от 1 до 4 или напиши 'назад':")
        return CHOOSE_CATEGORY

async def view_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.strip().lower()
    current_category = context.user_data.get("current_category")
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу общаться с использованием таких слов. "
            "Давай продолжим выбирать товары!"
        )
        await show_category_products(update, context, current_category)
        return VIEW_PRODUCTS
    
    cart_state = await handle_cart_commands(update, context, VIEW_PRODUCTS)
    if cart_state is not None:
        return cart_state
    
    if user_message == "поговорить":
        await update.message.reply_text(
            "Отлично! Немного отдохнем от покупок. Как твои дела?"
        )
        return CHATTING
    
    if user_message in ["назад", "вернуться"]:
        await show_categories(update, context)
        return CHOOSE_CATEGORY
    
    try:
        product_number = int(user_message)
        if 1 <= product_number <= len(PRODUCT_CATEGORIES[current_category]["products"]):
            await show_product_card(update, context, current_category, str(product_number))
            return PRODUCT_DETAIL
        else:
            await update.message.reply_text("Неверный номер товара. Попробуй еще раз:")
            return VIEW_PRODUCTS
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, выбери номер товара или используй команды:\n"
            "• 'назад' - вернуться к категориям\n"
            "• 'корзина' - посмотреть корзину\n"
            "• 'поговорить' - пообщаться со мной"
        )
        return VIEW_PRODUCTS

async def show_product_card(update: Update, context: ContextTypes.DEFAULT_TYPE, category_key: str, product_key: str):
    category = PRODUCT_CATEGORIES.get(category_key)
    if not category:
        await update.message.reply_text("Категория не найдена")
        return
    
    product = category["products"].get(product_key)
    if not product:
        await update.message.reply_text("Товар не найден")
        return
    
    product_text = (
        f"**{product['name']}**\n\n"
        f"**Цена:** {product['price']} руб.\n"
        f"**Ссылка на товар:** [Перейти к товару]({product['link']})\n\n"
        f"Чтобы добавить товар в корзину, напишите 'добавить'\n"
        f"Чтобы вернуться к списку товаров, напишите 'назад'"
    )
    
    try:
        if os.path.exists(product["image"]):
            with open(product["image"], 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=product_text,
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(product_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        await update.message.reply_text(product_text, parse_mode='Markdown')
    
    context.user_data["current_product"] = {
        "category": category_key,
        "product": product_key,
        "product_data": product
    }

async def product_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.strip().lower()
    current_product = context.user_data.get("current_product")
    
    if not current_product:
        await update.message.reply_text("Ошибка: информация о товаре не найдена")
        return VIEW_PRODUCTS
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу общаться с использованием таких слов. "
            "Давай продолжим выбирать товары!"
        )
        await show_product_card(update, context, current_product["category"], current_product["product"])
        return PRODUCT_DETAIL
    
    cart_state = await handle_cart_commands(update, context, PRODUCT_DETAIL)
    if cart_state is not None:
        return cart_state
    
    if user_message == "поговорить":
        await update.message.reply_text(
            "Отлично! Немного отдохнем от покупок. Как твои дела?"
        )
        return CHATTING
    
    if user_message in ["назад", "вернуться"]:
        await show_category_products(update, context, current_product["category"])
        return VIEW_PRODUCTS
    
    if user_message == "добавить":
        product_data = current_product["product_data"]
        cart_total = update_cart(context, product_data, "add")
        
        await update.message.reply_text(
            f"Товар '{product_data['name']}' добавлен в корзину\n"
            f"Сумма в корзине: {cart_total} руб.\n\n"
            f"Хочешь продолжить покупки или перейти к оформлению заказа?"
        )
        
        await update.message.reply_text(
            "Что дальше?\n"
            "• 'продолжить' - вернуться к списку товаров\n"
            "• 'корзина' - посмотреть корзину\n"
            "• 'заказать' - оформить заказ\n"
            "• 'поговорить' - пообщаться со мной"
        )
        return PRODUCT_DETAIL
    
    if user_message == "продолжить":
        await show_category_products(update, context, current_product["category"])
        return VIEW_PRODUCTS
    
    await update.message.reply_text(
        "Не понял команду. Доступные команды:\n"
        "• 'добавить' - добавить товар в корзину\n"
        "• 'назад' - вернуться к списку товаров\n"
        "• 'корзина' - посмотреть корзину\n"
        "• 'поговорить' - пообщаться со мной"
    )
    return PRODUCT_DETAIL
import random
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import GET_NAME, MAIN_MENU, CHATTING, JOKE, CHOOSE_CATEGORY
from utils.helpers import (
    contains_blacklisted_words, 
    extract_name_from_text, 
    detect_intent,
    get_chat_response
)
from utils.validation import handle_cart_commands
from data.content import JOKES

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "cart" not in context.user_data:
        context.user_data["cart"] = []
        context.user_data["cart_total"] = 0
    
    await update.message.reply_text(
        "Привет! Меня зовут Рональд и я являюсь ботом канцтоваров.\n"
        "Как я могу к тебе обращаться?"
    )
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    
    if contains_blacklisted_words(user_input):
        await update.message.reply_text(
            "Извините, но я не могу принять такое имя. "
            "Пожалуйста, представьтесь еще раз нормальным образом."
        )
        return GET_NAME
    
    user_name = extract_name_from_text(user_input)
    
    if not user_name:
        await update.message.reply_text(
            "Не удалось понять ваше имя. Пожалуйста, представьтесь еще раз "
            "(например: 'Алексей' или 'Меня зовут Алексей'):"
        )
        return GET_NAME
    
    context.user_data["user_name"] = user_name
    context.user_data["conversation_history"] = []
    
    await update.message.reply_text(
        f"Приятно познакомиться, {user_name}! 😊\n\n"
        "Вот что я умею:\n"
        "1. Поговорить с тобой по душам\n"
        "2. Рассказать смешную шутку\n"
        "3. Помочь с выбором канцелярии\n\n"
        "Что выберешь? Просто напиши номер или название функции!"
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    user_name = context.user_data.get("user_name", "")
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу общаться с использованием таких слов. "
            "Давай поговорим о чем-то приятном!"
        )
        return MAIN_MENU
    
    cart_state = await handle_cart_commands(update, context, MAIN_MENU)
    if cart_state is not None:
        return cart_state
    
    intent = detect_intent(user_message)
    
    if intent == "поговорить":
        context.user_data["conversation_history"] = []
        await update.message.reply_text(
            "Отлично! Давай пообщаемся! Можешь рассказать мне о чем угодно - "
            "о своем дне, планах, мыслях, или просто задать вопрос! 😊\n\n"
            "Если захочешь закончить диалог, напиши 'давай закончим'."
        )
        return CHATTING
        
    elif intent == "шутка":
        context.user_data["used_jokes"] = []
        context.user_data["all_jokes"] = JOKES.copy()
        
        await update.message.reply_text("Хорошо, попробую поднять тебе настроение! 😄")
        await tell_joke(update, context)
        return JOKE
        
    elif intent == "канцелярия":
        await show_categories(update, context)
        return CHOOSE_CATEGORY
        
    else:
        await update.message.reply_text(
            f"{user_name}, я не совсем понял. Выбери одну из функций:\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n"
            "3. Помочь с выбором канцелярии\n\n"
            "Также ты можешь написать 'корзина' для просмотра корзины"
        )
        return MAIN_MENU

async def tell_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    used_jokes = context.user_data.get("used_jokes", [])
    all_jokes = context.user_data.get("all_jokes", [])
    
    available_jokes = [j for j in all_jokes if j not in used_jokes]
    
    if available_jokes:
        joke = random.choice(available_jokes)
        used_jokes.append(joke)
        context.user_data["used_jokes"] = used_jokes
        
        await update.message.reply_text(joke)
        await update.message.reply_text("Хочешь еще шутку? 😄 (да/нет)")
    else:
        await update.message.reply_text("Прости, у меня закончились шутки! 😅")
        await update.message.reply_text(
            "Что ещё хочешь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n" 
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU

async def joke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.lower()
    user_name = context.user_data.get("user_name", "")
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу общаться с использованием таких слов. "
            "Давай вернемся к чему-то приятному!"
        )
        await update.message.reply_text("Хочешь еще шутку? (да/нет)")
        return JOKE
    
    cart_state = await handle_cart_commands(update, context, JOKE)
    if cart_state is not None:
        return cart_state
    
    if user_message == "поговорить":
        await update.message.reply_text(
            "Конечно! Шутки - это весело, но поговорить тоже здорово! Как твои дела?"
        )
        return CHATTING
    
    intent = detect_intent(user_message)
    
    if intent == "да":
        await tell_joke(update, context)
        return JOKE
    elif intent == "нет":
        await update.message.reply_text("Надеюсь, я поднял тебе настроение! 😊")
        await update.message.reply_text(
            "Что ещё хочешь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n" 
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU
    else:
        await update.message.reply_text("Не понял, хочешь еще шутку? (да/нет)")
        return JOKE

async def chatting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    user_name = context.user_data.get("user_name", "")
    
    if contains_blacklisted_words(user_message):
        await update.message.reply_text(
            "Извини, но я не могу продолжать разговор с такими словами. "
            "Давай поговорим о чем-то хорошем!"
        )
        return CHATTING
    
    cart_state = await handle_cart_commands(update, context, CHATTING)
    if cart_state is not None:
        return cart_state
    
    if user_message.lower() in ["давай закончим", "закончим", "хватит", "стоп"]:
        await update.message.reply_text(
            "Было приятно пообщаться! Надеюсь, мы скоро снова поговорим! 👋\n\n"
            "Что выберешь теперь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n"
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU
    
    # Генерируем интеллектуальный ответ
    response = get_chat_response(user_message, context)
    
    # Сохраняем историю диалога
    if "conversation_history" not in context.user_data:
        context.user_data["conversation_history"] = []
    
    context.user_data["conversation_history"].append({
        "user": user_message,
        "bot": response
    })
    
    # Ограничиваем историю последними 10 сообщениями
    if len(context.user_data["conversation_history"]) > 10:
        context.user_data["conversation_history"] = context.user_data["conversation_history"][-10:]
    
    await update.message.reply_text(response)
    return CHATTING

async def get_address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text
    user_name = context.user_data.get("user_name", "")
    cart_total = context.user_data.get("cart_total", 0)
    
    if contains_blacklisted_words(address):
        await update.message.reply_text(
            "Извините, но в адресе содержатся недопустимые слова. "
            "Пожалуйста, напишите адрес еще раз:"
        )
        from config import GET_ADDRESS
        return GET_ADDRESS
    
    cart = context.user_data.get("cart", [])
    order_details = "\n".join([f"• {product['name']} - {product['price']} руб." for product in cart])
    
    await update.message.reply_text(
        f"Спасибо за заказ, {user_name}! 🎉\n\n"
        f"Детали заказа:\n{order_details}\n\n"
        f"Итог: {cart_total} руб.\n"
        f"Адрес доставки: {address}\n\n"
        f"Курьер привезет вам заказ, оплата при получении."
    )
    
    context.user_data["cart"] = []
    context.user_data["cart_total"] = 0
    
    await update.message.reply_text(
        "Что ещё хочешь?\n"
        "1. Поговорить\n"
        "2. Рассказать шутку\n"
        "3. Помочь с выбором канцелярии"
    )
    return MAIN_MENU

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = context.user_data.get("user_name", "")
    
    cart_total = context.user_data.get("cart_total", 0)
    if cart_total > 0:
        await update.message.reply_text(
            f"Спасибо за заказы в корзине на сумму {cart_total} руб.! "
            f"Мы свяжемся с тобой для оформления заказа."
        )
    
    await update.message.reply_text(f"Всего хорошего, {user_name}! Если что-то понадобится — пиши! 👋")
    return ConversationHandler.END

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.products import show_categories as show_cats
    await show_cats(update, context)
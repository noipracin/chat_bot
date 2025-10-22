import json
import joblib
import random
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Загрузка диалогов из файла
def load_dialogues(filename="dialogues.txt"):
    dialogues = {}
    with open(filename, "r", encoding="utf-8") as file:
        current_section = None
        for line in file:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                dialogues[current_section] = []
            elif line and current_section:
                dialogues[current_section].append(line)
    return dialogues

# Загрузка модели ML (если используется)
try:
    model = joblib.load("intent_model.pkl")
    vectorizer = joblib.load("vectorizer.pkl")
    ml_enabled = True
    print("ML модель загружена")
except Exception as e:
    ml_enabled = False
    print(f"ML модель не загружена: {e}")

# Загрузка диалогов
dialogues = load_dialogues()

# Загрузка намерений
with open("intents.json", "r", encoding="utf-8") as file:
    intents_data = json.load(file)

# Структурированные товары по категориям с ценами
product_categories = {
    "1": {
        "name": "Карандаши, ручки и письменные принадлежности",
        "products": {
            "1": {"name": "Синяя/черная гелевая ручка", "price": 15, "description": "Гелевая ручка, пишет мягко и четко"},
            "2": {"name": "Набор гелевых ручек", "price": 120, "description": "Набор из 8 гелевых ручек разных цветов"},
            "3": {"name": "Синяя/черная шариковая ручка", "price": 10, "description": "Классическая шариковая ручка"},
            "4": {"name": "Набор шариковых ручек", "price": 80, "description": "Набор из 10 шариковых ручек"},
            "5": {"name": "Набор цветных ручек", "price": 150, "description": "Набор из 12 цветных гелевых ручек"},
            "6": {"name": "Простой карандаш", "price": 5, "description": "Графитовый карандаш твердости HB"},
            "7": {"name": "Набор цветных карандашей", "price": 200, "description": "Набор из 24 цветных карандашей"},
            "8": {"name": "Набор текстовыделителей", "price": 90, "description": "Набор из 5 неоновых текстовыделителей"},
            "9": {"name": "Ластик", "price": 8, "description": "Мягкий ластик для карандаша"},
            "10": {"name": "Точилка", "price": 12, "description": "Пластиковая точилка с контейнером"}
        }
    },
    "2": {
        "name": "Для рисования и творчества",
        "products": {
            "1": {"name": "Акварель", "price": 180, "description": "Набор акварельных красок, 12 цветов"},
            "2": {"name": "Гуашь", "price": 220, "description": "Набор гуашевых красок, 9 цветов"},
            "3": {"name": "Набор кисточек", "price": 150, "description": "Набор кистей разной толщины, 5 штук"},
            "4": {"name": "Палитра", "price": 25, "description": "Пластиковая палитра для смешивания красок"}
        }
    },
    "3": {
        "name": "Бумага, тетради и блокноты",
        "products": {
            "1": {"name": "Тетрадь в клетку", "price": 50, "description": "Тетрадь 48 листов, клетка"},
            "2": {"name": "Тетрадь в линейку", "price": 50, "description": "Тетрадь 48 листов, линейка"},
            "3": {"name": "Тетрадь на кольцах", "price": 120, "description": "Тетрадь на кольцах, 120 листов"},
            "4": {"name": "Блокнот", "price": 80, "description": "Блокнот А5, 80 листов"},
            "5": {"name": "Бумага белая А4", "price": 180, "description": "Пачка бумаги А4, 500 листов"},
            "6": {"name": "Бумага цветная", "price": 95, "description": "Набор цветной бумаги, 16 листов"},
            "7": {"name": "Картон", "price": 60, "description": "Набор цветного картона, 8 листов"}
        }
    },
    "4": {
        "name": "Иная продукция и аксессуары",
        "products": {
            "1": {"name": "Корректор", "price": 35, "description": "Корректор-лента, 5мм"},
            "2": {"name": "Скотч", "price": 25, "description": "Прозрачный скотч, 1см х 33м"},
            "3": {"name": "Линейка", "price": 15, "description": "Пластиковая линейка 20см"},
            "4": {"name": "Транспортир", "price": 20, "description": "Пластиковый транспортир 180°"},
            "5": {"name": "Циркуль", "price": 45, "description": "Металлический циркуль с грифелем"},
            "6": {"name": "Клей", "price": 30, "description": "Клей-карандаш 21г"}
        }
    }
}

# Новые шутки для бота
jokes = [
    "Почему карандаш решил стать художником? Потому что у него было острое чувство юмора! ✏️",
    "Что сказал один маркер другому? 'Ты такой яркий, что я тебя не перевариваю!' 🎨",
    "Почему тетрадь пошла к психологу? Потому что у нее были сложные отношения с листами! 📓",
    "Как ластик объясняет свои неудачи? 'Я просто стираюсь от ответственности!' 🧼",
    "Почему степлер такой уверенный в себе? Потому что он всегда скрепляет сделанное! 📎",
    "Что ручка сказала карандашу? 'Твои шутки такие острые, что я синею от смеха!' ✏️",
    "Почему линейка такая прямая? Потому что она не умеет отклоняться от темы! 📏",
    "Как ножницы решают конфликты? Они просто разрезают их пополам! ✂️",
    "Почему клей такой популярный? Потому что он умеет налаживать контакты! 🧴",
    "Что блокнот сказал своему хозяину? 'Я всегда открыт для новых идей!' 📔",
    "Почему скрепка не пошла на вечеринку? Потому что она боялась разойтись! 📎",
    "Как циркуль находит друзей? Он просто описывает вокруг себя окружность! 📐",
    "Почему дырокол всегда в хорошем настроении? Потому что он видит все в ином свете! 🕳️",
    "Что папка сказала документам? 'Ребята, давайте держаться вместе!' 📁",
    "Почему корректор такой скромный? Потому что он не любит выделяться! 🖍️"
]

# Темы для разговора с логическими переходами
conversation_flows = {
    "работа_учеба": [
        "Как твои успехи в учёбе/работе?",
        "А что тебе больше всего нравится в твоей деятельности?",
        "Сложно ли тебе дается учеба/работа? Как справляешься?"
    ],
    "хобби": [
        "Какие у тебя хобби?",
        "А как давно ты этим увлекаешься?",
        "Твои хобби как-то связаны с творчеством?"
    ],
    "кино_книги": [
        "Какой твой любимый фильм или книга?",
        "А почему именно этот? Что тебя в нем привлекло?",
        "Часто читаешь/сматришь что-то новое?"
    ],
    "технологии": [
        "Что ты думаешь о современных технологиях?",
        "А какими гаджетами пользуешься чаще всего?",
        "Как думаешь, технологии больше помогают или мешают?"
    ]
}

# Состояния диалога
GET_NAME, MAIN_MENU, CHATTING, JOKE, CHOOSE_CATEGORY, VIEW_PRODUCTS, CONFIRM_ORDER = range(7)

# Асинхронный обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Инициализация корзины
    context.user_data["cart"] = []
    context.user_data["cart_total"] = 0
    
    await update.message.reply_text(
        "Привет) Меня зовут Рональд и я являюсь ботом канцтоваров.\n"
        "Как я могу к тебе обращаться?"
    )
    return GET_NAME

# Обработчик получения имени пользователя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = update.message.text
    context.user_data["user_name"] = user_name
    context.user_data["conversation_state"] = {"topic": None, "step": 0}
    
    await update.message.reply_text(
        f"Приятно познакомиться, {user_name}!\n\n"
        "У меня есть несколько функций:\n"
        "1. Могу поговорить с тобой\n"
        "2. Рассказать шутку\n"
        "3. Помочь с выбором канцелярии\n\n"
        "Что выберешь?"
    )
    return MAIN_MENU

# Функция для определения намерения
def detect_intent(message):
    message_lower = message.lower()
    
    # Простая логика определения намерения по ключевым словам
    if any(word in message_lower for word in ["привет", "здравств", "добр", "хай", "ку"]):
        return "приветствие"
    elif any(word in message_lower for word in ["поговорить", "поболтать", "общение", "1"]):
        return "поговорить"
    elif any(word in message_lower for word in ["шутк", "юмор", "смех", "2"]):
        return "шутка"
    elif any(word in message_lower for word in ["канцеляр", "товар", "покуп", "ручк", "тетрад", "карандаш", "3"]):
        return "канцелярия"
    elif any(word in message_lower for word in ["пока", "до свидан", "конец", "закончи"]):
        return "завершение"
    elif any(word in message_lower for word in ["да", "еще", "ещё", "хочу", "конечно"]):
        return "да"
    elif any(word in message_lower for word in ["нет", "не", "хватит", "достаточно"]):
        return "нет"
    elif any(word in message_lower for word in ["работ", "учеб", "офиc", "коллег"]):
        return "работа_учеба"
    elif any(word in message_lower for word in ["хобби", "увлечен", "свободное время", "отдых"]):
        return "хобби"
    elif any(word in message_lower for word in ["фильм", "кино", "книг", "сериал"]):
        return "кино_книги"
    elif any(word in message_lower for word in ["технолог", "гаджет", "компьютер", "смартфон"]):
        return "технологии"
    elif any(word in message_lower for word in ["назад", "вернуться"]):
        return "назад"
    
    return None

# Функция для обновления корзины
def update_cart(context, product, operation="add"):
    cart = context.user_data.get("cart", [])
    cart_total = context.user_data.get("cart_total", 0)
    
    if operation == "add":
        cart.append(product)
        cart_total += product["price"]
    elif operation == "remove":
        if product in cart:
            cart.remove(product)
            cart_total -= product["price"]
    
    context.user_data["cart"] = cart
    context.user_data["cart_total"] = cart_total
    return cart_total

# Функция для показа категорий товаров
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = context.user_data.get("user_name", "")
    
    categories_text = (
        f"Хорошо, {user_name}, посмотри, что у меня есть:\n\n"
        "1. ✏️ Карандаши, ручки и письменные принадлежности\n"
        "2. 🎨 Для рисования и творчества\n" 
        "3. 📓 Бумага, тетради и блокноты\n"
        "4. 📎 Иная продукция и аксессуары\n\n"
        "Выбери номер категории, которая тебя интересует:"
    )
    
    await update.message.reply_text(categories_text)

# Функция для показа товаров в категории 1
async def show_category1_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products_text = (
        "✏️ Карандаши, ручки и письменные принадлежности:\n\n"
        "1. Синяя/черная гелевая ручка - 15 руб.\n"
        "2. Набор гелевых ручек - 120 руб.\n"
        "3. Синяя/черная шариковая ручка - 10 руб.\n"
        "4. Набор шариковых ручек - 80 руб.\n"
        "5. Набор цветных ручек - 150 руб.\n"
        "6. Простой карандаш - 5 руб.\n"
        "7. Набор цветных карандашей - 200 руб.\n"
        "8. Набор текстовыделителей - 90 руб.\n"
        "9. Ластик - 8 руб.\n"
        "10. Точилка - 12 руб.\n\n"
        "Вернуться назад\n\n"
        "Выбери номер товара для добавления в корзину:"
    )
    
    
    # await update.message.reply_photo(photo=open('images/category1_1.jpg', 'rb'), caption="Синяя/черная гелевая ручка")
    # ... и так для всех 10 товаров
    
    await update.message.reply_text(products_text)

# Функция для показа товаров в категории 2
async def show_category2_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products_text = (
        "🎨 Для рисования и творчества:\n\n"
        "1. Акварель - 180 руб.\n"
        "2. Гуашь - 220 руб.\n"
        "3. Набор кисточек - 150 руб.\n"
        "4. Палитра - 25 руб.\n\n"
        "Вернуться назад\n\n"
        "Выбери номер товара для добавления в корзину:"
    )
    
    # Здесь будут фото (в реальном боте нужно добавить отправку фото)
    await update.message.reply_text(products_text)

# Функция для показа товаров в категории 3
async def show_category3_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products_text = (
        "📓 Бумага, тетради и блокноты:\n\n"
        "1. Тетрадь в клетку - 50 руб.\n"
        "2. Тетрадь в линейку - 50 руб.\n"
        "3. Тетрадь на кольцах - 120 руб.\n"
        "4. Блокнот - 80 руб.\n"
        "5. Бумага белая А4 - 180 руб.\n"
        "6. Бумага цветная - 95 руб.\n"
        "7. Картон - 60 руб.\n\n"
        "Вернуться назад\n\n"
        "Выбери номер товара для добавления в корзину:"
    )
    
    # Здесь будут фото (в реальном боте нужно добавить отправку фото)
    await update.message.reply_text(products_text)

# Функция для показа товаров в категории 4
async def show_category4_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products_text = (
        "📎 Иная продукция и аксессуары:\n\n"
        "1. Корректор - 35 руб.\n"
        "2. Скотч - 25 руб.\n"
        "3. Линейка - 15 руб.\n"
        "4. Транспортир - 20 руб.\n"
        "5. Циркуль - 45 руб.\n"
        "6. Клей - 30 руб.\n\n"
        "Вернуться назад\n\n"
        "Выбери номер товара для добавления в корзину:"
    )
    
    # Здесь будут фото (в реальном боте нужно добавить отправку фото)
    await update.message.reply_text(products_text)

# Функция для добавления товара в корзину
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, category_key: str, product_key: str):
    category = product_categories.get(category_key)
    if not category:
        await update.message.reply_text("Ошибка: категория не найдена")
        return
    
    product = category["products"].get(product_key)
    if not product:
        await update.message.reply_text("Ошибка: товар не найден")
        return
    
    # Добавляем товар в корзину
    cart_total = update_cart(context, product, "add")
    
    await update.message.reply_text(
        f"Товар '{product['name']}' добавлен в корзину\n"
        f"Корзина: {cart_total} руб."
    )
    
    # Возвращаем пользователя к тому же списку товаров
    if category_key == "1":
        await show_category1_products(update, context)
    elif category_key == "2":
        await show_category2_products(update, context)
    elif category_key == "3":
        await show_category3_products(update, context)
    elif category_key == "4":
        await show_category4_products(update, context)

# Обработчик главного меню
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    user_name = context.user_data.get("user_name", "")
    
    intent = detect_intent(user_message)
    
    if intent == "поговорить":
        # Выбираем случайную тему для начала разговора
        topic = random.choice(list(conversation_flows.keys()))
        context.user_data["conversation_state"] = {"topic": topic, "step": 0}
        
        greeting = random.choice(dialogues["GREETING"])
        first_question = conversation_flows[topic][0]
        
        await update.message.reply_text(
            f"{greeting}\n\n"
            f"{first_question}\n\n"
            "Если захочешь закончить диалог, напиши 'Давай закончим'."
        )
        return CHATTING
        
    elif intent == "шутка":
        # Инициализируем список использованных шуток
        context.user_data["used_jokes"] = []
        context.user_data["all_jokes"] = jokes.copy()
        
        await update.message.reply_text("Хорошо, попробую поднять тебе настроение)")
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
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU

# Обработчик выбора категории
async def choose_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.strip()
    
    if user_message == "1":
        context.user_data["current_category"] = "1"
        await show_category1_products(update, context)
        return VIEW_PRODUCTS
    elif user_message == "2":
        context.user_data["current_category"] = "2"
        await show_category2_products(update, context)
        return VIEW_PRODUCTS
    elif user_message == "3":
        context.user_data["current_category"] = "3"
        await show_category3_products(update, context)
        return VIEW_PRODUCTS
    elif user_message == "4":
        context.user_data["current_category"] = "4"
        await show_category4_products(update, context)
        return VIEW_PRODUCTS
    else:
        await update.message.reply_text("Пожалуйста, выбери номер категории от 1 до 4:")
        return CHOOSE_CATEGORY

# Обработчик просмотра товаров
async def view_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.strip().lower()
    current_category = context.user_data.get("current_category")
    
    # Обработка команды "назад"
    if user_message in ["назад", "вернуться назад"]:
        await show_categories(update, context)
        return CHOOSE_CATEGORY
    
    # Добавление товара в корзину
    try:
        product_number = int(user_message)
        await add_to_cart(update, context, current_category, str(product_number))
        return VIEW_PRODUCTS
    except ValueError:
        await update.message.reply_text("Пожалуйста, выбери номер товара или напиши 'назад':")
        return VIEW_PRODUCTS

# Функция для рассказа шутки
async def tell_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    used_jokes = context.user_data.get("used_jokes", [])
    all_jokes = context.user_data.get("all_jokes", [])
    
    # Находим шутки, которые еще не использовались
    available_jokes = [j for j in all_jokes if j not in used_jokes]
    
    if available_jokes:
        # Выбираем случайную шутку из доступных
        joke = random.choice(available_jokes)
        used_jokes.append(joke)
        context.user_data["used_jokes"] = used_jokes
        
        await update.message.reply_text(joke)
        await update.message.reply_text("Хочешь еще?)")
    else:
        # Все шутки использованы
        await update.message.reply_text("Прости, у меня закончились шутки 😢")
        await update.message.reply_text(
            "Что ещё хочешь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n" 
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU

# Обработчик состояния шуток
async def joke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text.lower()
    user_name = context.user_data.get("user_name", "")
    
    intent = detect_intent(user_message)
    
    if intent == "да":
        await tell_joke(update, context)
        return JOKE
    elif intent == "нет":
        await update.message.reply_text("Надеюсь я поднял тебе настроение) ")
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

# Обработчик общения
async def chatting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    user_name = context.user_data.get("user_name", "")
    
    # Завершение диалога
    if user_message.lower() == "давай закончим":
        farewell = random.choice(dialogues["ENDING"])
        await update.message.reply_text(
            f"{farewell}\n\n"
            "Что выберешь теперь?\n"
            "1. Поговорить\n"
            "2. Рассказать шутку\n"
            "3. Помочь с выбором канцелярии"
        )
        return MAIN_MENU
    
    # Получаем текущее состояние разговора
    state = context.user_data.get("conversation_state", {"topic": None, "step": 0})
    topic = state["topic"]
    step = state["step"]
    
    # Если тема не установлена, выбираем случайную
    if not topic:
        topic = random.choice(list(conversation_flows.keys()))
        state["topic"] = topic
        state["step"] = 0
    
    # Определяем, о чем говорит пользователь
    user_intent = detect_intent(user_message)
    
    # Если пользователь явно переключил тему
    if user_intent and user_intent in conversation_flows:
        topic = user_intent
        state["topic"] = topic
        state["step"] = 0
        response = conversation_flows[topic][0]
    
    # Продолжаем текущую тему
    else:
        step += 1
        state["step"] = step
        
        # Если есть следующий вопрос в теме
        if step < len(conversation_flows[topic]):
            response = conversation_flows[topic][step]
        else:
            # Завершаем тему и переходим к новой
            response = random.choice(dialogues["CONTEXT_REACTIONS"])
            
            # Иногда предлагаем канцтовары (30% вероятность)
            if random.random() < 0.3:
                # Выбираем случайную категорию и товар
                category_key = random.choice(list(product_categories.keys()))
                category = product_categories[category_key]
                product_key = random.choice(list(category["products"].keys()))
                product = category["products"][product_key]
                response += f" Кстати, для {topic.replace('_', ' ')} могут пригодиться {product['name']}!"
            
            # Выбираем новую тему
            new_topic = random.choice([t for t in conversation_flows.keys() if t != topic])
            state["topic"] = new_topic
            state["step"] = 0
            response += f"\n\n{conversation_flows[new_topic][0]}"
    
    context.user_data["conversation_state"] = state
    await update.message.reply_text(response)
    return CHATTING

# Обработчик завершения диалога
async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_name = context.user_data.get("user_name", "")
    
    # Показываем итоги корзины при завершении
    cart_total = context.user_data.get("cart_total", 0)
    if cart_total > 0:
        await update.message.reply_text(
            f"Спасибо за заказы в корзине на сумму {cart_total} руб.! "
            f"Мы свяжемся с тобой для оформления заказа."
        )
    
    await update.message.reply_text(f"Всего хорошего, {user_name}! Если что-то понадобится — пиши!")
    return ConversationHandler.END

def main():
    application = Application.builder().token("8246619082:AAH2r5PFRDeNRCGfgOFPEFzD0a5bApy7EgU").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            CHATTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, chatting)],
            JOKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, joke_handler)],
            CHOOSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_category_handler)],
            VIEW_PRODUCTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_products_handler)],
        },
        fallbacks=[CommandHandler("end", end_conversation)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
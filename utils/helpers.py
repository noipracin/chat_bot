import re
import random
import json
import os
from difflib import SequenceMatcher

from data.content import BLACKLISTED_WORDS, JOKES

def contains_blacklisted_words(message):
    message_lower = message.lower()
    for word in BLACKLISTED_WORDS:
        if word in message_lower:
            return True
    return False

def extract_name_from_text(text):
    text_lower = text.lower().strip()
    
    patterns = [
        r'(?:меня зовут|мое имя|зовут|имя) ([а-яёa-z]{2,})',
        r'([а-яёa-z]{2,}) (?:это мое имя|меня зовут)',
        r'^([а-яёa-z]{2,})$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            name = match.group(1).strip()
            stop_words = ['меня', 'тебя', 'его', 'её', 'их', 'нам', 'вам', 'им', 'это', 'то', 'вот', 'ну', 'да', 'нет', 'привет']
            if name and name not in stop_words and len(name) >= 2:
                return name.capitalize()
    
    words = text.split()
    if words:
        first_word = words[0].strip('.,!?;:').capitalize()
        stop_words_capitalized = [word.capitalize() for word in stop_words]
        if first_word and first_word not in stop_words_capitalized and len(first_word) >= 2:
            return first_word
    
    return None

def load_intents():
    """Загружает интенты из JSON файла"""
    try:
        with open('data/intents.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл intents.json не найден")
        return {"intents": []}
    except json.JSONDecodeError:
        print("Ошибка чтения intents.json")
        return {"intents": []}

def load_dialogues():
    """Загружает диалоги из файла"""
    dialogues = []
    try:
        with open('data/dialogues.txt', 'r', encoding='utf-8') as f:
            current_dialogue = []
            for line in f:
                line = line.strip()
                if line.startswith('П: '):
                    current_dialogue.append(('user', line[3:]))
                elif line.startswith('Б: '):
                    current_dialogue.append(('bot', line[3:]))
                elif not line and current_dialogue:
                    dialogues.append(current_dialogue)
                    current_dialogue = []
            
            if current_dialogue:
                dialogues.append(current_dialogue)
    except FileNotFoundError:
        print("Файл dialogues.txt не найден")
    
    return dialogues

def similar(a, b):
    """Вычисляет схожесть двух строк"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_intent_response(message, intents_data):
    """Находит лучший ответ на основе интентов"""
    message_lower = message.lower()
    best_score = 0
    best_response = None
    
    for intent in intents_data.get("intents", []):
        for pattern in intent["patterns"]:
            score = similar(message_lower, pattern)
            
            # Если найдено точное совпадение или очень высокая схожесть
            if pattern in message_lower or score > 0.8:
                if score > best_score:
                    best_score = score
                    best_response = random.choice(intent["responses"])
    
    return best_response

def find_dialogue_response(message, dialogues):
    """Находит ответ в диалогах на основе схожести"""
    message_lower = message.lower()
    best_match = None
    best_score = 0
    
    for dialogue in dialogues:
        for i, (speaker, text) in enumerate(dialogue):
            if speaker == 'user':
                score = similar(message_lower, text.lower())
                if score > best_score and score > 0.6:
                    best_score = score
                    # Ищем следующий ответ бота в диалоге
                    for j in range(i + 1, len(dialogue)):
                        if dialogue[j][0] == 'bot':
                            best_match = dialogue[j][1]
                            break
    
    return best_match

def detect_intent(message):
    """Основная функция определения намерения с улучшенной логикой"""
    message_lower = message.lower()
    
    # Сначала проверяем команды корзины и управления
    keyword_map = {
        "поговорить": ["поговорить", "поболтать", "общение", "общай", "1", "разговор"],
        "шутка": ["шутк", "юмор", "смех", "2", "посмей", "рассмеши"],
        "канцелярия": ["канцеляр", "товар", "покуп", "ручк", "тетрад", "карандаш", "3", "магазин"],
        "завершение": ["пока", "до свидан", "конец", "закончи", "выход", "стоп"],
        "да": ["да", "еще", "ещё", "хочу", "конечно", "ага", "угу"],
        "нет": ["нет", "не", "хватит", "достаточно", "неа", "не хочу"],
        "корзина": ["корзина", "корзин", "заказ", "покупки", "что в корзине"],
        "очистить": ["очистить", "удалить все", "очист", "опустошить"],
        "заказать": ["заказать", "оформить", "доставк", "куплю", "приобрести"],
        "назад": ["назад", "вернуться", "возврат", "предыдущий"],
        "помощь": ["помощь", "помоги", "help", "что ты умеешь"]
    }
    
    for intent, keywords in keyword_map.items():
        if any(keyword in message_lower for keyword in keywords):
            return intent
    
    if message_lower.startswith("убрать"):
        return "убрать"
    
    return None

def get_chat_response(message, context):
    """Генерирует интеллектуальный ответ для общения"""
    # Загружаем данные если их нет в контексте
    if "intents_data" not in context.bot_data:
        context.bot_data["intents_data"] = load_intents()
    
    if "dialogues" not in context.bot_data:
        context.bot_data["dialogues"] = load_dialogues()
    
    # Пытаемся найти ответ в интентах
    intent_response = find_best_intent_response(message, context.bot_data["intents_data"])
    if intent_response:
        return intent_response
    
    # Пытаемся найти ответ в диалогах
    dialogue_response = find_dialogue_response(message, context.bot_data["dialogues"])
    if dialogue_response:
        return dialogue_response
    
    # Общие ответы если не нашли подходящего
    general_responses = [
        "Интересно! Расскажи подробнее?",
        "Понятно! А что ты об этом думаешь?",
        "Спасибо, что поделился! Как ты к этому пришел?",
        "Любопытно! А что было самым сложным?",
        "Ясно! Давай поговорим о чем-то еще?",
        "Спасибо за рассказ! Что планируешь делать дальше?",
        "Хм, понял. А как это на тебя повлияло?",
        "Интересная мысль! У тебя есть еще какие-то идеи?",
        "Понял тебя. Хочешь обсудить что-то конкретное?",
        "Слушаю внимательно! Продолжай, пожалуйста."
    ]
    
    # Добавляем персонализированный ответ если знаем имя
    user_name = context.user_data.get("user_name", "")
    if user_name and random.random() < 0.3:
        response = random.choice(general_responses)
        return f"{user_name}, {response.lower()}"
    
    return random.choice(general_responses)
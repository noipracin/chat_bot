import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

def train_intent_model():
    # Загрузка данных
    try:
        with open('intents.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        print("Файл intents.json успешно загружен")
    except Exception as e:
        print(f"Ошибка загрузки intents.json: {e}")
        return

    # Подготовка данных для обучения
    texts = []
    labels = []
    
    # Собираем статистику
    intent_stats = {}
    
    for intent in data['intents']:
        tag = intent['tag']
        patterns = intent.get('patterns', [])
        
        # Собираем статистику по каждому интенту
        intent_stats[tag] = len(patterns)
        
        # Добавляем только интенты с паттернами
        if patterns:
            for pattern in patterns:
                texts.append(pattern.lower())
                labels.append(tag)

    # Проверяем, есть ли данные для обучения
    if len(texts) == 0:
        print("Нет данных для обучения модели!")
        return

    # Выводим статистику
    print("\nСтатистика данных для обучения:")
    for tag, count in intent_stats.items():
        print(f"  {tag}: {count} примеров")
    print(f"Всего примеров: {len(texts)}")

    # Векторизация текста
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.8
    )

    try:
        X = vectorizer.fit_transform(texts)
        print(f"Размерность признаков: {X.shape}")
    except Exception as e:
        print(f"Ошибка векторизации: {e}")
        return

    # Разделение на обучающую и тестовую выборку
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print(f"Обучающая выборка: {X_train.shape[0]} примеров")
    print(f"Тестовая выборка: {X_test.shape[0]} примеров")

    # Обучение модели
    model = MultinomialNB(alpha=0.1)
    
    try:
        model.fit(X_train, y_train)
        print("Модель успешно обучена!")
    except Exception as e:
        print(f"Ошибка обучения модели: {e}")
        return

    # Оценка модели
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nТочность модели: {accuracy:.3f}")
    print("\nОтчет по классификации:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Сохранение модели и векторизатора
    try:
        joblib.dump(model, 'intent_model.pkl')
        joblib.dump(vectorizer, 'vectorizer.pkl')
        print("\nМодель и векторизатор успешно сохранены!")
        
    except Exception as e:
        print(f"Ошибка сохранения модели: {e}")

if __name__ == "__main__":
    print("Начало обучения модели классификации намерений...")
    train_intent_model()
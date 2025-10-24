import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

def train_model():
    """Обучает ML модель для распознавания намерений"""
    
    # Загружаем данные для обучения
    with open('intents.json', 'r', encoding='utf-8') as f:
        intents = json.load(f)
    
    # Подготавливаем данные для обучения
    texts = []
    labels = []
    
    for intent, examples in intents.items():
        for example in examples:
            texts.append(example)
            labels.append(intent)
    
    # Создаем и обучаем модель
    model = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('svc', SVC(probability=True))
    ])
    
    model.fit(texts, labels)
    
    # Сохраняем модель
    joblib.dump(model, 'intent_model.pkl')
    
    # Сохраняем векторизатор отдельно (если нужно)
    vectorizer = TfidfVectorizer()
    vectorizer.fit(texts)
    joblib.dump(vectorizer, 'vectorizer.pkl')
    
    print("✅ Модель успешно обучена и сохранена!")
    print(f"📊 Обучено на {len(texts)} примерах")
    print(f"🎯 Намерения: {list(intents.keys())}")

if __name__ == '__main__':
    train_model()
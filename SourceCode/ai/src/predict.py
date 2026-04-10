import joblib
from preprocessing import clean_text

# Load model
category_model = joblib.load("../models/category_model.pkl")
emotion_model = joblib.load("../models/emotion_model.pkl")
vectorizer = joblib.load("../models/vectorizer.pkl")

def predict(text):
    text = clean_text(text)
    vec = vectorizer.transform([text])

    category = category_model.predict(vec)[0]
    emotion = emotion_model.predict(vec)[0]

    return {
        "category": category,
        "emotion": emotion
    }
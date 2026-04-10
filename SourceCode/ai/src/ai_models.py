import joblib
import os
import sys

# ======================
# Fix import path
# ======================
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PROJECT_ROOT)

from preprocessing import clean_text


# ======================
# Load Models (Singleton)
# ======================
class AIModel:
    def __init__(self):
        model_dir = os.path.join(PROJECT_ROOT, "models")

        # Category
        self.category_model = joblib.load(
            os.path.join(model_dir, "category_model.pkl")
        )
        self.category_vectorizer = joblib.load(
            os.path.join(model_dir, "vectorizer.pkl")
        )

        # Emotion
        self.emotion_model = joblib.load(
            os.path.join(model_dir, "emotion_model.pkl")
        )
        self.emotion_vectorizer = joblib.load(
            os.path.join(model_dir, "emotion_vectorizer.pkl")
        )

    # ======================
    # Category Prediction
    # ======================
    def predict_category(self, text: str):
        clean = clean_text(text)
        vec = self.category_vectorizer.transform([clean])
        pred = self.category_model.predict(vec)[0]
        return pred

    # ======================
    # Emotion Prediction
    # ======================
    def predict_emotion(self, text: str):
        clean = clean_text(text)
        vec = self.emotion_vectorizer.transform([clean])  # ✅ FIX
        pred = self.emotion_model.predict(vec)[0]
        return pred

    # ======================
    # Predict All
    # ======================
    def predict_all(self, text: str):
        return {
            "text": text,
            "category": self.predict_category(text),
            "emotion": self.predict_emotion(text)
        }


# ======================
# Singleton instance
# ======================
ai_model = AIModel()


# ======================
# Wrapper functions
# ======================
def predict_category(text: str):
    return ai_model.predict_category(text)


def predict_emotion(text: str):
    return ai_model.predict_emotion(text)


def predict_all(text: str):
    return ai_model.predict_all(text)


# ======================
# Test
# ======================
if __name__ == "__main__":
    samples = [
        "mua thuốc cảm hết 200k",
        "ăn bún bò 35k sáng nay"
    ]

    for s in samples:
        print(predict_all(s))
import joblib
import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ======================
# Fix import path
# ======================
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

sys.path.append(PROJECT_ROOT)


from ai.src.preprocessing import clean_text
from ai.src.amount_extractor import extract_amount
# ======================
# Load Models (Singleton)
# ======================
class AIModel:
    def __init__(self):
        model_dir = os.path.join(PROJECT_ROOT, "models")

        try:
            # 1. Tải mô hình Category (SVM)
            self.category_model = joblib.load(
                os.path.join(model_dir, "category_model.pkl")
            )
            self.category_vectorizer = joblib.load(
                os.path.join(model_dir, "vectorizer.pkl")
            )

            # 2. Tải mô hình Emotion
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            phobert_path = os.path.join(model_dir, "emotion_phobert")

            self.emotion_tokenizer = AutoTokenizer.from_pretrained(phobert_path)
            self.emotion_model = AutoModelForSequenceClassification.from_pretrained(phobert_path)
            self.emotion_model.to(self.device)
            self.emotion_model.eval()

            # Từ điển dịch ngược nhãn của PhoBERT
            self.emotion_labels = {0: "Tiêu cực", 1: "Bình thường", 2: "Tích cực"}

            print(f" Models loaded successfully on {self.device}")

        except Exception as e:
            print(" Error loading models:", e)
            raise e

    # ======================
    # Category Prediction
    # ======================
    def predict_category(self, text: str):
        text_lower = text.lower()

        # 1. BỘ LỌC DỰ PHÒNG (Rule-based)
        # Bắt chết các từ khóa đặc thù mà không cần AI phải suy nghĩ
        if any(kw in text_lower for kw in ["tiền nhà", "thuê nhà", "phòng trọ", "tiền điện", "tiền nước", "wifi"]):
            return "Hóa đơn"
        if any(kw in text_lower for kw in ["học phí", "giáo trình", "tiền học", "quỹ lớp"]):
            return "Học tập"
        if any(kw in text_lower for kw in ["xăng", "taxi", "grab", "xe bus", "vé xe"]):
            return "Di chuyển"

        # 2. HỌC MÁY (Machine Learning)
        # Nếu câu nói lắt léo và không lọt vào các từ khóa trên, giao cho SVM dự đoán
        clean = clean_text(text)
        vec = self.category_vectorizer.transform([clean])
        return self.category_model.predict(vec)[0]
    # ======================
    # Emotion Prediction (PhoBERT)
    # ======================
    def predict_emotion(self, text: str):
        clean = clean_text(text)  # PhoBERT rất cần chữ được gạch nối (vd: trà_sữa)

        # Tiền xử lý thành Tensor
        inputs = self.emotion_tokenizer(clean, return_tensors="pt", truncation=True, padding=True, max_length=64)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Suy luận không tính đạo hàm (tăng tốc độ)
        with torch.no_grad():
            outputs = self.emotion_model(**inputs)
            pred_idx = torch.argmax(outputs.logits, dim=1).item()

        return self.emotion_labels[pred_idx]

    # ======================
    # FULL SMART INPUT
    # ======================
    def predict_all(self, text: str):
        try:
            amount = extract_amount(text)
            category = self.predict_category(text)
            emotion = self.predict_emotion(text)

            # Tự động suy luận Type cho Frontend
            trans_type = "Thu nhập" if category == "Thu nhập" else "Chi tiêu"

            return {
                "text": text,
                "amount": amount,
                "category": category,
                "emotion": emotion,
                "type": trans_type
            }

        except Exception as e:
            return {
                "text": text,
                "error": str(e)
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
        "hôm nay trúng số được 5 củ",
        "trả tiền nhà hết 1.5 triệu xót hết cả ruột"
    ]

    for s in samples:
        print(predict_all(s))
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
        if any(kw in text_lower for kw in ["tiền nhà", "thuê nhà", "phòng trọ", "tiền điện", "tiền nước", "wifi"]):
            return "Hóa đơn"
        if any(kw in text_lower for kw in ["học phí", "giáo trình", "tiền học", "quỹ lớp"]):
            return "Học tập"
        if any(kw in text_lower for kw in ["xăng", "taxi", "grab", "xe bus", "vé xe"]):
            return "Di chuyển"
        if any(kw in text_lower for kw in ["ăn", "uống", "trà sữa", "bún", "bánh mì", "cơm", "phở", "lẩu", "nhậu", "cà phê", "cafe", "ăn ngoài"]):
            return "Ăn uống"
        if any(kw in text_lower for kw in ["thuốc", "khám", "bệnh viện", "bác sĩ", "hiệu thuốc", "y tế", "thuốc cảm", "spa"]):
            return "Sức khỏe"
        if any(kw in text_lower for kw in ["mua sắm", "quần áo", "giày", "shopee", "tiki", "lazada"]):
            return "Mua sắm"

        # 2. HỌC MÁY
        clean = clean_text(text)
        vec = self.category_vectorizer.transform([clean])
        return self.category_model.predict(vec)[0]
    # ======================
    # Emotion Prediction
    # ======================
    def predict_emotion(self, text: str):
        text_lower = text.lower()
        
        # 1. BỘ LỌC TỪ KHÓA CẢM XÚC MẠNH
        negative_keywords = ["buồn", "chán", "stress", "mệt", "tệ", "thất vọng", "xót", "tức", "bực", "cáu", "áp lực", "đau ví", "thất tình", "đau lòng"]
        positive_keywords = ["vui", "sướng", "tuyệt", "ngon", "thưởng", "lương", "đã", "hạnh phúc", "phê", "hưng phấn", "may mắn"]
        
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        
        if neg_count > pos_count:
            return "Tiêu cực"
        elif pos_count > neg_count:
            return "Tích cực"
            
        # 2. HỌC MÁY (PhoBERT)
        clean = clean_text(text)
        inputs = self.emotion_tokenizer(clean, return_tensors="pt", truncation=True, padding=True, max_length=64)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

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
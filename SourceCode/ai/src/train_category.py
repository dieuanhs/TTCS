import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
import joblib


from preprocessing import clean_text


# ======================
# 1. Load data
# ======================
df = pd.read_csv("../data/dataset_v1_clean.csv")


# ======================
# 2. Preprocess
# ======================
df["clean_text"] = df["Raw Text (Câu văn thô)"].apply(clean_text)


# ======================
# 3. Feature + Label
# ======================
X = df["clean_text"]
y = df["auto_category"]


# ======================
# 4. Vectorize (CẢI TIẾN)
# ======================
vectorizer = TfidfVectorizer(
   ngram_range=(1, 2),      # 🔥 cực quan trọng
   max_features=5000        # tránh overfit
)


X_vec = vectorizer.fit_transform(X)


# ======================
# 5. Train/Test split (CẢI TIẾN)
# ======================
X_train, X_test, y_train, y_test = train_test_split(
   X_vec,
   y,
   test_size=0.2,
   random_state=42,
   stratify=y   # 🔥 giữ phân bố class
)


# ======================
# 6. Train model (CẢI TIẾN)
# ======================
model = LinearSVC(
   class_weight='balanced',   # 🔥 fix imbalance
   max_iter=2000
)


model.fit(X_train, y_train)


# ======================
# 7. Evaluate (FIX WARNING)
# ======================
y_pred = model.predict(X_test)


print("=== Classification Report ===")
print(classification_report(
   y_test,
   y_pred,
   zero_division=0   # 🔥 tránh warning
))


# ======================
# 8. Save model
# ======================
joblib.dump(model, "../models/category_model.pkl")
joblib.dump(vectorizer, "../models/vectorizer.pkl")


print("✅ Model saved!")


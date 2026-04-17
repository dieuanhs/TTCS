import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
import joblib
from utils import save_evaluation_log
# ======================
# 1. Load data
# ======================
df = pd.read_csv("../data/dataset_v1_clean.csv")

df = df.dropna(subset=["clean_text", "Category"])
X = df["clean_text"]
y = df["Category"]

# ======================
# 2. Vectorize (TRỌN VẸN TỪ KHÓA)
# ======================
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    sublinear_tf=True
)

X_vec = vectorizer.fit_transform(X)

# ======================
# 3. Split
# ======================
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y,
    test_size=0.15,
    random_state=42,
    stratify=y
)

# ======================
# 4. Train (
# ======================
model = LinearSVC(
    class_weight='balanced',
    C=5.0,
    max_iter=5000,
    random_state=42
)
model.fit(X_train, y_train)

# ======================
# 5. Evaluate
# ======================
y_pred = model.predict(X_test)

print("=== Classification Report ===")
report = classification_report(y_test, y_pred, zero_division=0)
print(report)


save_evaluation_log(
    model_name="LinearSVC (Category)",
    config_info="C=5.0, ngram_range=(1,2), sublinear_tf=True",
    report_text=report
)

# ======================
# 6. Save
# ======================
joblib.dump(model, "../models/category_model.pkl")
joblib.dump(vectorizer, "../models/vectorizer.pkl")
print(" Model saved!")
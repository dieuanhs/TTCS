import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from imblearn.over_sampling import RandomOverSampler
import joblib

from preprocessing import clean_text
from sklearn.feature_extraction.text import TfidfVectorizer

# Load data
df = pd.read_csv("../data/dataset_v1_clean.csv")

df["clean_text"] = df["Raw Text (Câu văn thô)"].apply(clean_text)

X = df["clean_text"]
y = df["Emotion"]

# Vectorize
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_vec, y, test_size=0.2, random_state=42
)

# Train
model = LogisticRegression(max_iter=200, class_weight="balanced")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print(y.value_counts())
# Save
joblib.dump(vectorizer, "../models/emotion_vectorizer.pkl")
joblib.dump(model, "../models/emotion_model.pkl")
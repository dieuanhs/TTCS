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
# 2. Vectorize (Tối ưu hóa params)
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

#4. Train
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression

if __name__ == "__main__":
    # Tìm kiếm tham số tốt nhất giữa các cấu hình LinearSVC và LogisticRegression
    param_grid = [
        {
            'estimator': [LinearSVC(random_state=42)],
            'estimator__C': [1.0, 5.0, 10.0],
            'estimator__class_weight': ['balanced', None]
        },
        {
            'estimator': [LogisticRegression(random_state=42, max_iter=1000)],
            'estimator__C': [1.0, 5.0, 10.0],
            'estimator__class_weight': ['balanced', None]
        }
    ]

    from sklearn.pipeline import Pipeline
    pipeline = Pipeline([('estimator', LinearSVC())])
    
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=5,
        scoring='accuracy',
        n_jobs=1
    )
    grid_search.fit(X_train, y_train)

    model = grid_search.best_estimator_.named_steps['estimator']
    print(f"Best params found: {grid_search.best_params_}")

    # ======================
    # 5. Evaluate
    # ======================
    y_pred = model.predict(X_test)

    print("=== Classification Report ===")
    report = classification_report(y_test, y_pred, zero_division=0)
    print(report)

    save_evaluation_log(
        model_name=model.__class__.__name__ + " (Tuned)",
        config_info=f"Best params: {grid_search.best_params_}, ngram_range=(1,2)",
        report_text=report
    )

    # ======================
    # 6. Save
    # ======================
    joblib.dump(model, "../models/category_model.pkl")
    joblib.dump(vectorizer, "../models/vectorizer.pkl")
    print(" Model saved!")
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import SessionLocal
from .. import models
import pandas as pd
import math

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/emotion-spending")
def emotion_spending(db: Session = Depends(get_db)):
    now = datetime.now()
    current_ym = now.strftime("%Y-%m")

    # 1. Lọc dữ liệu: CHỈ LẤY TRONG THÁNG HIỆN TẠI & Bỏ Hóa đơn (ID=5)
    transactions = db.query(
        models.Transaction.emotion,
        models.Transaction.amount
    ).filter(
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        models.Transaction.category_id != 5,
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym  # <--- Thêm lọc theo tháng
    ).all()

    if not transactions:
        return {"emotion_data": [], "correlation": 0, "insight": "Chưa có đủ dữ liệu trong tháng này để phân tích."}

    # 2. Đưa vào Pandas
    df = pd.DataFrame(transactions, columns=["emotion", "amount"])
    df["amount"] = df["amount"].abs()

    # 3. CHUẨN HÓA DỮ LIỆU:
    df["emotion"] = df["emotion"].apply(lambda x: str(x).strip().capitalize() if pd.notnull(x) else "Bình thường")

    # Map điểm số (Score) để tính toán
    score_map = {"Tích cực": 1, "Bình thường": 0.0, "Tiêu cực": -1}
    df["sentiment_score"] = df["emotion"].map(score_map).fillna(0.0)

    # 4. Tính Correlation
    if df["sentiment_score"].nunique() <= 1 or df["amount"].nunique() <= 1:
        correlation = 0.0
    else:
        correlation = df["sentiment_score"].corr(df["amount"])

    if math.isnan(correlation):
        correlation = 0.0

    # 5. Biểu đồ
    emo_summary = df.groupby("emotion")["amount"].sum().reset_index()
    emotion_data = emo_summary.to_dict(orient="records")

    # 6. Sinh Insight
    pos_spend = df[df["sentiment_score"] > 0]["amount"].sum()
    neg_spend = df[df["sentiment_score"] < 0]["amount"].sum()

    if neg_spend > pos_spend:
        insight = f"🚨 CẢNH BÁO: Tháng này bạn chi tiêu nhiều hơn lúc Tiêu cực ({neg_spend:,.0f}đ so với {pos_spend:,.0f}đ lúc Tích cực). Chỉ số tương quan là {correlation:.2f}, cho thấy dấu hiệu mua sắm bốc đồng để giải tỏa stress!"
    elif pos_spend > neg_spend:
        insight = f"✅ Tốt: Đa số khoản chi của bạn tháng này ({pos_spend:,.0f}đ) diễn ra trong trạng thái Tích cực. Tâm lý tài chính đang rất ổn định."
    else:
        insight = "Trạng thái chi tiêu của bạn trong tháng này khá cân bằng giữa các cảm xúc."

    return {
        "emotion_data": emotion_data,
        "correlation": round(correlation, 2),
        "insight": insight
    }
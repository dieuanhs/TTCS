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
def emotion_spending(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    current_ym = now.strftime("%Y-%m")

    # 1. Lọc dữ liệu: CHỈ LẤY TRONG THÁNG HIỆN TẠI & Bỏ Hóa đơn (ID=5)
    transactions = db.query(
        models.Transaction.emotion,
        models.Transaction.amount,
        models.Transaction.category_id,
        models.Transaction.transaction_time
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        models.Transaction.category_id != 5,
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).all()

    if not transactions:
        return {
            "emotion_data": [],
            "correlation": 0.0,
            "behavior_pattern": "stable",
            "insight": "Chưa có đủ dữ liệu trong tháng này để phân tích.",
            "is_sufficient": False,
            "confidence_score": 0.0,
            "risk_score": 10,
            "trend_data": [],
            "heatmap_data": []
        }

    # 2. Đưa vào Pandas
    df = pd.DataFrame(transactions, columns=["emotion", "amount", "category_id", "transaction_time"])
    df["amount"] = df["amount"].abs()

    # 3. CHUẨN HÓA DỮ LIỆU:
    df["emotion"] = df["emotion"].apply(lambda x: str(x).strip().capitalize() if pd.notnull(x) else "Bình thường")
    
    score_map = {"Tích cực": 1, "Bình thường": 0.0, "Tiêu cực": -1}
    df["sentiment_score"] = df["emotion"].map(score_map).fillna(0.0)

    # 4. Kiểm tra điều kiện dữ liệu (Data Sufficiency Check)
    total_txs = len(df)
    negative_txs = len(df[df["sentiment_score"] < 0])
    
    # Tính số ngày lịch sử có giao dịch
    df["date"] = pd.to_datetime(df["transaction_time"]).dt.strftime("%Y-%m-%d")
    unique_days = df["date"].nunique()
    
    MIN_TRANSACTIONS = 10
    MIN_NEGATIVE_RECORDS = 3
    MIN_HISTORY_DAYS = 1
    
    is_sufficient = (total_txs >= MIN_TRANSACTIONS) and (negative_txs >= MIN_NEGATIVE_RECORDS) and (unique_days >= MIN_HISTORY_DAYS)

    # 5. Tính Correlation
    if df["sentiment_score"].nunique() <= 1 or df["amount"].nunique() <= 1:
        correlation = 0.0
    else:
        correlation = df["sentiment_score"].corr(df["amount"])

    if math.isnan(correlation):
        correlation = 0.0

    # 6. Phân tích hành vi (Behavior Pattern)
    pos_spend = df[df["sentiment_score"] > 0]["amount"].sum()
    neg_spend = df[df["sentiment_score"] < 0]["amount"].sum()
    normal_spend = df[df["sentiment_score"] == 0]["amount"].sum()
    total_spend = df["amount"].sum()
    
    behavior_pattern = "stable"
    top_cat_id = None
    
    if correlation < -0.3 or (neg_spend > pos_spend * 1.5 and neg_spend > 0):
        behavior_pattern = "stress"
        stress_df = df[df["sentiment_score"] < 0]
        if not stress_df.empty:
            top_cat_id = stress_df.groupby("category_id")["amount"].sum().idxmax()
    elif correlation > 0.3 or (pos_spend > neg_spend * 1.5 and pos_spend > 0):
        behavior_pattern = "euphoric"
        euphoric_df = df[df["sentiment_score"] > 0]
        if not euphoric_df.empty:
            top_cat_id = euphoric_df.groupby("category_id")["amount"].sum().idxmax()

    cat_names = {
        1: "Ăn uống", 2: "Di chuyển", 3: "Giao lưu", 4: "Giải trí", 5: "Hóa đơn",
        6: "Học tập", 7: "Mua sắm", 8: "Phát sinh", 9: "Sức khỏe", 10: "Thu nhập"
    }
    top_cat_name = cat_names.get(top_cat_id, "Khác") if top_cat_id else "Chưa rõ"

    # 7. Confidence & Risk Score
    # Confidence phụ thuộc vào tổng số lượng GD và số GD tiêu cực
    confidence_score = min(total_txs / 20.0, 1.0) * 0.6 + min(negative_txs / 6.0, 1.0) * 0.4
    if not is_sufficient:
        confidence_score = confidence_score * 0.5
    confidence_score = round(confidence_score, 2)
    
    # Risk score (0-100)
    neg_ratio = neg_spend / total_spend if total_spend > 0 else 0
    pos_ratio = pos_spend / total_spend if total_spend > 0 else 0
    
    if behavior_pattern == "stress":
        risk_score = int(50 + (neg_ratio * 30) + (abs(min(correlation, 0.0)) * 20))
    elif behavior_pattern == "euphoric":
        risk_score = int(30 + (pos_ratio * 30) + (max(correlation, 0.0) * 20))
    else:
        risk_score = int((neg_ratio + pos_ratio) * 15 + abs(correlation) * 10)
    risk_score = min(max(risk_score, 10), 99)

    # 8. Biểu đồ dữ liệu
    emo_summary = df.groupby("emotion")["amount"].sum().reset_index()
    emotion_data = emo_summary.to_dict(orient="records")

    # Trend data (grouped by date & emotion)
    trend_df = df.groupby(["date", "emotion"])["amount"].sum().reset_index().sort_values("date")
    trend_data = trend_df.to_dict(orient="records")

    # Heatmap data (grouped by category & emotion)
    df["category_name"] = df["category_id"].map(cat_names).fillna("Khác")
    heatmap_df = df.groupby(["category_name", "emotion"])["amount"].sum().reset_index()
    heatmap_data = heatmap_df.to_dict(orient="records")

    # 9. Sinh Insight (Soften tone)
    if not is_sufficient:
        insight = "Hệ thống cần tích lũy thêm dữ liệu giao dịch của bạn trong tháng này để phân tích mối tương quan giữa cảm xúc và hành vi mua sắm một cách chính xác."
    elif behavior_pattern == "stress":
        if neg_spend > pos_spend:
            insight = f"🚨 Nhận diện xu hướng: Bạn có xu hướng tăng chi tiêu khi tâm trạng đi xuống (tháng này chi {neg_spend:,.0f}đ khi Tiêu cực so với {pos_spend:,.0f}đ khi Tích cực). "
        else:
            insight = f"🚨 Nhận diện xu hướng: Ghi nhận một số khoản chi tiêu lớn được thực hiện trong những ngày bạn cảm thấy tiêu cực. "
        if top_cat_id:
            insight += f"Đặc biệt, danh mục dễ bị ảnh hưởng bởi tâm trạng nhất là '{top_cat_name}'."
    elif behavior_pattern == "euphoric":
        insight = f"⚠️ Nhận diện xu hướng: Có dấu hiệu chi tiêu tăng cao khi tâm trạng tích cực/vui vẻ (tổng chi đạt {pos_spend:,.0f}đ). "
        if top_cat_id:
            insight += f"Bạn đặc biệt hào phóng hơn đối với danh mục '{top_cat_name}' trong những thời điểm này."
    else:
        insight = "✅ Thói quen chi tiêu của bạn rất cân bằng! Trạng thái cảm xúc vui buồn không có tác động đáng kể tới việc kiểm soát ngân sách cá nhân."

    return {
        "emotion_data": emotion_data,
        "correlation": round(correlation, 2),
        "behavior_pattern": behavior_pattern,
        "top_impulsive_category": top_cat_name if top_cat_id else None,
        "insight": insight,
        "is_sufficient": is_sufficient,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "trend_data": trend_data,
        "heatmap_data": heatmap_data
    }
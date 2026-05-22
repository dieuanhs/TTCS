from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import calendar
import pandas as pd
import math

from ..database import SessionLocal
from ..models import Transaction, Budget

router = APIRouter(prefix="/forecast", tags=["Forecast"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def forecast(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day

    # 1. Cấu hình thời gian
    _, days_in_month = calendar.monthrange(year, month)
    # Tối thiểu 7 ngày để thuật toán Burn Rate ổn định
    days_passed = current_day if current_day >= 7 else 7
    current_ym = now.strftime("%Y-%m")

    # 2. Thu nhập mục tiêu
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["income", "Thu nhập", "thu nhập"]),
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).scalar() or 0

    total_budget = db.query(func.sum(Budget.limit)).filter(
        Budget.user_id == user_id,
        Budget.month == month,
        Budget.year == year
    ).scalar() or 0
    base_income = max(total_income, total_budget)

    # 3. TÁCH CHI TIÊU: BIẾN ĐỔI VS CỐ ĐỊNH (Hóa đơn - ID: 5)
    # Chi tiêu biến đổi (Ăn uống, Mua sắm, Giải trí...)
    variable_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        Transaction.category_id != 5,
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).scalar() or 0
    variable_expense = abs(variable_expense)

    # Chi tiêu cố định thực tế đã tiêu (Hóa đơn)
    fixed_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        Transaction.category_id == 5,
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).scalar() or 0
    fixed_spent = abs(fixed_spent)


    fixed_budget = db.query(func.sum(Budget.limit)).filter(
        Budget.user_id == user_id,
        Budget.category_id == 5,
        Budget.month == month,
        Budget.year == year
    ).scalar() or 0

    # Dự báo Hóa đơn: Lấy số đã tiêu hoặc Ngân sách
    predicted_fixed = max(fixed_spent, fixed_budget)

    # 4. TÍNH TOÁN YẾU TỐ CẢM XÚC THEO DANH MỤC
    var_txs = db.query(Transaction.emotion, Transaction.amount, Transaction.transaction_time).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        Transaction.category_id != 5,
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).order_by(Transaction.transaction_time.asc()).all()

    correlation_strength = 0.0
    emotion_trend_score = 0.0
    confidence_score = 0.4
    
    if var_txs:
        df_tx = pd.DataFrame(var_txs, columns=["emotion", "amount", "time"])
        df_tx["amount"] = df_tx["amount"].abs()
        df_tx["emotion"] = df_tx["emotion"].apply(lambda x: str(x).strip().capitalize() if pd.notnull(x) else "Bình thường")
        score_map = {"Tích cực": 1, "Bình thường": 0.0, "Tiêu cực": -1}
        df_tx["sentiment_score"] = df_tx["emotion"].map(score_map).fillna(0.0)
        
        # Calculate Correlation
        if df_tx["sentiment_score"].nunique() > 1 and df_tx["amount"].nunique() > 1:
            correlation_strength = df_tx["sentiment_score"].corr(df_tx["amount"])
            if math.isnan(correlation_strength): correlation_strength = 0.0
            
        # Confidence Score
        n_txs = len(df_tx)
        if n_txs < 5:
            confidence_score = 0.4
        elif n_txs <= 20:
            confidence_score = 0.7
        else:
            confidence_score = 1.0
            
        # EMA
        df_tx["date"] = pd.to_datetime(df_tx["time"]).dt.date
        daily_sentiment = df_tx.groupby("date")["sentiment_score"].mean().tail(3).values
        if len(daily_sentiment) == 3:
            emotion_trend_score = 0.5 * daily_sentiment[-1] + 0.3 * daily_sentiment[-2] + 0.2 * daily_sentiment[-3]
        elif len(daily_sentiment) == 2:
            emotion_trend_score = 0.6 * daily_sentiment[-1] + 0.4 * daily_sentiment[-2]
        elif len(daily_sentiment) == 1:
            emotion_trend_score = daily_sentiment[-1]

    # 5. DỰ BÁO CHI TIẾT TỪNG DANH MỤC
    cat_expenses = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).group_by(Transaction.category_id).all()

    cat_names = {
        1: "Ăn uống", 2: "Di chuyển", 3: "Giao lưu", 4: "Giải trí", 5: "Hóa đơn",
        6: "Học tập", 7: "Mua sắm", 8: "Phát sinh", 9: "Sức khỏe", 10: "Thu nhập"
    }
    
    category_sensitivity = {
        1: 0.6, 2: 0.3, 3: 0.5, 4: 0.5, 5: 0.1,
        6: 0.2, 7: 0.8, 8: 0.4, 9: 0.3, 10: 0.0
    }

    category_forecast = {}
    predicted_variable = 0.0
    emotion_reasons = []
    
    max_increase_ratio = 0
    max_increase_cat = ""

    for c_id, amt in cat_expenses:
        c_name = cat_names.get(c_id, "Khác")
        actual_amt = abs(amt)

        if c_id == 5:
            # Hóa đơn không nhân theo ngày
            category_forecast[c_name] = predicted_fixed
        else:
            sens = category_sensitivity.get(c_id, 0.4)
            # Công thức Adaptive Emotion Factor cho danh mục
            raw_factor = 1.0 + (correlation_strength * emotion_trend_score * confidence_score * sens * 0.4)
            cat_factor = max(0.9, min(raw_factor, 1.15))
            
            projected = (actual_amt / days_passed) * days_in_month * cat_factor
            category_forecast[c_name] = projected
            predicted_variable += projected
            
            increase_ratio = cat_factor - 1.0
            if increase_ratio > max_increase_ratio:
                max_increase_ratio = increase_ratio
                max_increase_cat = c_name

    if not category_forecast or (len(category_forecast) == 1 and "Chưa có dữ liệu" in category_forecast):
        category_forecast = {"Chưa có dữ liệu": 0}

    # Tổng dự báo = (Dự báo biến đổi đã áp dụng cảm xúc) + Tiền hóa đơn cố định
    predicted_expense = predicted_variable + predicted_fixed
    projected_balance = base_income - predicted_expense

    # 6. Sinh Logic Lời khuyên AI (AI Insight & Reasons)
    if max_increase_ratio > 0.03:
        emotion_reasons.append(f"Chi tiêu cho '{max_increase_cat}' dự kiến tăng ({(max_increase_ratio)*100:.1f}%) do ảnh hưởng của tâm lý.")
        
        if emotion_trend_score < -0.2:
            emotion_reasons.append("Tâm trạng tiêu cực xuất hiện liên tục trong những ngày gần đây.")
        elif emotion_trend_score > 0.2:
            emotion_reasons.append("Tâm trạng tích cực xuất hiện nhiều trong những ngày gần đây.")
            
        if correlation_strength < -0.3:
            emotion_reasons.append(f"Dữ liệu lịch sử cho thấy bạn thường tăng chi tay khi bị stress.")
        elif correlation_strength > 0.3:
            emotion_reasons.append(f"Bạn thường có xu hướng chi tiêu bốc đồng vào lúc vui vẻ.")

    # Lời khuyên chung
    daily_average_var = variable_expense / days_passed
    if base_income == 0:
        ai_text = "Bạn chưa thiết lập ngân sách hoặc thu nhập tháng này nên AI không thể đưa ra cảnh báo chính xác."
    elif predicted_expense > base_income:
        ai_text = f"🚨 CẢNH BÁO ĐỎ: Tốc độ chi tiêu đang ở mức {daily_average_var:,.0f}đ/ngày. Dự kiến cuối tháng bạn sẽ ÂM {abs(projected_balance):,.0f}đ. Hãy thắt chặt chi tiêu ngay!"
    elif predicted_expense > base_income * 0.8:
        ai_text = "⚠️ Chú ý: Dự báo bạn sẽ tiêu hết hơn 80% ngân sách tháng này. Hãy hạn chế các khoản mua sắm không cần thiết để giữ an toàn tài chính."
    else:
        ai_text = f"✅ Tuyệt vời! Bạn đang quản lý rất tốt. Dự kiến cuối tháng bạn để ra được {projected_balance:,.0f}đ tiền tiết kiệm."

    return {
        "predicted_income": base_income,
        "predicted_expense": predicted_expense,
        "projected_balance": projected_balance,
        "category_forecast": category_forecast,
        "emotion_reasons": emotion_reasons,
        "ai_prediction_text": ai_text
    }
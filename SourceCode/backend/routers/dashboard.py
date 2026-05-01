from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def dashboard(db: Session = Depends(get_db)):
    now = datetime.now()
    current_ym = now.strftime("%Y-%m")

    # 1. TỔNG THU & CHI (Chỉ lấy trong tháng hiện tại)
    income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.type.in_(["income", "Thu nhập", "thu nhập"]),
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).scalar() or 0

    expense = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).scalar() or 0
    expense = abs(expense)

    net_balance = income - expense

    # 2. CHI TIÊU THEO DANH MỤC (Cho biểu đồ Tròn)
    cat_data = db.query(
        models.Transaction.category_id,
        func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).group_by(models.Transaction.category_id).all()

    # Ánh xạ ID sang tên danh mục
    cat_names = {1: "Ăn uống", 2: "Di chuyển", 3: "Mua sắm", 4: "Giải trí", 5: "Hóa đơn"}
    expense_by_category = {}

    for c_id, amt in cat_data:
        name = cat_names.get(c_id, "Khác")
        expense_by_category[name] = abs(amt)

    if not expense_by_category:
        expense_by_category = {"Chưa có dữ liệu": 1}

    # 3. CHI TIÊU THEO CẢM XÚC (Cho biểu đồ Cột)
    emo_data = db.query(
        models.Transaction.emotion,
        func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", models.Transaction.transaction_time) == current_ym
    ).group_by(models.Transaction.emotion).all()

    # Mồi sẵn 3 cảm xúc mặc định ở mức 0 để biểu đồ luôn hiện 3 cột
    emotion_spending = {
        "Tích cực": 0,
        "Tiêu cực": 0,
        "Bình thường": 0
    }
    tieucuc_spending = 0

    for emo, amt in emo_data:
        if not emo:
            continue

        e_name = emo.strip().capitalize()
        val = abs(amt)

        if e_name in emotion_spending:
            emotion_spending[e_name] += val
        else:
            emotion_spending[e_name] = val

        if e_name == "Tiêu cực":
            tieucuc_spending += val

    # 4. AI INSIGHT: Thuật toán Cảnh báo chi tiêu bốc đồng
    ai_insight = "✅ Tuyệt vời! Hiện tại bạn đang quản lý chi tiêu rất ổn định. Hãy tiếp tục phát huy nhé!"

    if expense > 0:
        tieucuc_ratio = (tieucuc_spending / expense) * 100
        if tieucuc_ratio > 30:
            ai_insight = f"🚨 CẢNH BÁO: {tieucuc_ratio:.0f}% chi tiêu tháng này diễn ra lúc bạn có cảm xúc 'Tiêu cực'. Bạn đang có xu hướng mua sắm bốc đồng để giải tỏa stress. Hãy thắt chặt ví lại nhé!"
        elif tieucuc_spending > 0:
            ai_insight = f"💡 Lưu ý nhỏ: Bạn đã tiêu {tieucuc_spending:,.0f}đ trong lúc tâm trạng không tốt. Cân nhắc tìm các phương pháp giải trí miễn phí như đi dạo thay vì tiêu tiền nhé."

    return {
        "total_income": income,
        "total_expense": expense,
        "net_balance": net_balance,
        "expense_by_category": expense_by_category,
        "emotion_spending": emotion_spending,
        "ai_insight": ai_insight
    }
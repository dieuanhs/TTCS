from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import calendar

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

    # 4. THUẬT TOÁN DỰ BÁO
    # Tốc độ đốt tiền chỉ tính trên các khoản chi tiêu biến đổi
    daily_average_var = variable_expense / days_passed
    predicted_variable = daily_average_var * days_in_month

    # Tổng dự báo = (Trung bình biến đổi * số ngày) + Tiền hóa đơn cố định
    predicted_expense = predicted_variable + predicted_fixed
    projected_balance = base_income - predicted_expense

    # 5. Dự báo chi tiết từng Danh mục
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
    category_forecast = {}

    for c_id, amt in cat_expenses:
        c_name = cat_names.get(c_id, "Khác")
        actual_amt = abs(amt)

        if c_id == 5:
            # Hóa đơn không nhân theo ngày
            category_forecast[c_name] = predicted_fixed
        else:
            # Các mục khác dự báo theo Burn Rate
            category_forecast[c_name] = (actual_amt / days_passed) * days_in_month

    if not category_forecast or (len(category_forecast) == 1 and "Chưa có dữ liệu" in category_forecast):
        category_forecast = {"Chưa có dữ liệu": 0}

    # 6. Lời khuyên AI (AI Prediction)
    if base_income == 0:
        ai_text = "Bạn chưa thiết lập ngân sách hoặc thu nhập tháng này nên AI không thể đưa ra cảnh báo chính xác."
    elif predicted_expense > base_income:
        ai_text = f"🚨 CẢNH BÁO ĐỎ: Tốc độ chi tiêu biến đổi đang ở mức {daily_average_var:,.0f}đ/ngày. Dự kiến cuối tháng bạn sẽ ÂM {abs(projected_balance):,.0f}đ (đã bao gồm các hóa đơn cố định). Hãy thắt chặt chi tiêu ngay!"
    elif predicted_expense > base_income * 0.8:
        ai_text = "⚠️ Chú ý: Dự báo bạn sẽ tiêu hết hơn 80% ngân sách tháng này. Hãy hạn chế các khoản mua sắm không cần thiết để giữ an toàn tài chính."
    else:
        ai_text = f"✅ Tuyệt vời! Bạn đang quản lý rất tốt. Dự kiến sau khi trừ các hóa đơn cố định, bạn vẫn để ra được {projected_balance:,.0f}đ tiền tiết kiệm."

    return {
        "predicted_income": base_income,
        "predicted_expense": predicted_expense,
        "projected_balance": projected_balance,
        "category_forecast": category_forecast,
        "ai_prediction_text": ai_text
    }
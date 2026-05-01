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
def forecast(db: Session = Depends(get_db)):
    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day

    # 1. Số ngày trong tháng & Số ngày đã qua (Tối thiểu là 7 để tránh nhiễu)
    _, days_in_month = calendar.monthrange(year, month)
    days_passed = current_day if current_day >= 7 else 7
    current_ym = now.strftime("%Y-%m")

    # 2. Tính Tổng Thu Nhập (Lấy Ngân sách hoặc Thu nhập thực tế, cái nào lớn hơn)
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "income",
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).scalar() or 0

    total_budget = db.query(func.sum(Budget.limit)).filter(
        Budget.month == month,
        Budget.year == year
    ).scalar() or 0

    base_income = max(total_income, total_budget)

    # 3. Tính Tổng Chi Tiêu từ đầu tháng
    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).scalar() or 0
    total_expense = abs(total_expense)

    # 4. THUẬT TOÁN DỰ BÁO CỐT LÕI
    daily_average = total_expense / days_passed
    predicted_expense = daily_average * days_in_month
    projected_balance = base_income - predicted_expense

    # 5. Dự báo chi tiết cho từng Danh mục (Để vẽ biểu đồ)
    cat_expenses = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        func.strftime("%Y-%m", Transaction.transaction_time) == current_ym
    ).group_by(Transaction.category_id).all()

    # Ánh xạ Category ID -> Tên
    cat_names = {1: "Ăn uống", 2: "Di chuyển", 3: "Mua sắm", 4: "Giải trí", 5: "Hóa đơn"}
    category_forecast = {}

    for c_id, amt in cat_expenses:
        c_name = cat_names.get(c_id, "Khác")
        # Dự báo danh mục = (Đã tiêu danh mục / số ngày) * tổng số ngày tháng
        cat_predicted = (abs(amt) / days_passed) * days_in_month
        category_forecast[c_name] = cat_predicted

    # Nếu chưa tiêu gì, cho mảng rỗng để Frontend không bị lỗi biểu đồ
    if not category_forecast:
        category_forecast = {"Chưa có dữ liệu": 0}

    # 6. Tạo lời khuyên AI động (AI Prediction)
    if base_income == 0:
        ai_text = "Bạn chưa thiết lập ngân sách hoặc thu nhập tháng này nên AI không thể đưa ra cảnh báo chính xác."
    elif predicted_expense > base_income:
        ai_text = f"🚨 CẢNH BÁO ĐỎ: Tốc độ tiêu tiền hiện tại quá nhanh ({daily_average:,.0f}đ/ngày). Dự kiến cuối tháng bạn sẽ ÂM {abs(projected_balance):,.0f}đ. Hãy đóng băng các khoản mua sắm ngay!"
    elif predicted_expense > base_income * 0.8:
        ai_text = "⚠️ Chú ý: Bạn dự kiến sẽ tiêu hết 80% ngân sách trong tháng này. Hãy rà soát lại các khoản chi phí giải trí nhé."
    else:
        ai_text = f"✅ Tuyệt vời! Bạn đang quản lý rất tốt. Dự kiến cuối tháng bạn sẽ để ra được khoản tiết kiệm {projected_balance:,.0f}đ."

    return {
        "predicted_income": base_income,
        "predicted_expense": predicted_expense,
        "projected_balance": projected_balance,
        "category_forecast": category_forecast,
        "ai_prediction_text": ai_text
    }
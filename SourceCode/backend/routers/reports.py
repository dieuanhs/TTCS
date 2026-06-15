from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import calendar

from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_reports(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    year = now.year
    month = now.month

    # Tính toán ranh giới thời gian cho tháng hiện tại
    start_of_month = datetime(year, month, 1, 0, 0, 0)
    _, last_day = calendar.monthrange(year, month)
    end_of_month = datetime(year, month, last_day, 23, 59, 59)

    # Từ điển Danh mục
    cat_names = {
        1: "Ăn uống", 2: "Di chuyển", 3: "Giao lưu", 4: "Giải trí", 5: "Hóa đơn",
        6: "Học tập", 7: "Mua sắm", 8: "Phát sinh", 9: "Sức khỏe", 10: "Thu nhập"
    }

    # --- 1. TỔNG QUAN THÁNG NÀY ---
    total_income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type.in_(["income", "Thu nhập", "thu nhập"]),
        models.Transaction.transaction_time >= start_of_month,
        models.Transaction.transaction_time <= end_of_month
    ).scalar() or 0

    total_expense = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        models.Transaction.transaction_time >= start_of_month,
        models.Transaction.transaction_time <= end_of_month
    ).scalar() or 0
    total_expense = abs(total_expense)

    net_balance = total_income - total_expense

    # --- 2. XU HƯỚNG 5 THÁNG GẦN NHẤT ---
    monthly_trend = {}
    for i in range(4, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1

        # Ranh giới thời gian cho từng tháng trong vòng lặp
        start_i = datetime(y, m, 1, 0, 0, 0)
        _, last_day_i = calendar.monthrange(y, m)
        end_i = datetime(y, m, last_day_i, 23, 59, 59)

        month_label = f"T{m}"

        monthly_exp = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
            models.Transaction.transaction_time >= start_i,
            models.Transaction.transaction_time <= end_i
        ).scalar() or 0
        monthly_trend[month_label] = abs(monthly_exp)

    # --- 3. CHI TIÊU THEO DANH MỤC THÁNG NÀY ---
    cat_expenses = db.query(
        models.Transaction.category_id,
        func.sum(models.Transaction.amount),
        func.count(models.Transaction.transaction_id)
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        models.Transaction.transaction_time >= start_of_month,
        models.Transaction.transaction_time <= end_of_month
    ).group_by(models.Transaction.category_id).all()

    categories = {}
    spending_details = []
    max_cat_name = "Chưa có"
    max_cat_amount = 0

    for c_id, amt, count in cat_expenses:
        name = cat_names.get(c_id, "Khác")
        amount = abs(amt)
        categories[name] = amount

        # Lấy các mô tả giao dịch trong danh mục để phân tích chi tiết
        txs = db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.category_id == c_id,
            models.Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
            models.Transaction.transaction_time >= start_of_month,
            models.Transaction.transaction_time <= end_of_month
        ).all()
        descriptions = [tx.description for tx in txs if tx.description]

        # Lấy ngân sách (Budget) của danh mục
        budget = db.query(models.Budget).filter(
            models.Budget.user_id == user_id,
            models.Budget.category_id == c_id,
            models.Budget.month == month,
            models.Budget.year == year
        ).first()

        limit = budget.limit if budget else 0
        diff = limit - amount

        if limit == 0:
            status = "Chưa đặt ngân sách"
        elif diff < 0:
            status = "Vượt hạn mức"
        else:
            status = "An toàn"

        spending_details.append({
            "cat": name,
            "count": count,
            "amt": amount,
            "lim": limit,
            "status": status,
            "diff": diff,
            "descriptions": descriptions
        })

        if amount > max_cat_amount:
            max_cat_amount = amount
            max_cat_name = name

    # Sắp xếp bảng chi tiết từ cao xuống thấp
    spending_details.sort(key=lambda x: x['amt'], reverse=True)
    if not categories:
        categories = {"Chưa có dữ liệu": 1}

    # --- 4. AI INSIGHT ---
    if total_expense == 0:
        ai_insight = "Bạn chưa có khoản chi tiêu nào trong tháng này. Hãy cập nhật thêm giao dịch nhé!"
    else:
        ai_insight = f"Bạn đang tiêu nhiều tiền nhất vào mục **{max_cat_name}** ({max_cat_amount:,.0f} VND). Hãy cân nhắc cắt giảm chi phí ở khoản này để bảo vệ ngân sách nhé!"

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "monthly_trend": monthly_trend,
        "categories": categories,
        "spending_details": spending_details,
        "ai_insight": ai_insight
    }
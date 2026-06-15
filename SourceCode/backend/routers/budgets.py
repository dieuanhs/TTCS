from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import calendar

from ..database import SessionLocal
from ..models import Budget, Transaction
from .. import schemas

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# ---------------------------
# DATABASE CONNECTION
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# CREATE CATEGORY BUDGET
# ---------------------------
@router.post("/")
def create_budget(data: schemas.BudgetCreate, db: Session = Depends(get_db)):
    budget = Budget(
        user_id=data.user_id,
        category_id=data.category_id,
        limit=data.limit,
        month=data.month,
        year=data.year
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


# ---------------------------
# GET BUDGETS OF A MONTH
# ---------------------------
@router.get("/monthly")
def get_monthly_budget(user_id: int, month: int, year: int, db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == month,
        Budget.year == year
    ).all()

    total_budget = sum(b.limit for b in budgets)

    return {
        "month": month,
        "year": year,
        "total_budget": total_budget,
        "categories": budgets
    }


# ---------------------------
# CATEGORY BUDGET PROGRESS
# ---------------------------
@router.get("/progress")
def category_progress(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    year = now.year
    month = now.month

    # Tính toán ranh giới ngày tháng độc lập với Database
    start_of_month = datetime(year, month, 1, 0, 0, 0)
    _, last_day = calendar.monthrange(year, month)
    end_of_month = datetime(year, month, last_day, 23, 59, 59)

    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == month,
        Budget.year == year
    ).all()

    result = []

    for b in budgets:
        # Lọc an toàn trên MySQL/SQLite + Chuẩn hóa mapping "Chi tiêu"
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == b.category_id,
            Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
            Transaction.transaction_time >= start_of_month,
            Transaction.transaction_time <= end_of_month
        ).scalar() or 0

        result.append({
            "category_id": b.category_id,
            "limit": b.limit,
            "spent": abs(spent),
            "remaining": b.limit - abs(spent)
        })

    return result


# ---------------------------
# MONTHLY BUDGET OVERVIEW
# ---------------------------
@router.get("/overview")
def budget_overview(user_id: int, db: Session = Depends(get_db)):
    now = datetime.now()
    year = now.year
    month = now.month

    # Tính toán ranh giới ngày tháng độc lập với Database
    start_of_month = datetime(year, month, 1, 0, 0, 0)
    _, last_day = calendar.monthrange(year, month)
    end_of_month = datetime(year, month, last_day, 23, 59, 59)

    total_budget = db.query(func.sum(Budget.limit)).filter(
        Budget.user_id == user_id,
        Budget.month == month,
        Budget.year == year
    ).scalar() or 0

    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type.in_(["expense", "Chi tiêu", "chi tiêu"]),
        Transaction.transaction_time >= start_of_month,
        Transaction.transaction_time <= end_of_month
    ).scalar() or 0

    spent = abs(total_spent)

    return {
        "total_budget": total_budget,
        "total_spent": spent,
        "remaining": total_budget - spent
    }
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ..models import Transaction, Budget
from ..database import SessionLocal

router = APIRouter(prefix="/reports", tags=["Reports"])


# -----------------------------
# DATABASE DEPENDENCY
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# DASHBOARD SUMMARY
# -----------------------------
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    now = datetime.now()

    total_budget = db.query(func.sum(Budget.limit)).filter(
        Budget.month == now.month,
        Budget.year == now.year
    ).scalar() or 0

    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "expense",
        func.strftime("%Y-%m", Transaction.transaction_time)
        == now.strftime("%Y-%m")
    ).scalar() or 0

    spent = abs(total_spent)

    percent = (spent / total_budget) * 100 if total_budget else 0

    alert = None
    if percent >= 80:
        alert = "Warning: You spent over 80% of your budget"

    return {
        "budget_limit": total_budget,
        "spent": spent,
        "remaining": total_budget - spent,
        "percent_used": percent,
        "alert": alert
    }


# -----------------------------
# EXPENSE BY CATEGORY
# -----------------------------
@router.get("/category")
def expense_by_category(db: Session = Depends(get_db)):

    data = db.query(
        Transaction.category_id,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type == "expense"
    ).group_by(
        Transaction.category_id
    ).all()

    return [
        {"category": c, "amount": abs(a)}
        for c, a in data
    ]


# -----------------------------
# EMOTION SPENDING
# -----------------------------
@router.get("/emotion")
def emotion_spending(db: Session = Depends(get_db)):

    data = db.query(
        Transaction.emotion,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type == "expense"
    ).group_by(
        Transaction.emotion
    ).all()

    return [
        {"emotion": e, "amount": abs(a)}
        for e, a in data
    ]


# -----------------------------
# MONTHLY TREND REPORT
# -----------------------------
@router.get("/monthly")
def monthly_report(db: Session = Depends(get_db)):

    data = db.query(
        func.strftime("%Y-%m", Transaction.transaction_time),
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type == "expense"
    ).group_by(
        func.strftime("%Y-%m", Transaction.transaction_time)
    ).all()

    return [
        {"month": m, "amount": abs(a)}
        for m, a in data
    ]
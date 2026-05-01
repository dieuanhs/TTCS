from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

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
def get_monthly_budget(month: int, year: int, db: Session = Depends(get_db)):

    budgets = db.query(Budget).filter(
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
def category_progress(db: Session = Depends(get_db)):

    now = datetime.now()

    budgets = db.query(Budget).filter(
        Budget.month == now.month,
        Budget.year == now.year
    ).all()

    result = []

    for b in budgets:

        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == b.category_id,
            # Transaction.type == "expense",
             func.strftime("%Y-%m", Transaction.transaction_time)
            == now.strftime("%Y-%m")
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
def budget_overview(db: Session = Depends(get_db)):

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

    return {
        "total_budget": total_budget,
        "total_spent": spent,
        "remaining": total_budget - spent
    }
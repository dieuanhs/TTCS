from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from . import models, schemas


def get_dashboard(db: Session):
    now = datetime.now()
    month_str = now.strftime("%Y-%m")

    # Tính tổng thu nhập và chi tiêu trong tháng
    income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.transaction_type == "income",
        models.Transaction.transaction_time.like(f"{month_str}%")
    ).scalar() or 0

    expense = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.transaction_type == "expense",
        models.Transaction.transaction_time.like(f"{month_str}%")
    ).scalar() or 0

    return {
        "balance": income - expense,
        "total_income": income,
        "total_expense": expense,
        "month": month_str
    }
# TRANSACTIONS
def get_transactions(db: Session):
    return db.query(models.Transaction).order_by(
        models.Transaction.transaction_time.desc()
    ).all()


def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_transaction(db: Session, transaction_id: int):

    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id
    ).first()

    if transaction:
        db.delete(transaction)
        db.commit()

    return transaction


# BUDGET
def create_budget(db: Session, data: schemas.BudgetCreate):

    budget = models.Budget(
        category=data.category,
        limit=data.limit,
        month=data.month,
        year=data.year
    )

    db.add(budget)
    db.commit()
    db.refresh(budget)

    return budget


def get_monthly_budgets(db: Session, month: int, year: int):

    return db.query(models.Budget).filter(
        models.Budget.month == month,
        models.Budget.year == year
    ).all()


def get_total_budget(db: Session):

    now = datetime.now()

    return db.query(func.sum(models.Budget.limit)).filter(
        models.Budget.month == now.month,
        models.Budget.year == now.year
    ).scalar() or 0


def get_category_budget(db: Session, category: str, month: int, year: int):

    return db.query(models.Budget).filter(
        models.Budget.category == category,
        models.Budget.month == month,
        models.Budget.year == year
    ).first()
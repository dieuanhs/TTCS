from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import SessionLocal
from ..models import Transaction

router = APIRouter(prefix="/forecast", tags=["Forecast"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def forecast(db: Session = Depends(get_db)):

    # Monthly income
    income_data = db.query(
        func.strftime("%Y-%m", Transaction.transaction_time),
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type == "income"
    ).group_by(
        func.strftime("%Y-%m", Transaction.transaction_time)
    ).all()

    # Monthly expense
    expense_data = db.query(
        func.strftime("%Y-%m", Transaction.transaction_time),
        func.sum(Transaction.amount)
    ).filter(
        Transaction.type == "expense"
    ).group_by(
        func.strftime("%Y-%m", Transaction.transaction_time)
    ).all()

    income_values = [x[1] for x in income_data]
    expense_values = [abs(x[1]) for x in expense_data]

    avg_income = sum(income_values) / len(income_values) if income_values else 0
    avg_expense = sum(expense_values) / len(expense_values) if expense_values else 0

    projected_balance = avg_income - avg_expense

    return {
        "predicted_income": avg_income,
        "predicted_expense": avg_expense,
        "projected_balance": projected_balance
    }
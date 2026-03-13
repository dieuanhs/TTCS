from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import SessionLocal
from ..models import Transaction
from .. import schemas

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# GET ALL TRANSACTIONS
# -----------------------------
@router.get("/")
def read_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).order_by(
        Transaction.transaction_time.desc()
    ).all()

    return transactions


# -----------------------------
# CREATE TRANSACTION
# -----------------------------
@router.post("/")
def create_transaction(
        data: schemas.TransactionCreate,
        db: Session = Depends(get_db)
):
    transaction = Transaction(
        user_id=data.user_id,
        description=data.description,
        category_id=data.category_id,
        amount=data.amount,
        type=data.type,
        emotion=data.emotion,
        transaction_time=datetime.now()
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


# -----------------------------
# DELETE TRANSACTION
# -----------------------------
@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()

    return {"message": "Transaction deleted"}


# -----------------------------
# ANALYZE TEXT TRANSACTION
# -----------------------------
@router.post("/analyze")
def analyze_transaction(data: dict):
    text = data.get("text", "").lower()

    category = "Other"
    emotion = "Neutral"
    amount = 0

    if "coffee" in text:
        category = "Drink"
        amount = 45000

    if "ăn" in text or "food" in text:
        category = "Food"

    if "taxi" in text or "grab" in text:
        category = "Transport"

    if "mệt" in text:
        emotion = "Tired"

    if "stress" in text:
        emotion = "Stress"

    return {
        "amount": amount,
        "category": category,
        "emotion": emotion
    }
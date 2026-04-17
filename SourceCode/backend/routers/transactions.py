import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import SessionLocal
from ..models import Transaction
from .. import schemas

from ai.src.ai_models import predict_all
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
# SMART INPUT (AI INTEGRATION THỰC SỰ)
@router.post("/smart-input", response_model=schemas.SmartInputResponse)
def smart_input_transaction(request: schemas.SmartInputRequest):
    """
    Bước 1: Gửi câu nói vào đây
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Văn bản không được để trống!")

    try:
        # Chuyền văn bản cho hàm predict_all của file ai_models.py
        ai_result = predict_all(request.text)

        # Kiểm tra nếu AI báo lỗi trong quá trình xử lý (như lỗi Regex, Tokenizer)
        if "error" in ai_result:
            raise HTTPException(status_code=500, detail=ai_result["error"])

        return ai_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tích hợp AI: {str(e)}")


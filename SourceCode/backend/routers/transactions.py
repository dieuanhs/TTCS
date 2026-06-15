import os
import sys
from datetime import datetime, timedelta
from typing import Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
# GET ALL TRANSACTIONS (THEO BỘ LỌC THỜI GIAN)
# -----------------------------
@router.get("/")
def read_transactions(
        user_id: int,
        time_range: Optional[str] = "all",
        db: Session = Depends(get_db)
):
    # 1. Khởi tạo câu truy vấn cơ bản
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    # 2. Xử lý bộ lọc thời gian
    now = datetime.now()

    if time_range == "week":
        # Lùi lại 7 ngày
        one_week_ago = now - timedelta(days=7)
        query = query.filter(Transaction.transaction_time >= one_week_ago)

    elif time_range == "month":
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Transaction.transaction_time >= start_of_month)

    # Nếu time_range == "all", giữ nguyên query không filter thêm

    # 3. Sắp xếp mới nhất lên đầu
    transactions = query.order_by(Transaction.transaction_time.desc()).all()

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
# SMART INPUT
# -----------------------------
@router.post("/smart-input", response_model=schemas.SmartInputResponse)
def smart_input_transaction(request: schemas.SmartInputRequest):
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
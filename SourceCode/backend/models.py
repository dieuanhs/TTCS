from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base


# =========================
# 1. MODEL NGƯỜI DÙNG (Users)
# =========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Khai báo độ dài cụ thể cho dialect MySQL
    full_name = Column(String(100), index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# =========================
# 2. MODEL DANH MỤC (Categories)
# =========================
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)

    category_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # income / expense


# =========================
# 3. MODEL GIAO DỊCH (Transactions)
# =========================
class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Thêm cấu hình ON DELETE CASCADE để dọn dẹp sạch dữ liệu liên quan khi xóa User
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)


    description = Column(Text, nullable=False)

    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)  # income / expense
    emotion = Column(String(50), default="Bình thường")

    # Cho phép ghi nhận thời gian giao dịch linh hoạt
    transaction_time = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# =========================
# 4. MODEL NGÂN SÁCH (Budgets)
# =========================
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)

    limit = Column(Float, default=0.0, nullable=False)

    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
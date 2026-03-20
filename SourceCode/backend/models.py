from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from .database import Base
from datetime import datetime


# =========================
# USERS
# =========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

   #$ created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# CATEGORIES
# =========================
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)

    category_name = Column(String)
    type = Column(String)  # income / expense


# TRANSACTIONS
class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))

    description = Column(String)   # ✅ thêm để khớp router

    amount = Column(Float)

    type = Column(String)  # income / expense

    emotion = Column(String)

    transaction_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)


# BUDGETS
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.user_id"))

    category_id = Column(Integer, ForeignKey("categories.category_id"))

    limit = Column(Float)

    month = Column(Integer)
    year = Column(Integer)
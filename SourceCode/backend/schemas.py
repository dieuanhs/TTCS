from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    model_config = ConfigDict(from_attributes=True)

# TRANSACTIONS

class TransactionBase(BaseModel):
    user_id: int
    category_id: int
    description: str
    amount: float
    type: str
    emotion: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    transaction_time: datetime

    class Config:
        from_attributes = True


# BUDGETS

class BudgetBase(BaseModel):
    category_id: int
    limit: float
    month: int
    year: int


class BudgetCreate(BudgetBase):
    pass


class Budget(BudgetBase):
    id: int

    class Config:
        from_attributes = True
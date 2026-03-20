from fastapi import FastAPI

from sqlalchemy.orm import Session
from .database import engine
from . import models, crud, schemas
from .routers import dashboard, transactions, budgets, reports, forecast, users

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Finance API")

app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(reports.router)
app.include_router(forecast.router)
app.include_router(users.router)


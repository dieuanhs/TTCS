from fastapi import FastAPI
from .database import engine
from . import models
from .routers import dashboard, transactions, budgets, reports, forecast

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Finance API")

app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(reports.router)
app.include_router(forecast.router)
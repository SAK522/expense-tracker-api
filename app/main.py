"""
Application entry point.

Run locally:   uvicorn app.main:app --reload
Docs:          http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from app.database import init_db
from app import models  # noqa: F401  (registers tables with Base)
from app.routers import auth, transactions, summary

# Creates missing tables on startup. (A migration tool like Alembic is the
# "future work" upgrade for evolving schemas.)
init_db()

app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A secured REST API for personal income and expense tracking. "
        "Sign up, log in to get a JWT, then click **Authorize** to call the "
        "protected endpoints."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(summary.router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

"""
Application entry point.

Run locally:   uvicorn app.main:app --reload
  Web app (for everyone):       http://127.0.0.1:8000/
  Interactive API docs (devs):  http://127.0.0.1:8000/docs
"""
import pathlib

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.database import init_db
from app import models  # noqa: F401  (registers tables with Base)
from app.routers import auth, transactions, summary

WEB_PAGE = pathlib.Path(__file__).resolve().parent / "web" / "index.html"

# Creates missing tables on startup. (A migration tool like Alembic is the
# "future work" upgrade for evolving schemas.)
init_db()

app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A secured REST API for personal income and expense tracking. "
        "Sign up, log in to get a JWT, then click **Authorize** to call the "
        "protected endpoints. Prefer clicking to coding? The web app is at [/](/)."
    ),
    version="1.1.0",
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(summary.router)


@app.get("/", include_in_schema=False)
def web_app():
    """The friendly web interface: track income and spending without writing code."""
    return FileResponse(WEB_PAGE, media_type="text/html")


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

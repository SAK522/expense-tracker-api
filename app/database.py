"""
Database connection layer: engine, session factory, Base, and get_db().
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

DATABASE_URL = settings.sqlalchemy_url

# SQLite refuses cross-thread use by default; FastAPI uses threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping drops dead connections (free-tier Postgres closes idle ones).
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()


def get_db():
    """Give a route a session, and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

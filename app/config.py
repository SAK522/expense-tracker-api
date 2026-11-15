"""
Central place for all settings.

WHY this file exists:
Secrets (database URL, JWT secret key) must NOT be hard-coded in the code,
because the code goes to GitHub where anyone can read it. Instead we read
them from "environment variables" (values the operating system or the deploy
platform holds). This class loads those values once and the rest of the app
imports `settings` from here.

WHAT it does:
pydantic-settings reads a `.env` file during local development, and reads
real environment variables in production (Render/Railway). Same code, two
sources — you never change the code to deploy.
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Where the database lives. Defaults to a local SQLite file for easy dev.
    # In production you set DATABASE_URL to your PostgreSQL URL instead.
    database_url: str = "sqlite:///./expense.db"
    # Optional PostgreSQL schema. Lets several apps share one database (e.g. Render's single
    # free Postgres) while keeping their tables completely separate.
    database_schema: Optional[str] = None

    # The secret used to sign JWT tokens. Anyone who knows it can forge logins,
    # so in production you override it with a long random value.
    jwt_secret: str = "dev-only-insecure-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Tells pydantic to read a file named `.env` if it exists.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_url(self) -> str:
        """Normalise the database URL for SQLAlchemy.

        - Render/Heroku hand out 'postgres://', which SQLAlchemy doesn't accept.
        - The driver is named explicitly ('+psycopg2'): SQLAlchemy 2.1 changed its default
          PostgreSQL driver, so relying on the default would break when upgrading.
        """
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg2://" + url[len(prefix):]
        return url


# One shared instance the whole app imports.
settings = Settings()

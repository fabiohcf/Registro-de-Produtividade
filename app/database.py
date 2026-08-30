# app/database.py

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()


# ==========================================================
# Database configuration
# ==========================================================

TESTING = os.getenv("TESTING", "").lower() in (
    "1",
    "true",
    "yes",
) or "PYTEST_CURRENT_TEST" in os.environ


if TESTING:
    DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:",
    )
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não definido. "
            "Ex.: postgresql+psycopg2://usuario:senha@localhost:5432/registro_prod"
        )


# ==========================================================
# Engine
# ==========================================================

if DATABASE_URL.startswith("sqlite") and ":memory:" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
else:
    connect_args = (
        {"check_same_thread": False}
        if DATABASE_URL.startswith("sqlite")
        else {}
    )

    engine = create_engine(
        DATABASE_URL,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


# ==========================================================
# ORM base
# ==========================================================

Base = declarative_base()


# ==========================================================
# Session factory
# ==========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


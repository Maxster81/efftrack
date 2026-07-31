"""Infrastruttura database: engine, sessione, base ORM e dependency.

Regole SQLite (vedi clinerules/03-database.md):
- PRAGMA journal_mode=WAL ad ogni connessione.
- PRAGMA foreign_keys=ON ad ogni connessione.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


# L'argomento `check_same_thread` è necessario solo per SQLite.
# È False perché Uvicorn può usare più thread.
connect_args: dict = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection: object, connection_record: object) -> None:
    """Abilita WAL e foreign keys su ogni nuova connessione SQLite."""
    # L'import è qui per non forzare l'import di sqlite3 se il DB è Postgres.
    import sqlite3

    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    """Base dichiarativa per tutti i modelli ORM del progetto."""


def get_db() -> Generator[Session, None, None]:
    """Dependency FastAPI che fornisce una sessione DB e ne garantisce la chiusura."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

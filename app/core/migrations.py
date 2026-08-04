"""Migrazioni controllate dello schema.

Gestisce l'evoluzione dello schema SQLite senza introdurre Alembic. Ogni
migrazione è idempotente e viene applicata all'avvio.
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db import Base

logger: logging.Logger = logging.getLogger(__name__)


def _migrate_effort_entries(engine: Engine) -> None:
    """Ricrea `effort_entries` senza la colonna legacy `user_text`.

    La tabella viene DROPpata e ricreata se nel DB esiste ancora la colonna
    legacy. I dati esistenti vengono eliminati.
    """
    inspector = inspect(engine)
    if "effort_entries" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("effort_entries")}
    if "user_text" not in columns:
        logger.debug("Schema effort_entries già aggiornato, migrazione non necessaria")
        return

    logger.info("Migrazione: ricreazione effort_entries (dati esistenti eliminati)")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS effort_entries"))
    Base.metadata.create_all(bind=engine)
    logger.info("Tabella effort_entries ricreata con lo schema corrente")


def _migrate_users_last_login(engine: Engine) -> None:
    """Aggiunge la colonna `last_login` a `users`.

    Idempotente: se la colonna esiste già, non fa nulla. Usa ALTER TABLE
    (pattern già consolidato per le modifiche schema semplici in SQLite).
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "last_login" in columns:
        logger.debug("Colonna users.last_login già presente, migrazione non necessaria")
        return

    logger.info("Migrazione: aggiunta colonna users.last_login")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
    logger.info("Colonna users.last_login aggiunta")


def _migrate_users_group_id(engine: Engine) -> None:
    """Aggiunge la colonna `group_id` a `users`.

    Idempotente: se la colonna esiste già, non fa nulla. Usa ALTER TABLE
    con FK verso `groups.id` (nullable).
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "group_id" in columns:
        logger.debug("Colonna users.group_id già presente, migrazione non necessaria")
        return

    logger.info("Migrazione: aggiunta colonna users.group_id")
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES groups(id)")
        )
    logger.info("Colonna users.group_id aggiunta")


def _migrate_users_disabled_at(engine: Engine) -> None:
    """Aggiunge la colonna `disabled_at` a `users`.

    Idempotente: se la colonna esiste già, non fa nulla. Traccia la data di
    disabilitazione per calcolare la finestra minima prima dell'eliminazione.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "disabled_at" in columns:
        logger.debug("Colonna users.disabled_at già presente, migrazione non necessaria")
        return

    logger.info("Migrazione: aggiunta colonna users.disabled_at")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN disabled_at DATETIME"))
    logger.info("Colonna users.disabled_at aggiunta")


def _migrate_users_disabled(engine: Engine) -> None:
    """Aggiunge la colonna `disabled` a `users`.

    Idempotente: se la colonna esiste già, non fa nulla. Il default è 0 (False).
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "disabled" in columns:
        logger.debug("Colonna users.disabled già presente, migrazione non necessaria")
        return

    logger.info("Migrazione: aggiunta colonna users.disabled")
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN disabled BOOLEAN NOT NULL DEFAULT 0")
        )
    logger.info("Colonna users.disabled aggiunta")


def _migrate_users_profile(engine: Engine) -> None:
    """Migrazione profilo utente: aggiunge `first_name`, `last_name`, `email`
    e `password_change_required` a `users`.

    Idempotente: se le colonne esistono già, non fa nulla.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    new_columns = [
        ("first_name", "ALTER TABLE users ADD COLUMN first_name VARCHAR(64)"),
        ("last_name", "ALTER TABLE users ADD COLUMN last_name VARCHAR(64)"),
        ("email", "ALTER TABLE users ADD COLUMN email VARCHAR(128)"),
        (
            "password_change_required",
            "ALTER TABLE users ADD COLUMN password_change_required BOOLEAN NOT NULL DEFAULT 0",
        ),
    ]
    for col_name, sql in new_columns:
        if col_name in columns:
            logger.debug("Colonna users.%s già presente, migrazione non necessaria", col_name)
            continue
        logger.info("Migrazione profilo utente: aggiunta colonna users.%s", col_name)
        with engine.begin() as connection:
            connection.execute(text(sql))
        logger.info("Colonna users.%s aggiunta", col_name)


def run_schema_migrations(engine: Engine) -> None:
    """Applica le migrazioni controllate dello schema all'avvio.

    Gestisce: rimozione legacy in `effort_entries` e aggiunta delle colonne
    `last_login`, `group_id`, `disabled`, `disabled_at` e dei dati profilo
    a `users`. Idempotente: se lo schema è già allineato, non fa nulla.
    """
    _migrate_effort_entries(engine)
    _migrate_users_last_login(engine)
    _migrate_users_group_id(engine)
    _migrate_users_disabled_at(engine)
    _migrate_users_disabled(engine)
    _migrate_users_profile(engine)

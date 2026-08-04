"""Migrazioni controllate dello schema (Fase 11).

Gestisce l'evoluzione dello schema SQLite senza introdurre Alembic:
- Fase 11: ricrea `effort_entries` per aggiungere la ForeignKey su `users.id`
  e rimuovere la colonna `user_text`. Poiché l'utente ha deciso di eliminare
  i dati di sviluppo, la tabella viene semplicemente DROPpata e ricreata
  vuota con lo schema corrente (create_all idempotente).
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db import Base

logger: logging.Logger = logging.getLogger(__name__)


def _migrate_effort_entries(engine: Engine) -> None:
    """Migrazione Fase 11: ricrea `effort_entries` senza la colonna `user_text`.

    La tabella viene DROPpata e ricreata se nel DB esiste ancora la colonna
    legacy `user_text`. I dati di sviluppo vengono eliminati (decisione
    utente Fase 11).
    """
    inspector = inspect(engine)
    if "effort_entries" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("effort_entries")}
    if "user_text" not in columns:
        logger.debug("Schema effort_entries già aggiornato, migrazione non necessaria")
        return

    logger.info("Migrazione Fase 11: ricreazione effort_entries (dati di sviluppo eliminati)")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS effort_entries"))
    Base.metadata.create_all(bind=engine)
    logger.info("Tabella effort_entries ricreata con lo schema Fase 11")


def _migrate_users_last_login(engine: Engine) -> None:
    """Migrazione Fase 12b: aggiunge la colonna `last_login` a `users`.

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

    logger.info("Migrazione Fase 12b: aggiunta colonna users.last_login")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
    logger.info("Colonna users.last_login aggiunta")


def _migrate_users_group_id(engine: Engine) -> None:
    """Migrazione Fase 12c: aggiunge la colonna `group_id` a `users`.

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

    logger.info("Migrazione Fase 12c: aggiunta colonna users.group_id")
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES groups(id)")
        )
    logger.info("Colonna users.group_id aggiunta")


def _migrate_users_disabled_at(engine: Engine) -> None:
    """Migrazione Suggestion 8 (Fase 13d): aggiunge la colonna `disabled_at` a `users`.

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

    logger.info("Migrazione Suggestion 8: aggiunta colonna users.disabled_at")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN disabled_at DATETIME"))
    logger.info("Colonna users.disabled_at aggiunta")


def _migrate_users_disabled(engine: Engine) -> None:
    """Migrazione Fase 13a: aggiunge la colonna `disabled` a `users`.

    Idempotente: se la colonna esiste già, non fa nulla. Il default è 0 (False).
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "disabled" in columns:
        logger.debug("Colonna users.disabled già presente, migrazione non necessaria")
        return

    logger.info("Migrazione Fase 13a: aggiunta colonna users.disabled")
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN disabled BOOLEAN NOT NULL DEFAULT 0")
        )
    logger.info("Colonna users.disabled aggiunta")


def run_schema_migrations(engine: Engine) -> None:
    """Applica le migrazioni controllate dello schema all'avvio.

    - Fase 11: rimozione di `effort_entries.user_text` e aggiunta della FK.
    - Fase 12b: aggiunta della colonna `users.last_login`.
    - Fase 12c: aggiunta della colonna `users.group_id` (FK verso groups).
    - Fase 13a: aggiunta della colonna `users.disabled`.
    - Suggestion 8 (Fase 13d): aggiunta della colonna `users.disabled_at`.

    Idempotente: se lo schema è già allineato, non fa nulla.
    """
    _migrate_effort_entries(engine)
    _migrate_users_last_login(engine)
    _migrate_users_group_id(engine)
    _migrate_users_disabled_at(engine)
    _migrate_users_disabled(engine)

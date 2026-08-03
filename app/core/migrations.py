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


def run_schema_migrations(engine: Engine) -> None:
    """Applica le migrazioni controllate dello schema all'avvio.

    Per ora gestisce solo la rimozione di `effort_entries.user_text` e
    l'aggiunta della FK su `users.id`. Idempotente: se la tabella già
    rispetta lo schema corrente, non fa nulla.
    """
    inspector = inspect(engine)
    if "effort_entries" not in inspector.get_table_names():
        # La tabella non esiste ancora: verrà creata da create_all all'avvio.
        return

    columns = {col["name"] for col in inspector.get_columns("effort_entries")}
    if "user_text" not in columns:
        # Schema già aggiornato (nessuna colonna legacy da rimuovere).
        logger.debug("Schema effort_entries già aggiornato, migrazione non necessaria")
        return

    # Schema legacy (pre-Fase 11): elimina la tabella e i dati di sviluppo.
    logger.info("Migrazione Fase 11: ricreazione effort_entries (dati di sviluppo eliminati)")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS effort_entries"))

    # Ricrea la tabella con lo schema corrente (FK su users.id, senza user_text).
    Base.metadata.create_all(bind=engine)
    logger.info("Tabella effort_entries ricreata con lo schema Fase 11")
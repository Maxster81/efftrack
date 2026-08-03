"""Seed idempotente delle tabelle lookup e dell'utente admin.

Popola clients, groups, activities e l'utente admin solo se le rispettive
tabelle sono vuote. Eseguito a ogni startup (vedi `app/main.py` lifespan).

Fase 9: logging di quali lookup sono state populate all'avvio.
Fase 10: seed dell'utente admin (primo utente master) con password da config.
"""
from __future__ import annotations

import logging

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.models import Activity, Client, Group, User

logger: logging.Logger = logging.getLogger(__name__)

# --- Dati di default (derivati dal vecchio tool) -----------------------------

_CLIENTS: list[dict[str, str]] = [
    {"name": "INAIL"},
    {"name": "MDS"},
]

_GROUPS: list[dict[str, str]] = [
    {"name": "GRUPPO SOC"},
]

_ACTIVITIES: list[dict[str, object]] = [
    {
        "name": "SOC-Conduzione",
        "requires_description": False,
    },
    {
        "name": "SOC-Supporto Specialistico",
        "requires_description": True,
    },
]


def seed_lookup_tables(db: Session) -> None:
    """Inserisce i dati di default se le tabelle lookup sono vuote."""
    seeded_clients = _is_empty(db, Client)
    seeded_groups = _is_empty(db, Group)
    seeded_activities = _is_empty(db, Activity)

    if seeded_clients:
        db.add_all(Client(**data) for data in _CLIENTS)
    if seeded_groups:
        db.add_all(Group(**data) for data in _GROUPS)
    if seeded_activities:
        db.add_all(Activity(**data) for data in _ACTIVITIES)

    if seeded_clients or seeded_groups or seeded_activities:
        db.commit()
        logger.info(
            "Seed lookup completato (clients=%s, groups=%s, activities=%s)",
            seeded_clients,
            seeded_groups,
            seeded_activities,
        )
    else:
        logger.debug("Lookup già popolati, seed non necessario")


def seed_admin_user(db: Session) -> None:
    """Crea l'utente amministratore iniziale se la tabella users è vuota.

    Idempotente: se esiste già almeno un utente, non fa nulla. La password
    proviene da `ADMIN_PASSWORD` (env var, default "admin" in sviluppo).
    """
    if not _is_empty(db, User):
        logger.debug("Utenti già presenti, seed admin non necessario")
        return

    password_hash: str = bcrypt.hash(ADMIN_PASSWORD)
    db.add(
        User(
            username=ADMIN_USERNAME,
            password_hash=password_hash,
            role="admin",
        )
    )
    db.commit()
    logger.info("Utente admin creato: username=%s", ADMIN_USERNAME)


def _is_empty(db: Session, model: type) -> bool:
    """True se la tabella del modello non contiene righe."""
    return db.execute(select(model.id).limit(1)).first() is None
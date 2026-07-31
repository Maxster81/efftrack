"""Seed idempotente delle tabelle lookup.

Popola clients, groups e activities solo se la rispettiva tabella è
vuota. Eseguito a ogni startup (vedi `app/main.py` lifespan).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Activity, Client, Group

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
    if _is_empty(db, Client):
        db.add_all(Client(**data) for data in _CLIENTS)

    if _is_empty(db, Group):
        db.add_all(Group(**data) for data in _GROUPS)

    if _is_empty(db, Activity):
        db.add_all(Activity(**data) for data in _ACTIVITIES)

    db.commit()


def _is_empty(db: Session, model: type) -> bool:
    """True se la tabella del modello non contiene righe."""
    return db.execute(select(model.id).limit(1)).first() is None
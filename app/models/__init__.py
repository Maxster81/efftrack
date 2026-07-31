"""Modelli ORM del progetto.

Espone i modelli delle tabelle lookup (clients, groups, activities) e
della tabella centrale effort_entries. Il modulo `models` viene importato
in `app/main.py` (tramite `from app.db import Base`) affinché
`Base.metadata.create_all()` conosca tutte le tabelle.
"""
from __future__ import annotations

from app.db import Base
from app.models.activity import Activity
from app.models.client import Client
from app.models.effort_entry import EffortEntry
from app.models.group import Group

__all__ = [
    "Activity",
    "Base",
    "Client",
    "EffortEntry",
    "Group",
]
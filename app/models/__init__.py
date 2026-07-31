"""Modelli ORM del progetto.

In Fase 0 viene esposta solo la Base. I modelli veri e propri
(clients, groups, activities, effort_entries) verranno aggiunti
in Fase 4 insieme al database.
"""
from app.db import Base

__all__ = ["Base"]

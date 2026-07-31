"""Router API JSON dell'applicazione Effort Tracking.

Predisposizione per le future API REST (CRUD su effort_entries, export,
endpoint amministrativi). Al momento non espone alcuna route: viene
incluso in `app.main` per definire il prefisso `/api` e rendere
disponibile la struttura già dalle prime fasi.
"""
from __future__ import annotations

from fastapi import APIRouter


router: APIRouter = APIRouter(prefix="/api", tags=["api"])
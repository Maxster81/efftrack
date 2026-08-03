"""Router amministrativo (Fase 12a scheletro).

Router protetto da `require_admin`: espone le route di amministrazione
(gestione utenti, ruoli e lookup). In questa sottofase è solo lo scheletro
senza endpoint; la logica arriverà nella Fase 12b.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.permissions import require_admin
from app.models import User

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])
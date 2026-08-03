"""Dipendenze di autenticazione (Fase 10).

`get_current_user` è una dependency FastAPI che restituisce l'utente
autenticato dalla sessione HTTP, oppure None. Non chiude la sessione DB:
la chiude il normale lifecycle di FastAPI tramite `Depends(get_db)`.
"""
from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import AUTH_ENABLED
from app.db import get_db
from app.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Restituisce l'utente autenticato (o None) senza chiudere la sessione.

    Se `AUTH_ENABLED` è False restituisce sempre None (web server pubblico).
    Le route decidono se redirigere al login quando l'utente è assente.
    """
    if not AUTH_ENABLED:
        return None

    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)
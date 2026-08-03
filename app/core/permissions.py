"""Ruoli, permessi e dependency di autorizzazione (Fase 12a).

Fonte di verità unica per i controlli di autorizzazione.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

ROLE_ADMIN: str = "admin"
ROLE_MANAGER: str = "manager"
ROLE_USER: str = "user"


def is_admin(user: User | None) -> bool:
    """True se l'utente ha ruolo admin."""
    return user is not None and user.role == ROLE_ADMIN


def is_manager(user: User | None) -> bool:
    """True se l'utente ha ruolo manager."""
    return user is not None and user.role == ROLE_MANAGER


def is_staff(user: User | None) -> bool:
    """True se l'utente ha un ruolo di supervisione (admin o manager)."""
    return user is not None and user.role in (ROLE_ADMIN, ROLE_MANAGER)


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Dependency FastAPI: accesso solo agli utenti admin (401/403)."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Accesso non autorizzato")
    user = db.get(User, user_id)
    if user is None or user.role != ROLE_ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Richiesti privilegi di amministratore")
    return user


def require_manager(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Dependency FastAPI: accesso solo a manager o admin (401/403)."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Accesso non autorizzato")
    user = db.get(User, user_id)
    if user is None or user.role not in (ROLE_ADMIN, ROLE_MANAGER):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Richiesti privilegi di manager")
    return user
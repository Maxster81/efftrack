"""Modello ORM per la tabella degli utenti (Fase 10).

Predispone anche il campo `role` (admin/manager/user) che verrà
utilizzato dalle Fasi 12-13 per la gestione dei permessi.
Fase 12b: aggiunta colonna `last_login` per tracciare l'ultimo accesso.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.effort_entry import utcnow


class User(Base):
    """Utente del sistema con credenziali di accesso."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    # Fase 12b: traccia l'ultimo login dell'utente (popolato da auth.py).
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
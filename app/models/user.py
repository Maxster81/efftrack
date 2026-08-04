"""Modello ORM per la tabella degli utenti.

Dalla Fase 10 il modello traccia credenziali e ruolo.
Fase 12b: aggiunta colonna `last_login` per l'ultimo accesso.
Fase 12c: aggiunta colonna `group_id` (FK verso groups) per il ruolo MANAGER,
che gestisce un gruppo di lavoro e ne può consultare/esportare i record.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.effort_entry import utcnow


class User(Base):
    """Utente del sistema con credenziali di accesso e ruolo."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    # Fase 12b: traccia l'ultimo login dell'utente (popolato da auth.py).
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Fase 12c: gruppo di lavoro gestito dal ruolo MANAGER (nullable per USER/ADMIN).
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
    )
    # Fase 13a: utente disabilitato (bloccato al login ma record intatti).
    disabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Suggestion 8 (Fase 13d): momento della disabilitazione, per calcolare la
    # finestra temporale minima prima di poter eliminare definitivamente l'utente.
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relazione verso il gruppo (per leggere il nome nel template).
    group: Mapped["Group | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"

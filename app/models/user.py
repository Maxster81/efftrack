"""Modello ORM per la tabella degli utenti.

Traccia credenziali, ruolo, gruppo di appartenenza, dati anagrafici e
stato di disabilitazione/eliminazione.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.effort_entry import utcnow


class User(Base):
    """Utente del sistema con credenziali di accesso e ruolo."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # username: con la login SAML (SAML-D1) può essere l'email/UPN di Entra ID,
    # quindi serve più spazio rispetto a un semplice username (String(128)).
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # --- Campi per l'autenticazione SAML (feature MFA, branch MFA) ---
    # Identificatore univoco fornito dall'IdP (NameID, es. UPN dell'utente).
    saml_name_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    # Entity ID dell'IdP che ha fornito l'identità (per supportare più IdP in futuro).
    saml_entity_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    # Ultimo accesso dell'utente (popolato da auth.py).
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Gruppo di lavoro gestito dal ruolo MANAGER (nullable per USER/ADMIN).
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
    )
    # Utente disabilitato (bloccato al login ma record intatti).
    disabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Momento della disabilitazione, per calcolare la finestra temporale
    # minima prima di poter eliminare definitivamente l'utente.
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Profilo utente: dati anagrafici di base.
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Flag per forzare il cambio password al prossimo login (futuro).
    password_change_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    # Relazione verso il gruppo (per leggere il nome nel template).
    group: Mapped["Group | None"] = relationship()  # noqa: F821

    @property
    def full_name(self) -> str:
        """Nome e cognome concatenati (fallback sullo username se mancano)."""
        name = " ".join(p for p in (self.first_name, self.last_name) if p)
        return name if name else (self.username or "")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"

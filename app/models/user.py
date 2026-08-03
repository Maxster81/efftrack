"""Modello ORM per la tabella degli utenti (Fase 10).

Predispone anche il campo `role` (admin/manager/user) che verrà
utilizzato dalle Fasi 12-13 per la gestione dei permessi.
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """Utente del sistema con credenziali di accesso."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
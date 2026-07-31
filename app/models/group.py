"""Modello ORM per la tabella lookup dei gruppi."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Group(Base):
    """Gruppo di appartenenza dell'attività di effort."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Group {self.name}>"

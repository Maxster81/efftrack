"""Modello ORM per la tabella lookup delle attività."""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Activity(Base):
    """Attività di effort. `requires_description` indica se la
    descrizione attività è obbligatoria (es. Supporto Specialistico).
    """

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    requires_description: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Activity {self.name}>"

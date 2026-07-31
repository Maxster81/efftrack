"""Modello ORM per la tabella lookup dei clienti."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Client(Base):
    """Cliente a cui vengono addebitate le ore di effort."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Client {self.name}>"

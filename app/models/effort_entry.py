"""Modello ORM per le registrazioni di effort."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow_naive() -> datetime:
    """Datetime UTC corrente senza timezone info (per compatibilità SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


utcnow: Callable[[], datetime] = _utcnow_naive


class EffortEntry(Base):
    """Registrazione di ore lavorate per cliente/gruppo/attività.

    Il mese non viene persistito: è derivato da `work_date` via service
    helper (vedi memory-bank/systemPatterns.md).
    `user_id` è una colonna nullable senza ForeignKey: la tabella `users`
    arriverà in Fase 11 e solo allora verrà aggiunta la FK.
    """

    __tablename__ = "effort_entries"
    __table_args__ = (
        CheckConstraint(
            "hours_spent > 0 AND hours_spent <= 24",
            name="ck_effort_entries_hours_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Segregazione utente futura: colonna senza FK fino a Fase 11.
    user_id: Mapped[int | None] = mapped_column(nullable=True)

    # Testo libero del campo User del form (utile per i test pre-auth;
    # in Fase 10 verrà derivato dall'utente autenticato).
    user_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)

    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hours_spent: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    # Relazioni di lettura (utilizzate a partire da Fase 6 per l'elenco).
    client: Mapped["Client"] = relationship()  # noqa: F821
    group: Mapped["Group"] = relationship()  # noqa: F821
    activity: Mapped["Activity"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<EffortEntry {self.work_date} {self.hours_spent}h>"
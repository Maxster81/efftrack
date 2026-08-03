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
    Dalla Fase 11 `user_id` è una colonna con ForeignKey verso `users.id`:
    ogni record appartiene all'utente che lo ha creato.
    """

    __tablename__ = "effort_entries"
    __table_args__ = (
        CheckConstraint(
            "hours_spent > 0 AND hours_spent <= 24",
            name="ck_effort_entries_hours_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Segregazione utente (Fase 11): FK verso users.id.
    # ON DELETE SET NULL: se un utente viene cancellato, i suoi record
    # restano nel DB ma senza proprietario (visibili solo all'admin).
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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

    # Relazioni di lettura.
    client: Mapped["Client"] = relationship()  # noqa: F821
    group: Mapped["Group"] = relationship()  # noqa: F821
    activity: Mapped["Activity"] = relationship()  # noqa: F821
    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<EffortEntry {self.work_date} {self.hours_spent}h>"
"""Schema Pydantic per l'inserimento di un record di effort.

La validazione server-side obbligatoria vive qui (struttura, tipi, range).
La verifica condizionale della descrizione rispetto a `requires_description`
dipende dal DB e viene eseguita nella route (dove la sessione è disponibile).
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class EffortEntryCreate(BaseModel):
    """Input del form di inserimento/aggiornamento del tool.

    I nomi dei campi corrispondono ai `name` dei controlli del form HTML.
    `user` è un testo libero fino alla Fase 10 (quando arriverà l'auth).
    Le foreign key devono essere id numerici esistenti.
    """

    user: str = Field(min_length=1, max_length=64)
    date: date
    client_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    activity_id: int = Field(gt=0)
    hours: float = Field(ge=0.25, le=24)
    notes: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("user")
    @classmethod
    def user_not_blank(cls, value: str) -> str:
        """Il campo User non deve essere una stringa vuota o solo spazi."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Il campo User è obbligatorio.")
        return stripped

    @field_validator("hours")
    @classmethod
    def hours_step_quarter(cls, value: float) -> float:
        """Le ore devono essere multipli di 0.25 (tolleranza floating point)."""
        if abs(value * 4 - round(value * 4)) > 1e-6:
            raise ValueError("Le ore devono essere multipli di 0.25.")
        # Arrotonda per evitare errori floating point (es. 7.4999999 -> 7.5).
        return round(value, 2)

    @field_validator("notes", "description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        """Se il campo è una stringa vuota, la tratta come None."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
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
    # Fase 13b (Issue D): range 1-12, step 0.50 (assorbe Suggestion 2).
    # Nessun vincolo speciale per Supporto Specialistico (possono esserci straordinari > 4).
    hours: float = Field(ge=1, le=12)
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
    def hours_step_half(cls, value: float) -> float:
        """Le ore devono essere multiple di 0.50 (Fase 13b, tolleranza floating point).

        Il range (1-12) è già garantito dal Field; qui si verifica solo il passo.
        Elimina anche i valori non multipli di 0.50 (es. 7.25).
        """
        if abs(value * 2 - round(value * 2)) > 1e-6:
            raise ValueError("Le ore devono essere multiple di 0.50.")
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


class UserCreate(BaseModel):
    """Input per la creazione di un utente da parte dell'admin (Fase 12d)."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Il campo username è obbligatorio.")
        return stripped


class PasswordChange(BaseModel):
    """Input per il cambio password di un utente (Fase 12d)."""

    password: str = Field(min_length=1, max_length=128)


class RoleChange(BaseModel):
    """Input per il cambio ruolo di un utente (Fase 12d)."""

    role: str = Field(min_length=1, max_length=20)

    @field_validator("role")
    @classmethod
    def role_valid(cls, value: str) -> str:
        allowed = {"admin", "manager", "user"}
        if value not in allowed:
            raise ValueError("Ruolo non valido.")
        return value


class LookupCreate(BaseModel):
    """Input per la creazione/aggiornamento di una voce lookup (Fase 12d).

    `type` indica la tabella: client, group, activity.
    """

    type: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=128)

    @field_validator("type")
    @classmethod
    def type_valid(cls, value: str) -> str:
        allowed = {"client", "group", "activity"}
        if value not in allowed:
            raise ValueError("Tipo lookup non valido.")
        return value

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Il campo nome è obbligatorio.")
        return stripped

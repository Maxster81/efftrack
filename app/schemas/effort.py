"""Schema Pydantic per l'inserimento di un record di effort.

La validazione server-side obbligatoria vive qui (struttura, tipi, range).
La verifica condizionale della descrizione rispetto a `requires_description`
dipende dal DB e viene eseguita nella route (dove la sessione è disponibile).
"""
from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

# Caratteri di controllo da rimuovere dai campi testo: teniamo tab, LF e CR
# (utili in note/descrizione), eliminiamo il resto.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def _strip_control_chars(value: str) -> str:
    """Rimuove i caratteri di controllo non testuali da una stringa.

    Previene injection di sequenze di escape nei campi che poi vengono
    renderizzati nei template o persistiti.
    """
    return _CONTROL_CHARS_RE.sub("", value)


class EffortEntryCreate(BaseModel):
    """Input del form di inserimento/aggiornamento del tool.

    I nomi dei campi corrispondono ai `name` dei controlli del form HTML.
    `user` è il nome utente della sessione.

    Per i **giorni non lavorati** (S6), `is_holiday=True`: i campi
    `client_id`, `activity_id` e `hours` diventano opzionali, perché la
    route li forza ai lookup sentinella "NON LAVORATO" (cliente/attività)
    e a 8 ore. Il gruppo resta sempre quello reale dell'utente di sessione.
    """

    user: str = Field(min_length=1, max_length=64)
    date: date
    client_id: int | None = Field(default=None, gt=0)
    group_id: int | None = Field(default=None, gt=0)
    activity_id: int | None = Field(default=None, gt=0)
    # Range 1-12, step 0.50 (obbligatorio solo per i giorni lavorativi).
    # Nessun vincolo speciale per Supporto Specialistico (possono esserci straordinari > 4).
    hours: float | None = Field(default=None, ge=1, le=12)
    notes: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=2000)
    # Flag per i giorni non lavorati: la route forza i valori sentinella.
    is_holiday: bool = False

    @field_validator("user")
    @classmethod
    def user_not_blank(cls, value: str) -> str:
        """Il campo User non deve essere una stringa vuota o solo spazi."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Il campo User è obbligatorio.")
        return _strip_control_chars(stripped)

    @field_validator("hours")
    @classmethod
    def hours_step_half(cls, value: float | None) -> float | None:
        """Le ore devono essere multiple di 0.50 (tolleranza floating point).

        Il range (1-12) è già garantito dal Field; qui si verifica solo il passo.
        Elimina anche i valori non multipli di 0.50 (es. 7.25).
        Per i giorni non lavorati `hours` può essere None (la route forza 8).
        """
        if value is None:
            return None
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
        if not stripped:
            return None
        return _strip_control_chars(stripped)


class UserCreate(BaseModel):
    """Input per la creazione di un utente da parte dell'admin."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Il campo username è obbligatorio.")
        return _strip_control_chars(stripped)


class PasswordChange(BaseModel):
    """Input per il cambio password di un utente."""

    password: str = Field(min_length=1, max_length=128)


class RoleChange(BaseModel):
    """Input per il cambio ruolo di un utente."""

    role: str = Field(min_length=1, max_length=20)

    @field_validator("role")
    @classmethod
    def role_valid(cls, value: str) -> str:
        allowed = {"admin", "manager", "user"}
        if value not in allowed:
            raise ValueError("Ruolo non valido.")
        return value


class LookupCreate(BaseModel):
    """Input per la creazione/aggiornamento di una voce lookup.

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
        return _strip_control_chars(stripped)


class ProfileUpdate(BaseModel):
    """Input per l'aggiornamento del profilo utente (nome, cognome, email)."""

    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        """Normalizza i campi nome/cognome: rimuove spazi, None se vuoto."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        return _strip_control_chars(stripped)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalizza l'email: rimuove spazi, None se vuoto, formato valido."""
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        # Rimuove caratteri di controllo prima di verificare il formato.
        stripped = _strip_control_chars(stripped)
        # Verifica formato email di base (deve contenere @ e un punto dopo).
        if "@" not in stripped or "." not in stripped.split("@")[-1]:
            raise ValueError("Formato email non valido.")
        return stripped.lower()


class SelfPasswordChange(BaseModel):
    """Input per il cambio password da parte dell'utente stesso."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_not_blank(cls, value: str) -> str:
        """La nuova password non deve essere una stringa vuota o solo spazi."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("La nuova password è obbligatoria.")
        return stripped

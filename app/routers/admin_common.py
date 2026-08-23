"""Helper condivisi dei router amministrativi.

Non è un router: contiene solo funzioni di supporto riusate dai tre
sotto-router dell'area admin (`admin_dashboard`, `admin_users`,
`admin_lookup`), che condividono lo stesso prefisso `/admin`.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import (
    APP_NAME,
    APP_VERSION,
    AUTH_ENABLED,
    DATABASE_URL,
    USER_DELETE_GRACE_DAYS,
)
from app.models import Activity, Client, EffortEntry, Group, User
from app.models.effort_entry import utcnow


def sidebar_items() -> list[dict[str, str]]:
    """Voci della sidebar dell'area admin."""
    return [
        {"label": "Dashboard", "href": "/admin"},
        {"label": "Registrazioni", "href": "/admin/records"},
        {"label": "Gestione Utenti", "href": "/admin/users"},
        {"label": "Gestione Lookup", "href": "/admin/lookup"},
    ]


def base_context(request: Request, current_username: str, active: str = "") -> dict:
    """Contesto condiviso per i template dell'area admin."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "phase": "Pannello Admin",
        "current_username": current_username,
        "auth_enabled": AUTH_ENABLED,
        "is_admin": True,
        "sidebar_items": sidebar_items(),
        "active": active,
    }


def db_size_mb() -> str:
    """Dimensione del file SQLite in MB (fallback a '—' se non è un file)."""
    if not DATABASE_URL.startswith("sqlite:///"):
        return "—"
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)
    try:
        size = os.path.getsize(db_path)
        return f"{size / (1024 * 1024):.1f} MB"
    except OSError:
        return "—"


def month_bounds() -> tuple[date, date]:
    """Estremi (primo e ultimo giorno) del mese corrente."""
    today = date.today()
    start = today.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month - timedelta(days=1)


def inactive_users(db: Session, days: int = 7) -> list[tuple[str, int | None]]:
    """Utenti non disabilitati che non registrano effort da almeno `days` giorni.

    Restituisce coppie (username, giorni_dall_ultimo_record) ordinate per
    inattività decrescente. Gli utenti senza alcun record sono considerati
    inattivi con giorni = None.
    """
    cutoff = date.today() - timedelta(days=days)
    users = db.execute(select(User)).scalars().all()
    last_date_expr = (
        select(func.max(EffortEntry.work_date))
        .where(EffortEntry.user_id == User.id)
        .scalar_subquery()
    )
    rows = []
    for u in users:
        if u.disabled:
            continue
        last = db.execute(
            select(last_date_expr).where(User.id == u.id)
        ).scalar()
        if last is None:
            rows.append((u.username, None))
        elif last < cutoff:
            rows.append((u.username, (date.today() - last).days))
    rows.sort(
        key=lambda item: (item[1] is None, item[1] if item[1] is not None else 10**9),
        reverse=True,
    )
    return rows


def format_last_login(value: datetime | None) -> str:
    """Formatta il timestamp dell'ultimo login (— se assente)."""
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y %H:%M")


def user_stats(db: Session, user_id: int) -> int:
    """Numero di record di effort di un utente."""
    return db.execute(
        select(func.count()).select_from(EffortEntry).where(EffortEntry.user_id == user_id)
    ).scalar() or 0


def days_since(value: datetime | None) -> int | None:
    """Giorni trascorsi da un timestamp (None se assente)."""
    if value is None:
        return None
    return (utcnow() - value).days


def can_delete_user(u: User) -> bool:
    """True se l'utente è disabilitato da almeno `USER_DELETE_GRACE_DAYS` giorni."""
    if not u.disabled or u.disabled_at is None:
        return False
    return days_since(u.disabled_at) >= USER_DELETE_GRACE_DAYS


def delete_user_records(db: Session, user_id: int) -> int:
    """Elimina definitivamente i record di effort dell'utente.

    Restituisce il numero di record eliminati.
    """
    records = db.execute(
        select(EffortEntry).where(EffortEntry.user_id == user_id)
    ).scalars().all()
    count = len(records)
    for r in records:
        db.delete(r)
    return count


def lookup_model(lookup_type: str):
    """Restituisce il modello ORM del tipo di lookup indicato."""
    if lookup_type == "client":
        return Client
    if lookup_type == "group":
        return Group
    if lookup_type == "activity":
        return Activity
    raise ValueError(f"Tipo lookup non valido: {lookup_type}")


def lookup_label(lookup_type: str) -> str:
    """Etichetta italiana del tipo di lookup."""
    return {
        "client": "Clienti",
        "group": "Gruppi",
        "activity": "Attività",
    }.get(lookup_type, lookup_type)
"""Seed idempotente delle tabelle lookup, utente admin, utenti e record di test.

Popola clients, groups, activities, l'utente admin e (in sviluppo) utenti di
test con i relativi record di effort. Eseguito a ogni startup (vedi
`app/main.py` lifespan).

Fase 9: logging di quali lookup sono state populate all'avvio.
Fase 10: seed dell'utente admin (primo utente master) con password da config.
Fase 11: seed utenti + record di test per la segregazione dati.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from random import Random

from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.models import Activity, Client, EffortEntry, Group, User

logger: logging.Logger = logging.getLogger(__name__)

# --- Dati di default (derivati dal vecchio tool) -----------------------------

_CLIENTS: list[dict[str, str]] = [
    {"name": "INAIL"},
    {"name": "MDS"},
]

_GROUPS: list[dict[str, str]] = [
    {"name": "GRUPPO SOC"},
]

_ACTIVITIES: list[dict[str, object]] = [
    {
        "name": "SOC-Conduzione",
        "requires_description": False,
    },
    {
        "name": "SOC-Supporto Specialistico",
        "requires_description": True,
    },
]

# Utenti di test (Fase 11): usati solo per verificare la segregazione dati.
_TEST_USERS: list[dict[str, str]] = [
    {"username": "mario", "password": "test", "role": "user"},
    {"username": "giulia", "password": "test", "role": "user"},
    {"username": "luca", "password": "test", "role": "user"},
]

# Record di test per ciascun utente di test (Fase 11).
_TEST_RECORDS_PER_USER: int = 20


def seed_lookup_tables(db: Session) -> None:
    """Inserisce i dati di default se le tabelle lookup sono vuote."""
    seeded_clients = _is_empty(db, Client)
    seeded_groups = _is_empty(db, Group)
    seeded_activities = _is_empty(db, Activity)

    if seeded_clients:
        db.add_all(Client(**data) for data in _CLIENTS)
    if seeded_groups:
        db.add_all(Group(**data) for data in _GROUPS)
    if seeded_activities:
        db.add_all(Activity(**data) for data in _ACTIVITIES)

    if seeded_clients or seeded_groups or seeded_activities:
        db.commit()
        logger.info(
            "Seed lookup completato (clients=%s, groups=%s, activities=%s)",
            seeded_clients,
            seeded_groups,
            seeded_activities,
        )
    else:
        logger.debug("Lookup già popolati, seed non necessario")


def seed_admin_user(db: Session) -> None:
    """Crea l'utente amministratore iniziale se la tabella users è vuota.

    Idempotente: se esiste già almeno un utente, non fa nulla. La password
    proviene da `ADMIN_PASSWORD` (env var, default "admin" in sviluppo).
    """
    if not _is_empty(db, User):
        logger.debug("Utenti già presenti, seed admin non necessario")
        return

    password_hash: str = bcrypt.hash(ADMIN_PASSWORD)
    db.add(
        User(
            username=ADMIN_USERNAME,
            password_hash=password_hash,
            role="admin",
        )
    )
    db.commit()
    logger.info("Utente admin creato: username=%s", ADMIN_USERNAME)


def seed_test_users(db: Session) -> None:
    """Crea gli utenti di test (mario, giulia, luca) se non esistono (Fase 11).

    Idempotente per username: non duplica ni utente che esiste già.
    Password di default "test" (solo sviluppo).
    """
    existing = set(db.execute(select(User.username)).scalars().all())
    created: list[str] = []
    for data in _TEST_USERS:
        if data["username"] in existing:
            continue
        db.add(
            User(
                username=data["username"],
                password_hash=bcrypt.hash(data["password"]),
                role=data["role"],
            )
        )
        created.append(data["username"])
    if created:
        db.commit()
        logger.info("Utenti di test creati: %s", ", ".join(created))
    else:
        logger.debug("Utenti di test già presenti, seed non necessario")


def seed_test_records(db: Session) -> None:
    """Crea ~20 record di effort per ciascun utente di test (Fase 11).

    Idempotente: se esistono già record con `user_id` associati agli utenti
    di test, non fa nulla. I record sono spalmati sui giorni feriali del 2026.
    """
    test_users = db.execute(
        select(User).where(User.username.in_(["mario", "giulia", "luca"]))
    ).scalars().all()
    if not test_users:
        logger.debug("Nessun utente di test: seed record non necessario")
        return

    # Se qualche utente di test ha già record, considera il seed già fatto.
    already_seeded = db.execute(
        select(EffortEntry.id)
        .where(EffortEntry.user_id.in_([u.id for u in test_users]))
        .limit(1)
    ).first()
    if already_seeded is not None:
        logger.debug("Record di test già presenti, seed non necessario")
        return

    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()
    if not clients or not groups or not activities:
        logger.debug("Lookup mancanti: seed record di test non possibile")
        return

    rng = Random(42)  # seed fisso → dati riproducibili
    workdays = _workdays_in_year(2026)
    if len(workdays) < _TEST_RECORDS_PER_USER * len(test_users):
        raise ValueError("Numero di giorni lavorativi insufficiente per il seed di test")

    rows = rng.sample(workdays, k=_TEST_RECORDS_PER_USER * len(test_users))
    created_ids = 0
    for i, username in enumerate(["mario", "giulia", "luca"]):
        user = next(u for u in test_users if u.username == username)
        for j, work_date in enumerate(
            sorted(rows[i * _TEST_RECORDS_PER_USER : (i + 1) * _TEST_RECORDS_PER_USER])
        ):
            activity = rng.choice(activities)
            requires_description = activity.requires_description
            entry = EffortEntry(
                user_id=user.id,
                client_id=rng.choice(clients).id,
                group_id=groups[0].id,
                activity_id=activity.id,
                work_date=work_date,
                hours_spent=rng.choice([4.0, 5.0, 6.0, 7.0, 7.5, 8.0]),
                notes=f"Record di test {j+1} per {username}" if j % 3 == 0 else None,
                description=(
                    "Supporto specialistico di test" if requires_description else None
                ),
            )
            db.add(entry)
            created_ids += 1
    db.commit()
    logger.info("Record di test creati: %d", created_ids)


def _workdays_in_year(year: int) -> list[date]:
    """Restituisce i giorni feriali (lun–ven) dell'anno indicato."""
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    days: list[date] = []
    current = start
    while current < end:
        if current.weekday() < 5:  # lun=0 ... ven=4
            days.append(current)
        current += timedelta(days=1)
    return days


def _is_empty(db: Session, model: type) -> bool:
    """True se la tabella del modello non contiene righe."""
    return db.execute(select(model.id).limit(1)).first() is None
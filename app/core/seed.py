"""Seed idempotente delle tabelle lookup, utente admin, utenti e record di test.

Popola clients, groups, activities, l'utente admin e (in sviluppo) utenti di
test con i relativi record di effort. Eseguito a ogni startup (vedi
`app/main.py` lifespan).

Esegue il logging delle lookup popolate, crea l'utente admin (primo utente
master) con password da config e, in sviluppo, gli utenti di test con i loro
record di effort per la segregazione dei dati.
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
    {"name": "GRUPPO NOC"},
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

# Utenti di test per verificare segregazione dati e ruoli.
# La colonna `group` è il nome del gruppo di appartenenza (mappato a group_id
# da seed_test_users); `group_none=True` lascia il group_id a None (es. admin).
# Profilo utente: vengono colonne `first_name`, `last_name`, `email`.
_TEST_USERS: list[dict[str, str | None]] = [
    # 2 MANAGER: uno per SOC, uno per NOC.
    {"username": "giulia", "password": "test", "role": "manager", "group": "GRUPPO SOC",
     "first_name": "Giulia", "last_name": "Verdi", "email": "giulia@efftrack.local"},
    {"username": "marco", "password": "test", "role": "manager", "group": "GRUPPO NOC",
     "first_name": "Marco", "last_name": "Neri", "email": "marco@efftrack.local"},
    # 4 USER: 2 per SOC, 2 per NOC.
    {"username": "mario", "password": "test", "role": "user", "group": "GRUPPO SOC",
     "first_name": "Mario", "last_name": "Bianchi", "email": "mario@efftrack.local"},
    {"username": "paolo", "password": "test", "role": "user", "group": "GRUPPO SOC",
     "first_name": "Paolo", "last_name": "Gialli", "email": "paolo@efftrack.local"},
    {"username": "anna", "password": "test", "role": "user", "group": "GRUPPO NOC",
     "first_name": "Anna", "last_name": "Rossi", "email": "anna@efftrack.local"},
    {"username": "elisa", "password": "test", "role": "user", "group": "GRUPPO NOC",
     "first_name": "Elisa", "last_name": "Marroni", "email": "elisa@efftrack.local"},
]

# Record di test per ciascun utente di test.
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
            first_name="Admin",
            last_name="Master",
            email="admin@efftrack.local",
            # Al primo login l'admin deve cambiare la password di bootstrap.
            password_change_required=True,
        )
    )
    db.commit()
    logger.info("Utente admin creato: username=%s", ADMIN_USERNAME)


def _username_list() -> list[str]:
    """Lista di tutti gli username di test (per query e seed record)."""
    return [str(u["username"]) for u in _TEST_USERS]


def seed_test_users(db: Session) -> None:
    """Crea/aggiorna gli utenti di test (2 MANAGER + 4 USER su 2 gruppi).

    Idempotente per username. Ogni utente ha `role` e `group_id` derivati
    dalla configurazione `_TEST_USERS`, mappando il nome del gruppo al suo id.
    Gli utenti esistenti vengono aggiornati (upsert) per allineare ruolo/gruppo.
    Password di default "test" (solo sviluppo).
    """
    # Mappa nome gruppo → id (SOC e NOC).
    groups = {g.name: g.id for g in db.execute(select(Group)).scalars().all()}

    updated: list[str] = []
    for data in _TEST_USERS:
        username = data["username"]
        role = data["role"]
        group_name = data["group"]
        group_id = groups.get(group_name) if group_name else None

        user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")

        if user is None:
            db.add(
                User(
                    username=username,
                    password_hash=bcrypt.hash(data["password"]),
                    role=role,
                    group_id=group_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
            )
            updated.append(f"{username} (creato, {role})")
            continue

        # Upsert per allineare ruolo, gruppo e profilo.
        changed = False
        if user.role != role:
            user.role = role
            changed = True
        if user.group_id != group_id:
            user.group_id = group_id
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if user.email != email:
            user.email = email
            changed = True
        if changed:
            updated.append(f"{username} (aggiornato, {role})")

    if updated:
        db.commit()
        logger.info("Utenti di test aggiornati: %s", ", ".join(updated))
    else:
        logger.debug("Utenti di test già allineati, seed non necessario")


def seed_test_records(db: Session) -> None:
    """Crea ~20 record di effort per ciascun utente di test.

    Idempotente: se esistono già record con `user_id` associati agli utenti
    di test, non fa nulla. Ogni record usa il `group_id` del gruppo di
    appartenenza dell'utente (così la vista manager per gruppo ha senso).
    """
    usernames = _username_list()
    test_users = db.execute(
        select(User).where(User.username.in_(usernames))
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
    groups = {g.name: g.id for g in db.execute(select(Group)).scalars().all()}
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
    for i, data in enumerate(_TEST_USERS):
        username = data["username"]
        group_name = data["group"]
        user = next(u for u in test_users if u.username == username)
        group_id = groups.get(group_name) if group_name else None

        for j, work_date in enumerate(
            sorted(rows[i * _TEST_RECORDS_PER_USER : (i + 1) * _TEST_RECORDS_PER_USER])
        ):
            activity = rng.choice(activities)
            requires_description = activity.requires_description
            entry = EffortEntry(
                user_id=user.id,
                client_id=rng.choice(clients).id,
                group_id=group_id,
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
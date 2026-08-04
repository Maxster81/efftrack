"""Fixture pytest condivise per i test funzionali (Issue H).

Configura un database SQLite su file dedicato ai test, PRIMA di importare
i moduli applicativi, così `app.config` legge `EFFORT_TRACKING_DB_URL` con
il path di test e non tocca mai il DB di sviluppo `data/efftrack.db`.

Ogni fixture `client` è function-scope: il TestClient riesegue il lifespan
(migrazioni + seed idempotenti) e, al termine, le tabelle transazionali
(record e utenti non-admin) vengono ripulite, riportando il DB allo stato
del solo seed admin. Questo garantisce isolamento tra i test.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Il DB di test va configurato PRIMA di importare qualsiasi modulo app.*.
# Si usa un file su disco (non :memory:) perché TestClient esegue il server
# in un thread separato e le connessioni in-memory non sarebbero condivise.
TEST_DIR = Path(tempfile.mkdtemp(prefix="efftrack_test_"))
os.environ["EFFORT_TRACKING_DB_URL"] = f"sqlite:///{TEST_DIR / 'test.db'}"

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app as fastapi_app
from app.models import EffortEntry, User


@pytest.fixture()
def client():
    """TestClient FastAPI con DB di test seedato e sessione isolata.

    Il context manager esegue il lifespan (migrazioni + seed di lookup,
    admin, utenti di test e 20 record ciascuno). Al teardown ripulisce le
    tabelle transazionali così il test successivo riparte da uno stato
    identico (il nuovo TestClient ri-semina nel lifespan).
    """
    with TestClient(fastapi_app) as c:
        yield c
    with SessionLocal() as db:
        db.execute(EffortEntry.__table__.delete())
        db.execute(User.__table__.delete().where(User.username != "admin"))
        db.commit()


@pytest.fixture()
def db_session():
    """Sessione SQLAlchemy diretta sul DB di test per setup/assert."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
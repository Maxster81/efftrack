"""Test di base per il modello dati e il seed della Fase 4.

Usa unittest (stdlib) e un SQLite in-memory dedicato, separato dal
database di sviluppo `data/efftrack.db`.
"""
from __future__ import annotations

import unittest

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.core.seed import seed_lookup_tables
from app.db import Base
from app.models import Activity, Client, EffortEntry, Group


class DatabaseTestCase(unittest.TestCase):
    """Fixture condivisa: engine SQLite in-memory + schema + seed."""

    @classmethod
    def setUpClass(cls) -> None:
        # Engine in-memory dedicato ai test (isolato dal DB di sviluppo).
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            future=True,
        )
        cls.engine.connect().exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(bind=cls.engine)
        with Session(cls.engine) as db:
            seed_lookup_tables(db)

    def setUp(self) -> None:
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()


class TestSchema(DatabaseTestCase):
    def test_expected_tables_exist(self) -> None:
        """Le 4 tabelle attese sono presenti nello schema."""
        table_names = set(inspect(self.engine).get_table_names())
        for table in {"clients", "groups", "activities", "effort_entries"}:
            self.assertIn(table, table_names)


class TestSeed(DatabaseTestCase):
    def test_clients_seed(self) -> None:
        clients = self.db.execute(select(Client).order_by(Client.name)).scalars().all()
        self.assertEqual([c.name for c in clients], ["INAIL", "MDS"])

    def test_groups_seed(self) -> None:
        groups = self.db.execute(select(Group).order_by(Group.name)).scalars().all()
        self.assertEqual([g.name for g in groups], ["GRUPPO SOC"])

    def test_activities_seed(self) -> None:
        activities = self.db.execute(select(Activity).order_by(Activity.name)).scalars().all()
        self.assertEqual(len(activities), 2)
        by_name = {a.name: a for a in activities}
        self.assertFalse(by_name["SOC-Conduzione"].requires_description)
        self.assertTrue(by_name["SOC-Supporto Specialistico"].requires_description)

    def test_seed_is_idempotent(self) -> None:
        """Un secondo seed non deve duplicare le righe."""
        seed_lookup_tables(self.db)
        n_clients = len(self.db.execute(select(Client)).scalars().all())
        self.assertEqual(n_clients, 2)


class TestEffortEntry(DatabaseTestCase):
    def test_insert_entry(self) -> None:
        client = self.db.execute(select(Client)).scalars().first()
        group = self.db.execute(select(Group)).scalars().first()
        activity = self.db.execute(select(Activity)).scalars().first()

        from datetime import date

        entry = EffortEntry(
            user_id=None,
            client_id=client.id,
            group_id=group.id,
            activity_id=activity.id,
            work_date=date(2026, 7, 31),
            hours_spent=7.5,
            notes=None,
            description=None,
        )
        self.db.add(entry)
        self.db.commit()

        saved = self.db.execute(select(EffortEntry)).scalars().first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.hours_spent, 7.5)
        self.assertEqual(saved.client.name, client.name)


if __name__ == "__main__":
    unittest.main()
"""Test di base per il modello dati e il seed della Fase 4.

Usa unittest (stdlib) e un SQLite in-memory dedicato, separato dal
database di sviluppo `data/efftrack.db`.
"""
from __future__ import annotations

import unittest
from datetime import date

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.core.seed import (
    seed_admin_user,
    seed_lookup_tables,
    seed_test_records,
    seed_test_users,
)
from app.db import Base
from app.models import Activity, Client, EffortEntry, Group, User


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
            seed_admin_user(db)

    def setUp(self) -> None:
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()


class TestSchema(DatabaseTestCase):
    def test_expected_tables_exist(self) -> None:
        """Le 5 tabelle attese sono presenti nello schema."""
        table_names = set(inspect(self.engine).get_table_names())
        for table in {"clients", "groups", "activities", "effort_entries", "users"}:
            self.assertIn(table, table_names)

    def test_users_has_last_login_column(self) -> None:
        """Fase 12b: la tabella users ha la colonna last_login."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("last_login", columns)

    def test_users_has_group_id_column(self) -> None:
        """Fase 12c: la tabella users ha la colonna group_id (FK verso groups)."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("group_id", columns)
        fks = inspect(self.engine).get_foreign_keys("users")
        group_fks = [fk for fk in fks if "group_id" in fk["constrained_columns"]]
        self.assertEqual(len(group_fks), 1)
        self.assertEqual(group_fks[0]["referred_table"], "groups")

    def test_effort_entries_has_no_user_text(self) -> None:
        """Fase 11: la colonna legacy user_text è stata rimossa."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("effort_entries")}
        self.assertNotIn("user_text", columns)

    def test_effort_entries_has_user_foreign_key(self) -> None:
        """Fase 11: user_id è una FK verso users.id."""
        fks = inspect(self.engine).get_foreign_keys("effort_entries")
        user_fks = [fk for fk in fks if "user_id" in fk["constrained_columns"]]
        self.assertEqual(len(user_fks), 1)
        self.assertEqual(user_fks[0]["referred_table"], "users")


class TestSeed(DatabaseTestCase):
    def test_clients_seed(self) -> None:
        clients = self.db.execute(select(Client).order_by(Client.name)).scalars().all()
        self.assertEqual([c.name for c in clients], ["INAIL", "MDS"])

    def test_groups_seed(self) -> None:
        groups = self.db.execute(select(Group).order_by(Group.name)).scalars().all()
        self.assertEqual([g.name for g in groups], ["GRUPPO NOC", "GRUPPO SOC"])

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


class TestAdminUser(DatabaseTestCase):
    """Test di creazione dell'utente admin (Fase 10)."""

    def test_admin_seed_creates_user(self) -> None:
        """Crea l'utente admin con password hashata e ruolo admin."""
        seed_admin_user(self.db)
        user = self.db.execute(select(User)).scalars().first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "admin")
        self.assertEqual(user.role, "admin")

    def test_admin_password_hash_is_valid(self) -> None:
        """L'hash della password admin verifica con la password di default."""
        from passlib.hash import bcrypt

        seed_admin_user(self.db)
        user = self.db.execute(select(User)).scalars().first()
        self.assertTrue(bcrypt.verify("admin", user.password_hash))

    def test_admin_seed_is_idempotent(self) -> None:
        """Un secondo seed non deve duplicare l'utente admin."""
        seed_admin_user(self.db)
        seed_admin_user(self.db)
        count = len(self.db.execute(select(User)).scalars().all())
        self.assertEqual(count, 1)


class TestExportCsv(DatabaseTestCase):
    """Test della generazione del CSV di export (Fase 8/11)."""

    def _create_entry(self, db: Session, user: User | None = None) -> EffortEntry:
        """Crea un record di effort, opzionalmente associato a un utente."""
        client = db.execute(select(Client)).scalars().first()
        group = db.execute(select(Group)).scalars().first()
        activity = db.execute(select(Activity)).scalars().first()

        entry = EffortEntry(
            user_id=user.id if user is not None else None,
            client_id=client.id,
            group_id=group.id,
            activity_id=activity.id,
            work_date=date(2026, 7, 31),
            hours_spent=7.5,
            notes="Nota di test",
            description=None,
        )
        # Assegna le relazioni direttamente sull'oggetto: `_build_csv`
        # accede a `client.name`, `group.name`, `activity.name` e `user.username`.
        entry.client = client
        entry.group = group
        entry.activity = activity
        entry.user = user
        db.add(entry)
        db.commit()
        return entry

    def test_build_csv_header_and_row_with_user(self) -> None:
        """Il CSV contiene il BOM, l'header e una riga con lo username reale."""
        from app.routers.web import _build_csv

        user = User(username="mario", password_hash="x", role="user")
        self.db.add(user)
        self.db.commit()
        entry = self._create_entry(self.db, user=user)

        csv_lines = _build_csv([entry]).splitlines()
        # La prima riga inizia con il BOM UTF-8.
        self.assertTrue(csv_lines[0].startswith("\ufeffData"))
        self.assertEqual(len(csv_lines), 2)
        row = csv_lines[1]
        self.assertIn("31/07/2026", row)
        self.assertIn("mario", row)  # username dal JOIN su users (Fase 11)
        self.assertIn("INAIL", row)
        self.assertIn("GRUPPO SOC", row)
        self.assertIn("7.5", row)
        self.assertIn("Nota di test", row)

    def test_build_csv_orphan_record_shows_empty_user(self) -> None:
        """Un record senza proprietario mostra colonna Utente vuota."""
        from app.routers.web import _build_csv

        entry = self._create_entry(self.db, user=None)
        csv_lines = _build_csv([entry]).splitlines()
        row = csv_lines[1]
        # La colonna Utente (quinta, indice 4) è vuota.
        fields = row.split(",")
        self.assertEqual(fields[4], "")


class TestEffortEntry(DatabaseTestCase):
    def test_insert_entry(self) -> None:
        """Fase 11: l'inserimento valorizza user_id (FK verso users)."""
        client = self.db.execute(select(Client)).scalars().first()
        group = self.db.execute(select(Group)).scalars().first()
        activity = self.db.execute(select(Activity)).scalars().first()
        user = self.db.execute(select(User)).scalars().first()
        self.assertIsNotNone(user)

        entry = EffortEntry(
            user_id=user.id,
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
        self.assertEqual(saved.user_id, user.id)
        self.entry_id = saved.id
        self.entry_user_id = user.id

    def test_update_entry(self) -> None:
        """Aggiorna un record esistente senza cambiare il proprietario (Fase 7/11)."""
        # Prepara un record da aggiornare.
        self.test_insert_entry()
        entry = self.db.get(EffortEntry, self.entry_id)
        self.assertIsNotNone(entry)

        second_client = self.db.execute(select(Client).order_by(Client.id.desc())).scalars().first()
        entry.client_id = second_client.id
        entry.work_date = date(2026, 8, 1)
        entry.hours_spent = 8.0
        entry.notes = "Note aggiornate"
        entry.description = "Descrizione aggiornata"
        self.db.commit()

        updated = self.db.get(EffortEntry, self.entry_id)
        self.assertEqual(updated.client_id, second_client.id)
        self.assertEqual(updated.work_date.isoformat(), "2026-08-01")
        self.assertEqual(updated.hours_spent, 8.0)
        self.assertEqual(updated.notes, "Note aggiornate")
        self.assertEqual(updated.description, "Descrizione aggiornata")
        self.assertIsNotNone(updated.updated_at)
        # Il proprietario resta invariato su update (Fase 11).
        self.assertEqual(updated.user_id, self.entry_user_id)


class TestTestUsers(DatabaseTestCase):
    """Test degli utenti di test (Fasi 11/12c)."""

    def test_seed_creates_six_users(self) -> None:
        """Crea 2 manager (giulia, marco) e 4 user (mario, paolo, anna, elisa)."""
        seed_test_users(self.db)
        usernames = set(self.db.execute(select(User.username)).scalars().all())
        for name in ["giulia", "marco", "mario", "paolo", "anna", "elisa"]:
            self.assertIn(name, usernames)

    def test_seed_promotes_giulia_to_manager(self) -> None:
        """Fase 12c: giulia è manager del GRUPPO SOC."""
        seed_test_users(self.db)
        giulia = self.db.execute(
            select(User).where(User.username == "giulia")
        ).scalar_one_or_none()
        self.assertIsNotNone(giulia)
        self.assertEqual(giulia.role, "manager")
        self.assertIsNotNone(giulia.group_id)

    def test_seed_users_is_idempotent(self) -> None:
        """Un secondo seed non duplica gli utenti di test."""
        seed_test_users(self.db)
        seed_test_users(self.db)
        count = len(self.db.execute(select(User)).scalars().all())
        self.assertEqual(count, 7)  # admin + 6 di test


class TestTestRecords(DatabaseTestCase):
    """Test dei record di test per la segregazione (Fasi 11/12c)."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with Session(cls.engine) as db:
            seed_test_users(db)
            seed_test_records(db)
        cls.records_per_user = _count_records_per_user(cls.engine)

    def test_records_assigned_to_test_users(self) -> None:
        """Ogni utente di test ha 20 record assegnati."""
        for username, count in self.records_per_user.items():
            self.assertEqual(
                count, 20, f"{username} dovrebbe avere 20 record, ne ha {count}"
            )

    def test_records_seed_is_idempotent(self) -> None:
        """Un secondo seed di record non deve duplicare."""
        with Session(self.engine) as db:
            seed_test_records(db)
        total = _count_total_records(self.engine)
        self.assertEqual(total, 120)  # 6 utenti × 20


def _count_records_per_user(engine) -> dict[str, int]:
    """Conteggia i record di effort per ciascun utente di test."""
    usernames = ["giulia", "marco", "mario", "paolo", "anna", "elisa"]
    with Session(engine) as db:
        users = db.execute(
            select(User).where(User.username.in_(usernames))
        ).scalars().all()
        result: dict[str, int] = {}
        for u in users:
            n = db.execute(
                select(EffortEntry).where(EffortEntry.user_id == u.id)
            ).scalars().all()
            result[u.username] = len(n)
        return result


def _count_total_records(engine) -> int:
    """Conteggia tutti i record di effort."""
    with Session(engine) as db:
        return len(db.execute(select(EffortEntry)).scalars().all())


class TestSidebar(DatabaseTestCase):
    """Test delle voci della sidebar in base al ruolo (Fasi 12b/12c)."""

    def test_user_sidebar_has_registrazioni_link(self) -> None:
        from app.routers.web import _sidebar_items

        user = User(username="mario", password_hash="x", role="user")
        items = _sidebar_items(user)
        self.assertEqual(items, [{"label": "Registrazioni", "href": "/"}])

    def test_manager_sidebar_has_registrazioni_and_group(self) -> None:
        """Fase 12c: il manager ha i link Registrazioni e Gruppo."""
        from app.routers.web import _sidebar_items

        group = self.db.execute(select(Group)).scalars().first()
        user = User(username="giulia", password_hash="x", role="manager", group_id=group.id)
        items = _sidebar_items(user)
        self.assertEqual(
            items,
            [
                {"label": "Registrazioni", "href": "/"},
                {"label": "Gruppo", "href": "/group"},
            ],
        )

    def test_manager_view_requires_group(self) -> None:
        """Fase 12c: un manager senza group_id non è abilitato alla vista gruppo."""
        from app.routers.web import _is_manager_view

        manager_no_group = User(username="giulia", password_hash="x", role="manager", group_id=None)
        self.assertFalse(_is_manager_view(manager_no_group))

        group = self.db.execute(select(Group)).scalars().first()
        manager = User(username="giulia", password_hash="x", role="manager", group_id=group.id)
        self.assertTrue(_is_manager_view(manager))


class TestAdminSidebar(DatabaseTestCase):
    """Test della sidebar del ruolo ADMIN (Fase 12d)."""

    def test_admin_sidebar_has_four_items(self) -> None:
        from app.routers.web import _sidebar_items

        admin = User(username="admin", password_hash="x", role="admin")
        items = _sidebar_items(admin)
        labels = [i["label"] for i in items]
        self.assertEqual(
            labels,
            ["Dashboard", "Registrazioni", "Gestione Utenti", "Gestione Lookup"],
        )

    def test_lookup_model_mapping(self) -> None:
        """Fase 12d: il mapping dei tipi di lookup restituisce i modelli giusti."""
        from app.routers.admin import _lookup_model

        self.assertIs(_lookup_model("client"), Client)
        self.assertIs(_lookup_model("group"), Group)
        self.assertIs(_lookup_model("activity"), Activity)

    def test_invalid_lookup_type_raises(self) -> None:
        from app.routers.admin import _lookup_model

        with self.assertRaises(ValueError):
            _lookup_model("bogus")


class TestManagerGroup(DatabaseTestCase):
    """Test del ruolo MANAGER e della vista gruppo (Fase 12c)."""

    def setUp(self) -> None:
        """Pulisce gli effort e gli utenti non-admin prima di ogni test."""
        super().setUp()
        self.db.execute(EffortEntry.__table__.delete())
        self.db.execute(User.__table__.delete().where(User.username != "admin"))
        self.db.commit()
        self.group = self.db.execute(select(Group)).scalars().first()
        self.client = self.db.execute(select(Client)).scalars().first()
        self.activity = self.db.execute(select(Activity)).scalars().first()

    def _create_users(self) -> tuple[User, User, User]:
        """Crea manager + 2 utenti del gruppo + 1 utente fuori gruppo.

        Usa username unici per evitare collisioni con la fixture condivisa
        (il setUp pulisce gli utenti non-admin prima di ogni test).
        """
        manager = User(username="mgmt1", password_hash="x", role="manager", group_id=self.group.id)
        member = User(username="mem1", password_hash="x", role="user", group_id=self.group.id)
        member2 = User(username="mem2", password_hash="x", role="user", group_id=self.group.id)
        outsider = User(username="ext1", password_hash="x", role="user", group_id=None)
        self.db.add_all([manager, member, member2, outsider])
        self.db.commit()
        return manager, member, member2, outsider

    def _add_entry(self, user: User) -> None:
        """Crea un record di effort per l'utente indicato."""
        self.db.add(
            EffortEntry(
                user_id=user.id,
                client_id=self.client.id,
                group_id=self.group.id,
                activity_id=self.activity.id,
                work_date=date(2026, 6, 10),
                hours_spent=8.0,
            )
        )
        self.db.commit()

    def test_seed_promotes_giulia_to_manager(self) -> None:
        """Fase 12c: giulia (creata/promossa) è manager del GRUPPO SOC."""
        seed_test_users(self.db)
        giulia = self.db.execute(
            select(User).where(User.username == "giulia")
        ).scalar_one_or_none()
        self.assertIsNotNone(giulia)
        self.assertEqual(giulia.role, "manager")
        self.assertIsNotNone(giulia.group_id)

    def test_records_in_group_shows_only_group_members(self) -> None:
        """La vista gruppo mostra solo i record dei membri del gruppo."""
        from app.routers.web import _records_in_group

        manager, member, member2, outsider = self._create_users()
        self._add_entry(member)
        self._add_entry(member2)
        self._add_entry(outsider)

        records = _records_in_group(self.db, self.group.id, month=None)
        user_ids = {r.user_id for r in records}
        self.assertIn(member.id, user_ids)
        self.assertIn(member2.id, user_ids)
        self.assertNotIn(outsider.id, user_ids)

    def test_month_options_in_group(self) -> None:
        """Le opzioni mese della vista gruppo derivano dai record del gruppo."""
        from app.routers.web import _month_options_in_group

        manager, member, member2, outsider = self._create_users()
        self._add_entry(member)  # 2026-06
        months = _month_options_in_group(self.db, self.group.id)
        self.assertIn("2026-06", [m for m, _ in months])

    def test_manager_sees_own_records_on_personal_page(self) -> None:
        """Il manager sulla propria pagina vede solo i propri record (come USER)."""
        from app.routers.web import _filter_by_user

        manager, member, member2, outsider = self._create_users()
        self._add_entry(manager)
        self._add_entry(member)

        stmt = select(EffortEntry)
        filtered = _filter_by_user(stmt, manager)
        records = self.db.execute(filtered).scalars().all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].user_id, manager.id)


class TestSegregation(DatabaseTestCase):
    """Test della segregazione dati tra utenti (Fase 11)."""

    def setUp(self) -> None:
        """Pulisce gli effort e gli utenti non-admin prima di ogni test."""
        super().setUp()
        self.db.execute(EffortEntry.__table__.delete())
        self.db.execute(User.__table__.delete().where(User.username != "admin"))
        self.db.commit()

    def _create_users_and_entries(self) -> tuple[User, User, User]:
        """Crea due utenti normali + riusa l'admin della fixture, con record."""
        mario = User(username="mario", password_hash="x", role="user")
        giulia = User(username="giulia", password_hash="x", role="user")
        self.db.add_all([mario, giulia])
        self.db.commit()
        admin = self.db.execute(
            select(User).where(User.username == "admin")
        ).scalars().first()
        self.assertIsNotNone(admin)

        client = self.db.execute(select(Client)).scalars().first()
        group = self.db.execute(select(Group)).scalars().first()
        activity = self.db.execute(select(Activity)).scalars().first()

        self.db.add_all([
            EffortEntry(
                user_id=mario.id,
                client_id=client.id,
                group_id=group.id,
                activity_id=activity.id,
                work_date=date(2026, 1, 15),
                hours_spent=8,
            ),
            EffortEntry(
                user_id=giulia.id,
                client_id=client.id,
                group_id=group.id,
                activity_id=activity.id,
                work_date=date(2026, 2, 20),
                hours_spent=6,
            ),
        ])
        self.db.commit()
        return mario, giulia, admin

    def test_user_sees_only_own_records(self) -> None:
        """Un utente normale vede solo i propri record."""
        from app.routers.web import _filter_by_user

        mario, giulia, admin = self._create_users_and_entries()

        stmt = select(EffortEntry)
        filtered = _filter_by_user(stmt, mario)
        records = self.db.execute(filtered).scalars().all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].user_id, mario.id)

    def test_admin_sees_all_records(self) -> None:
        """L'admin vede tutti i record (nessun filtro)."""
        from app.routers.web import _filter_by_user

        mario, giulia, admin = self._create_users_and_entries()

        stmt = select(EffortEntry)
        filtered = _filter_by_user(stmt, admin)
        records = self.db.execute(filtered).scalars().all()
        self.assertEqual(len(records), 2)

    def test_admin_cannot_update_or_delete_others(self) -> None:
        """Regola aziendale: nemmeno l'admin modifica/elimina record altrui."""
        from app.routers.web import _delete_entry, _save_single
        from app.schemas.effort import EffortEntryCreate

        mario, giulia, admin = self._create_users_and_entries()
        giulia_entry = self.db.execute(
            select(EffortEntry).where(EffortEntry.user_id == giulia.id)
        ).scalars().first()
        self.assertIsNotNone(giulia_entry)

        payload = EffortEntryCreate(
            user="admin",
            date=date(2026, 8, 1),
            client_id=giulia_entry.client_id,
            group_id=giulia_entry.group_id,
            activity_id=giulia_entry.activity_id,
            hours=7.0,
            notes="tentativo admin",
            description=None,
        )

        # L'admin NON può aggiornare il record di giulia: redirect a errore.
        resp_update = _save_single(payload, self.db, admin, record_id=giulia_entry.id)
        self.assertIn("error=validazione", resp_update.headers["location"])

        # Il record di giulia è intatto.
        refreshed = self.db.get(EffortEntry, giulia_entry.id)
        self.assertEqual(refreshed.hours_spent, giulia_entry.hours_spent)

        # L'admin NON può eliminare il record di giulia: redirect a errore.
        resp_delete = _delete_entry(giulia_entry.id, self.db, admin)
        self.assertIn("error=validazione", resp_delete.headers["location"])

        # Il record di giulia esiste ancora.
        self.assertIsNotNone(self.db.get(EffortEntry, giulia_entry.id))

    def test_orphan_records_invisible_to_normal_user(self) -> None:
        """Un record orfano (user_id NULL) non è visibile agli utenti normali."""
        from app.routers.web import _filter_by_user

        mario, giulia, admin = self._create_users_and_entries()
        client = self.db.execute(select(Client)).scalars().first()
        group = self.db.execute(select(Group)).scalars().first()
        activity = self.db.execute(select(Activity)).scalars().first()
        self.db.add(
            EffortEntry(
                user_id=None,
                client_id=client.id,
                group_id=group.id,
                activity_id=activity.id,
                work_date=date(2026, 3, 10),
                hours_spent=7,
            )
        )
        self.db.commit()

        stmt = select(EffortEntry)
        records_mario = self.db.execute(_filter_by_user(stmt, mario)).scalars().all()
        self.assertEqual(len(records_mario), 1)  # solo il suo

        stmt_admin = select(EffortEntry)
        records_admin = self.db.execute(_filter_by_user(stmt_admin, admin)).scalars().all()
        self.assertEqual(len(records_admin), 3)  # 2 + 1 orfano


if __name__ == "__main__":
    unittest.main()

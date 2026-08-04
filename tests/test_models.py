"""Test di base per il modello dati e il seed.

Usa unittest (stdlib) e un SQLite in-memory dedicato, separato dal
database di sviluppo `data/efftrack.db`.
"""
from __future__ import annotations

import unittest
from datetime import date

from pydantic import ValidationError
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
from app.schemas.effort import (
    EffortEntryCreate,
    ProfileUpdate,
    SelfPasswordChange,
)


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
        """La tabella users ha la colonna last_login."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("last_login", columns)

    def test_users_has_group_id_column(self) -> None:
        """La tabella users ha la colonna group_id (FK verso groups)."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("group_id", columns)
        fks = inspect(self.engine).get_foreign_keys("users")
        group_fks = [fk for fk in fks if "group_id" in fk["constrained_columns"]]
        self.assertEqual(len(group_fks), 1)
        self.assertEqual(group_fks[0]["referred_table"], "groups")

    def test_users_has_disabled_column(self) -> None:
        """La tabella users ha la colonna disabled."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("disabled", columns)

    def test_users_has_disabled_at_column(self) -> None:
        """La tabella users ha la colonna disabled_at."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("disabled_at", columns)

    def test_effort_entries_has_no_user_text(self) -> None:
        """La colonna legacy user_text è stata rimossa."""
        columns = {col["name"] for col in inspect(self.engine).get_columns("effort_entries")}
        self.assertNotIn("user_text", columns)

    def test_effort_entries_has_user_foreign_key(self) -> None:
        """user_id è una FK verso users.id."""
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
    """Test di creazione dell'utente admin."""

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
    """Test della generazione del CSV di export."""

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
        self.assertTrue(csv_lines[0].startswith("\ufeffData"))
        self.assertEqual(len(csv_lines), 2)
        row = csv_lines[1]
        self.assertIn("31/07/2026", row)
        self.assertIn("mario", row)
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
        fields = row.split(",")
        self.assertEqual(fields[4], "")


class TestEffortEntry(DatabaseTestCase):
    def test_insert_entry(self) -> None:
        """L'inserimento valorizza user_id (FK verso users)."""
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
        """Aggiorna un record esistente senza cambiare il proprietario."""
        self.test_insert_entry()
        entry = self.db.get(EffortEntry, self.entry_id)
        self.assertIsNotNone(entry)

        second_client = self.db.execute(
            select(Client).order_by(Client.id.desc())
        ).scalars().first()
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
        self.assertEqual(updated.user_id, self.entry_user_id)


class TestTestUsers(DatabaseTestCase):
    """Test degli utenti di test."""

    def test_seed_creates_six_users(self) -> None:
        """Crea 2 manager (giulia, marco) e 4 user (mario, paolo, anna, elisa)."""
        seed_test_users(self.db)
        usernames = set(self.db.execute(select(User.username)).scalars().all())
        for name in ["giulia", "marco", "mario", "paolo", "anna", "elisa"]:
            self.assertIn(name, usernames)

    def test_seed_promotes_giulia_to_manager(self) -> None:
        """giulia è manager del GRUPPO SOC."""
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
    """Test dei record di test per la segregazione."""

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
    """Test delle voci della sidebar in base al ruolo."""

    def test_user_sidebar_has_registrazioni_and_profile(self) -> None:
        """L'utente USER ha Registrazioni e Profilo nella sidebar."""
        from app.routers.web import _sidebar_items

        user = User(username="mario", password_hash="x", role="user")
        items = _sidebar_items(user)
        self.assertEqual(
            items,
            [
                {"label": "Registrazioni", "href": "/"},
                {"label": "Profilo", "href": "/profile"},
            ],
        )

    def test_manager_sidebar_has_registrazioni_group_and_profile(self) -> None:
        """Il manager ha Registrazioni, Gruppo e Profilo."""
        from app.routers.web import _sidebar_items

        group = self.db.execute(select(Group)).scalars().first()
        user = User(
            username="giulia", password_hash="x", role="manager", group_id=group.id
        )
        items = _sidebar_items(user)
        self.assertEqual(
            items,
            [
                {"label": "Registrazioni", "href": "/"},
                {"label": "Gruppo", "href": "/group"},
                {"label": "Profilo", "href": "/profile"},
            ],
        )

    def test_manager_view_requires_group(self) -> None:
        """Un manager senza group_id non è abilitato alla vista gruppo."""
        from app.routers.web import _is_manager_view

        manager_no_group = User(
            username="giulia", password_hash="x", role="manager", group_id=None
        )
        self.assertFalse(_is_manager_view(manager_no_group))

        group = self.db.execute(select(Group)).scalars().first()
        manager = User(
            username="giulia", password_hash="x", role="manager", group_id=group.id
        )
        self.assertTrue(_is_manager_view(manager))


class TestDisabledUser(DatabaseTestCase):
    """Test della disabilitazione utente."""

    def test_user_defaults_to_not_disabled(self) -> None:
        """Un nuovo utente non è disabilitato per default."""
        u = User(username="disp_test_1", password_hash="x", role="user")
        self.assertFalse(u.disabled)

    def test_disabled_user_default_false_in_db(self) -> None:
        """Inserendo un utente senza specificare disabled, resta False."""
        u = User(username="disp_test_2", password_hash="x", role="user")
        self.db.add(u)
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertIsNotNone(saved)
        self.assertFalse(saved.disabled)

    def test_can_toggle_disabled(self) -> None:
        """Il flag disabled può essere aggiornato su un utente esistente."""
        u = User(username="disp_test_3", password_hash="x", role="user")
        self.db.add(u)
        self.db.commit()
        u.disabled = True
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertTrue(saved.disabled)


class TestUserGracePeriod(DatabaseTestCase):
    """Test della finestra temporale di eliminazione."""

    def test_disabled_at_populated_on_disable(self) -> None:
        """Disabilitando un utente, `disabled_at` viene valorizzato."""
        from app.models.effort_entry import utcnow

        u = User(username="grace_test_1", password_hash="x", role="user")
        self.db.add(u)
        self.db.commit()
        u.disabled = True
        u.disabled_at = utcnow()
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertTrue(saved.disabled)
        self.assertIsNotNone(saved.disabled_at)

    def test_disabled_at_cleared_on_reenable(self) -> None:
        """Riabilitando un utente, `disabled_at` viene azzerato."""
        from app.models.effort_entry import utcnow

        u = User(username="grace_test_2", password_hash="x", role="user")
        self.db.add(u)
        self.db.commit()
        u.disabled = True
        u.disabled_at = utcnow()
        self.db.commit()
        u.disabled = False
        u.disabled_at = None
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertFalse(saved.disabled)
        self.assertIsNone(saved.disabled_at)

    def test_cannot_delete_user_before_grace_period(self) -> None:
        """Un utente non può essere eliminato prima del periodo di grazia."""
        from datetime import timedelta

        from app.models.effort_entry import utcnow
        from app.routers.admin import _can_delete_user

        u = User(
            username="grace_test_3", password_hash="x", role="user", disabled=True
        )
        u.disabled_at = utcnow() - timedelta(seconds=30)
        self.assertFalse(_can_delete_user(u))

    def test_can_delete_user_after_grace_period(self) -> None:
        """Un utente può essere eliminato dopo il periodo di grazia."""
        from datetime import timedelta

        from app.config import USER_DELETE_GRACE_DAYS
        from app.models.effort_entry import utcnow
        from app.routers.admin import _can_delete_user

        u = User(
            username="grace_test_4", password_hash="x", role="user", disabled=True
        )
        u.disabled_at = utcnow() - timedelta(days=USER_DELETE_GRACE_DAYS + 1)
        self.assertTrue(_can_delete_user(u))


class TestUserGroupAssignment(DatabaseTestCase):
    """Test dell'assegnazione gruppo a un utente."""

    def test_user_can_be_assigned_to_group(self) -> None:
        """A un utente può essere assegnato group_id (dal lookup gruppi)."""
        group = self.db.execute(select(Group)).scalars().first()
        u = User(
            username="grp_test_1", password_hash="x", role="user", group_id=group.id
        )
        self.db.add(u)
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertEqual(saved.group_id, group.id)
        self.assertEqual(saved.group.name, group.name)

    def test_user_group_can_be_cleared(self) -> None:
        """Assegnare group_id=None rimuove l'appartenenza al gruppo."""
        group = self.db.execute(select(Group)).scalars().first()
        u = User(
            username="grp_test_2", password_hash="x", role="user", group_id=group.id
        )
        self.db.add(u)
        self.db.commit()
        u.group_id = None
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertIsNone(saved.group_id)


class TestAdminSidebar(DatabaseTestCase):
    """Test della sidebar del ruolo ADMIN."""

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
        """Il mapping dei tipi di lookup restituisce i modelli giusti."""
        from app.routers.admin import _lookup_model

        self.assertIs(_lookup_model("client"), Client)
        self.assertIs(_lookup_model("group"), Group)
        self.assertIs(_lookup_model("activity"), Activity)

    def test_invalid_lookup_type_raises(self) -> None:
        from app.routers.admin import _lookup_model

        with self.assertRaises(ValueError):
            _lookup_model("bogus")

    def test_admin_users_edit_route_registered(self) -> None:
        """La route di modifica utente GET /admin/users/{id}/edit è registrata."""
        from app.routers.admin import router

        paths = {route.path for route in router.routes}
        names = {getattr(route, "name", None) for route in router.routes}
        self.assertIn("/admin/users/{user_id}/edit", paths)
        self.assertIn("admin_users_edit", names)


class TestManagerGroup(DatabaseTestCase):
    """Test del ruolo MANAGER e della vista gruppo."""

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
        """Crea manager + 2 utenti del gruppo + 1 utente fuori gruppo."""
        manager = User(
            username="mgmt1",
            password_hash="x",
            role="manager",
            group_id=self.group.id,
        )
        member = User(
            username="mem1", password_hash="x", role="user", group_id=self.group.id
        )
        member2 = User(
            username="mem2", password_hash="x", role="user", group_id=self.group.id
        )
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
        """giulia (creata/promossa) è manager del GRUPPO SOC."""
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
    """Test della segregazione dati tra utenti."""

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

        self.db.add_all(
            [
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
            ]
        )
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

        resp_update = _save_single(
            payload, self.db, admin, record_id=giulia_entry.id
        )
        self.assertIn("error=validazione", resp_update.headers["location"])

        refreshed = self.db.get(EffortEntry, giulia_entry.id)
        self.assertEqual(refreshed.hours_spent, giulia_entry.hours_spent)

        resp_delete = _delete_entry(giulia_entry.id, self.db, admin)
        self.assertIn("error=validazione", resp_delete.headers["location"])

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
        records_mario = self.db.execute(
            _filter_by_user(stmt, mario)
        ).scalars().all()
        self.assertEqual(len(records_mario), 1)

        stmt_admin = select(EffortEntry)
        records_admin = self.db.execute(
            _filter_by_user(stmt_admin, admin)
        ).scalars().all()
        self.assertEqual(len(records_admin), 3)


class TestEffortEntryValidation(DatabaseTestCase):
    """Test della validazione delle ore."""

    def _payload(self, hours: float) -> EffortEntryCreate:
        client = self.db.execute(select(Client)).scalars().first()
        group = self.db.execute(select(Group)).scalars().first()
        activity = self.db.execute(select(Activity)).scalars().first()
        return EffortEntryCreate(
            user="admin",
            date=date(2026, 8, 15),
            client_id=client.id,
            group_id=group.id,
            activity_id=activity.id,
            hours=hours,
            notes=None,
            description=None,
        )

    def test_valid_hours_range(self) -> None:
        """Il range valido 1-12 è accettato."""
        for h in (1, 1.5, 6.5, 11.5, 12):
            with self.subTest(hours=h):
                model = self._payload(h)
                self.assertEqual(model.hours, round(h, 2))

    def test_invalid_hours_below_min(self) -> None:
        """Ore < 1 sono rifiutate."""
        with self.assertRaises(ValidationError):
            self._payload(0.5)

    def test_invalid_hours_above_max(self) -> None:
        """Ore > 12 sono rifiutate."""
        with self.assertRaises(ValidationError):
            self._payload(12.5)

    def test_invalid_hours_step(self) -> None:
        """Ore non multiple di 0.50 (es. 7.25) sono rifiutate."""
        with self.assertRaises(ValidationError):
            self._payload(7.25)

    def test_hours_float_rounding(self) -> None:
        """Il valore è arrotondato a 2 decimali per evitare errori floating point."""
        model = self._payload(7.4999999)
        self.assertEqual(model.hours, 7.5)

    def test_high_hours_specialist_allowed(self) -> None:
        """Nessun vincolo della vecchia 4h per Supporto Specialistico: 12h ok."""
        model = self._payload(12)
        self.assertEqual(model.hours, 12)


# ─── Nuovi test: profilo utente ───────────────────────────────────────────


class TestControlCharsSanitization(DatabaseTestCase):
    """Test della sanificazione dei caratteri di controllo.

    Verifica che i validatori Pydantic rimuovano i caratteri di controllo
    dai campi di testo prima della persistenza/rendering.
    """

    def test_effort_notes_sanitized(self) -> None:
        entry = EffortEntryCreate(
            user="Mario",
            date=date(2026, 8, 4),
            client_id=1,
            group_id=1,
            activity_id=1,
            hours=7.5,
            notes="Nota con \x07 carattere di controllo",
            description=None,
        )
        self.assertEqual(entry.notes, "Nota con  carattere di controllo")

    def test_effort_description_sanitized(self) -> None:
        entry = EffortEntryCreate(
            user="Mario",
            date=date(2026, 8, 4),
            client_id=1,
            group_id=1,
            activity_id=1,
            hours=7.5,
            notes=None,
            description="Desc \x1f controllo",
        )
        self.assertEqual(entry.description, "Desc  controllo")

    def test_user_sanitized(self) -> None:
        entry = EffortEntryCreate(
            user="Mario\x00",
            date=date(2026, 8, 4),
            client_id=1,
            group_id=1,
            activity_id=1,
            hours=7.5,
        )
        self.assertEqual(entry.user, "Mario")

    def test_username_sanitized(self) -> None:
        from app.schemas.effort import UserCreate

        user = UserCreate(username="mario\x07", password="secret")
        self.assertEqual(user.username, "mario")

    def test_lookup_name_sanitized(self) -> None:
        from app.schemas.effort import LookupCreate

        lookup = LookupCreate(type="client", name="INAIL\x0E")
        self.assertEqual(lookup.name, "INAIL")

    def test_profile_name_sanitized(self) -> None:
        profile = ProfileUpdate(first_name="Mario\x01", last_name=None, email=None)
        self.assertEqual(profile.first_name, "Mario")


class TestProfileColumns(DatabaseTestCase):
    """Test delle colonne profilo utente (nome, cognome, email, pwd_change_required)."""

    def test_users_has_first_name_column(self) -> None:
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("first_name", columns)

    def test_users_has_last_name_column(self) -> None:
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("last_name", columns)

    def test_users_has_email_column(self) -> None:
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("email", columns)

    def test_users_has_password_change_required_column(self) -> None:
        columns = {col["name"] for col in inspect(self.engine).get_columns("users")}
        self.assertIn("password_change_required", columns)

    def test_profile_fields_default_null(self) -> None:
        u = User(username="prof_test", password_hash="x", role="user")
        self.assertIsNone(u.first_name)
        self.assertIsNone(u.last_name)
        self.assertIsNone(u.email)
        self.assertFalse(u.password_change_required)

    def test_profile_fields_persist_correctly(self) -> None:
        u = User(
            username="prof_persist",
            password_hash="x",
            role="user",
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
            password_change_required=True,
        )
        self.db.add(u)
        self.db.commit()
        saved = self.db.get(User, u.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.first_name, "Mario")
        self.assertEqual(saved.last_name, "Rossi")
        self.assertEqual(saved.email, "mario@example.com")
        self.assertTrue(saved.password_change_required)


class TestProfileUpdateValidation(DatabaseTestCase):
    """Test della validazione Pydantic per ProfileUpdate."""

    def test_valid_profile_update(self) -> None:
        data = ProfileUpdate(
            first_name="Giulia",
            last_name="Verdi",
            email="giulia@efftrack.local",
        )
        self.assertEqual(data.first_name, "Giulia")
        self.assertEqual(data.last_name, "Verdi")
        self.assertEqual(data.email, "giulia@efftrack.local")

    def test_empty_strings_become_none(self) -> None:
        data = ProfileUpdate(first_name="", last_name=" ", email="")
        self.assertIsNone(data.first_name)
        self.assertIsNone(data.last_name)
        self.assertIsNone(data.email)

    def test_email_is_lowercased(self) -> None:
        data = ProfileUpdate(email="Giulia@EffTrack.Local")
        self.assertEqual(data.email, "giulia@efftrack.local")

    def test_invalid_email_format(self) -> None:
        with self.assertRaises(ValidationError):
            ProfileUpdate(email="notanemail")

    def test_email_without_dot_after_at(self) -> None:
        with self.assertRaises(ValidationError):
            ProfileUpdate(email="user@localhost")

    def test_all_fields_none(self) -> None:
        data = ProfileUpdate(first_name=None, last_name=None, email=None)
        self.assertIsNone(data.first_name)
        self.assertIsNone(data.last_name)
        self.assertIsNone(data.email)


class TestSelfPasswordChangeValidation(DatabaseTestCase):
    """Test della validazione Pydantic per SelfPasswordChange."""

    def test_valid_password_change(self) -> None:
        data = SelfPasswordChange(current_password="oldpass", new_password="newpass123")
        self.assertEqual(data.current_password, "oldpass")
        self.assertEqual(data.new_password, "newpass123")

    def test_blank_new_password_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SelfPasswordChange(current_password="x", new_password="")
        with self.assertRaises(ValidationError):
            SelfPasswordChange(current_password="x", new_password="   ")

    def test_missing_fields_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SelfPasswordChange(current_password="x")  # type: ignore[arg-type]
        with self.assertRaises(ValidationError):
            SelfPasswordChange(new_password="x")  # type: ignore[arg-type]


class TestSeedProfileFields(DatabaseTestCase):
    """Test dei campi profilo popolati dal seed."""

    def test_admin_seed_has_profile_fields(self) -> None:
        admin = self.db.execute(
            select(User).where(User.username == "admin")
        ).scalar_one_or_none()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.first_name, "Admin")
        self.assertEqual(admin.last_name, "Master")
        self.assertEqual(admin.email, "admin@efftrack.local")
        self.assertFalse(admin.password_change_required)

    def test_test_users_have_profile_fields(self) -> None:
        seed_test_users(self.db)
        mario = self.db.execute(
            select(User).where(User.username == "mario")
        ).scalar_one_or_none()
        self.assertIsNotNone(mario)
        self.assertEqual(mario.first_name, "Mario")
        self.assertEqual(mario.last_name, "Bianchi")
        self.assertEqual(mario.email, "mario@efftrack.local")

        giulia = self.db.execute(
            select(User).where(User.username == "giulia")
        ).scalar_one_or_none()
        self.assertIsNotNone(giulia)
        self.assertEqual(giulia.first_name, "Giulia")
        self.assertEqual(giulia.last_name, "Verdi")
        self.assertEqual(giulia.email, "giulia@efftrack.local")


class TestPasswordChangeIntegration(DatabaseTestCase):
    """Test end-to-end del cambio password."""

    def test_password_hash_updated_after_change(self) -> None:
        from passlib.hash import bcrypt

        old_hash = bcrypt.hash("oldpass")
        user = User(username="pwd_test", password_hash=old_hash, role="user")
        self.db.add(user)
        self.db.commit()

        fresh = self.db.get(User, user.id)
        self.assertTrue(bcrypt.verify("oldpass", fresh.password_hash))

        fresh.password_hash = bcrypt.hash("newpass456")
        self.db.commit()

        refreshed = self.db.get(User, user.id)
        self.assertNotEqual(refreshed.password_hash, old_hash)
        self.assertTrue(bcrypt.verify("newpass456", refreshed.password_hash))
        self.assertFalse(bcrypt.verify("oldpass", refreshed.password_hash))

    def test_password_change_required_reset(self) -> None:
        from passlib.hash import bcrypt

        user = User(
            username="pwd_flag_test",
            password_hash=bcrypt.hash("temppass"),
            role="user",
            password_change_required=True,
        )
        self.db.add(user)
        self.db.commit()

        fresh = self.db.get(User, user.id)
        self.assertTrue(fresh.password_change_required)

        fresh.password_hash = bcrypt.hash("newsecure")
        fresh.password_change_required = False
        self.db.commit()

        refreshed = self.db.get(User, user.id)
        self.assertFalse(refreshed.password_change_required)
        self.assertTrue(bcrypt.verify("newsecure", refreshed.password_hash))


if __name__ == "__main__":
    unittest.main()
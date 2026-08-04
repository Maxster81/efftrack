"""Test funzionali end-to-end (Issue H, Fase 14).

Verifica le route applicative con `TestClient` (FastAPI + HTTPX) su un
database SQLite dedicato ai test (configurato in conftest.py):

- Route pubbliche: `/health`.
- Autenticazione: login/logout, account disabilitato, redirect a login.
- CRUD record: creato, aggiornato, eliminato.
- Export CSV con segregazione per utente.
- Permessi di ruolo: USER non accede ad area admin, MANAGER non accede
  ad area admin, ADMIN ha accesso completo.
- Vista gruppo (MANAGER) e segregazione.
- Profilo utente: visualizzazione e cambio password.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Activity, Client, EffortEntry, User


def _login(client: TestClient, username: str, password: str = "test") -> None:
    """Esegue il login restituendo l'HTTP status (2xx/3xx) e i cookies."""
    resp = client.post(
        "/login", data={"username": username, "password": password}
    )
    assert resp.status_code in (200, 303), (
        f"Login {username} fallito: {resp.status_code}"
    )


def _logout(client: TestClient) -> None:
    client.get("/logout")


def _lookup_ids(db, model) -> list[int]:
    """Restituisce gli id di una tabella lookup in ordine ascendente."""
    return [
        row[0]
        for row in db.execute(select(model.id).order_by(model.id)).all()
    ]


def test_health_is_public(client: TestClient) -> None:
    """GET /health è raggiungibile senza autenticazione e risponde ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


def test_index_redirects_to_login_when_anonymous(client: TestClient) -> None:
    """Senza sessione, GET / redirige al login."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/login")


def test_export_redirects_to_login_when_anonymous(client: TestClient) -> None:
    """Senza sessione, GET /export redirige al login."""
    resp = client.get("/export", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/login")


def test_login_with_valid_user_shows_index(client: TestClient) -> None:
    """Con credenziali valide l'utente USER arriva alla pagina principale."""
    _login(client, "mario")
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Registrazioni" in resp.text


def test_login_with_invalid_credentials(client: TestClient) -> None:
    """Credenziali errate ri-mostrano la pagina di login con errore."""
    resp = client.post(
        "/login", data={"username": "mario", "password": "sbagliata"}
    )
    assert resp.status_code == 200
    assert "Credenziali non valide" in resp.text


def test_login_without_credentials(client: TestClient) -> None:
    """Campo mancante mostra l'errore di compilazione."""
    resp = client.post("/login", data={"username": "", "password": ""})
    assert resp.status_code == 200
    assert "Inserisci username e password" in resp.text


def test_login_disabled_user_rejected(client: TestClient, db_session) -> None:
    """Un account disabilitato non può fare login."""
    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()
    mario.disabled = True
    mario.disabled_at = None
    db_session.commit()

    resp = client.post(
        "/login", data={"username": "mario", "password": "test"}
    )
    assert resp.status_code == 200
    assert "Account disabilitato" in resp.text


def test_login_admin_lands_on_dashboard(client: TestClient) -> None:
    """L'admin arriva alla dashboard /admin dopo il login."""
    resp = client.post(
        "/login", data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/admin"


def test_logout_clears_session(client: TestClient) -> None:
    """Dopo il logout, GET / torna a redirigere al login."""
    _login(client, "mario")
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 200

    _logout(client)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/login")


def test_create_record_via_form(client: TestClient, db_session) -> None:
    """POST / crea un record di effort associato all'utente di sessione."""
    _login(client, "mario")
    client_ids = _lookup_ids(db_session, Client)
    activity_ids = _lookup_ids(db_session, Activity)

    resp = client.post(
        "/",
        data={
            "user": "mario",
            "date": "2026-08-03",
            "client_id": client_ids[0],
            "group_id": 999,  # verrà forzato lato server a quello dell'utente
            "activity_id": activity_ids[0],
            "hours": "7.5",
            "notes": "Nota di test funzionale",
            "description": "",
            "action": "single",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/?success=1" in resp.headers["location"]

    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()
    entries = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == mario.id)
    ).scalars().all()
    assert len(entries) == 21  # 20 seed + 1 nuovo
    created = entries[-1]
    assert created.hours_spent == 7.5
    assert created.group_id == mario.group_id  # forzato al gruppo utente
    assert created.notes == "Nota di test funzionale"


def test_update_record_via_form(client: TestClient, db_session) -> None:
    """POST / con record_id aggiorna il record esistente."""
    _login(client, "mario")
    client_ids = _lookup_ids(db_session, Client)
    activity_ids = _lookup_ids(db_session, Activity)

    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()
    entry = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == mario.id)
    ).scalars().first()
    entry_id = entry.id

    resp = client.post(
        "/",
        data={
            "user": "mario",
            "date": entry.work_date.isoformat(),
            "client_id": client_ids[1],
            "group_id": 999,
            "activity_id": activity_ids[0],
            "hours": "8.0",
            "notes": "Nota aggiornata",
            "description": "",
            "action": "single",
            "record_id": entry_id,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert f"/?success=2&highlight_id={entry_id}" in resp.headers["location"]

    # Forza il refresh dal DB: la sessione db_session ha expire_on_commit=False
    # e l'oggetto è ancora in cache nell'identity map.
    db_session.expire_all()
    updated = db_session.get(EffortEntry, entry_id)
    assert updated.hours_spent == 8.0
    assert updated.notes == "Nota aggiornata"
    assert updated.user_id == mario.id  # proprietario invariato


def test_delete_record_via_form(client: TestClient, db_session) -> None:
    """POST / con action=delete elimina il record dell'utente."""
    _login(client, "mario")
    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()
    entry = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == mario.id)
    ).scalars().first()
    entry_id = entry.id

    resp = client.post(
        "/",
        data={"action": "delete", "record_id": entry_id},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/?success=3" in resp.headers["location"]
    # Forza il refresh: l'oggetto è in cache; dopo l'expire, .get() ri-querya
    # il DB e quindi restituisce None (record eliminato).
    db_session.expire_all()
    assert db_session.get(EffortEntry, entry_id) is None


def test_user_cannot_update_others_record(client: TestClient, db_session) -> None:
    """Un utente non può aggiornare un record altrui (regola aziendale)."""
    _login(client, "mario")
    client_ids = _lookup_ids(db_session, Client)
    activity_ids = _lookup_ids(db_session, Activity)

    giulia = db_session.execute(
        select(User).where(User.username == "giulia")
    ).scalar_one()
    giulia_entry = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == giulia.id)
    ).scalars().first()

    resp = client.post(
        "/",
        data={
            "user": "mario",
            "date": giulia_entry.work_date.isoformat(),
            "client_id": client_ids[0],
            "group_id": 999,
            "activity_id": activity_ids[0],
            "hours": "7.0",
            "notes": "tentativo",
            "description": "",
            "action": "single",
            "record_id": giulia_entry.id,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "error=validazione" in resp.headers["location"]

    # Il record di giulia non è cambiato.
    assert db_session.get(EffortEntry, giulia_entry.id).hours_spent == (
        giulia_entry.hours_spent
    )


def test_cannot_delete_others_record(client: TestClient, db_session) -> None:
    """Un utente non può eliminare un record altrui (regola aziendale)."""
    _login(client, "mario")
    giulia = db_session.execute(
        select(User).where(User.username == "giulia")
    ).scalar_one()
    giulia_entry = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == giulia.id)
    ).scalars().first()

    resp = client.post(
        "/",
        data={"action": "delete", "record_id": giulia_entry.id},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "error=validazione" in resp.headers["location"]
    assert db_session.get(EffortEntry, giulia_entry.id) is not None


def test_export_csv_segregated_per_user(client: TestClient, db_session) -> None:
    """L'export CSV di un USER contiene solo i propri record."""
    _login(client, "mario")
    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()

    resp = client.get("/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

    text = resp.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    # Header + 20 righe (solo i record di mario).
    assert len(lines) == 21
    assert lines[0].startswith("Data")
    # Tutte le righe appartengono a mario.
    for line in lines[1:]:
        assert "mario" in line


def test_export_csv_month_filter(client: TestClient, db_session) -> None:
    """L'export con filtro mese restituisce solo i record del mese."""
    _login(client, "mario")
    mario = db_session.execute(
        select(User).where(User.username == "mario")
    ).scalar_one()
    entries = db_session.execute(
        select(EffortEntry).where(EffortEntry.user_id == mario.id)
    ).scalars().all()
    assert entries, "non ci sono record di seed per mario"
    some_month = entries[0].work_date.strftime("%Y-%m")

    resp = client.get(f"/export?month={some_month}")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    # Solo record dello stesso mese (almeno l'header + quelle del mese).
    assert len(lines) >= 2
    for line in lines[1:]:
        assert f"/{some_month[-2:]}/" in line or some_month in line


def test_anonymous_cannot_access_admin(client: TestClient) -> None:
    """Senza sessione, /admin risponde 401 (richiesti diritti admin)."""
    resp = client.get("/admin")
    assert resp.status_code == 401


def test_user_cannot_access_admin(client: TestClient) -> None:
    """Un USER riceve 403 sull'area admin."""
    _login(client, "mario")
    resp = client.get("/admin")
    assert resp.status_code == 403


def test_manager_cannot_access_admin(client: TestClient) -> None:
    """Un MANAGER riceve 403 sull'area admin (solo admin può)."""
    _login(client, "giulia")
    resp = client.get("/admin")
    assert resp.status_code == 403


def test_admin_can_access_dashboard(client: TestClient) -> None:
    """L'ADMIN accede alla dashboard."""
    _login(client, "admin", password="admin")
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert "Dashboard" in resp.text or "Pannello Admin" in resp.text


def test_manager_group_view_shows_only_group_members(
    client: TestClient, db_session
) -> None:
    """La vista /group del manager mostra solo i membri del suo gruppo."""
    _login(client, "giulia")  # manager GRUPPO SOC
    resp = client.get("/group")
    assert resp.status_code == 200
    # Contiene utenti di mario/paolo (SOC), non anna/elisa (NOC).
    assert "mario" in resp.text or "paolo" in resp.text
    assert "anna" not in resp.text
    assert "elisa" not in resp.text


def test_user_cannot_access_group_view(client: TestClient) -> None:
    """Un USER normale viene rediretto via da /group."""
    _login(client, "mario")
    resp = client.get("/group", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"


def test_manager_group_export_segregated(client: TestClient, db_session) -> None:
    """L'export del gruppo contiene solo gli utenti del gruppo del manager."""
    _login(client, "giulia")  # GRUPPO SOC → mario, paolo
    resp = client.get("/group/export")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8-sig")
    # Solo membri SOC (giulia, mario, paolo) — mai NOC (anna, elisa, marco).
    assert "anna" not in text
    assert "elisa" not in text
    assert "marco" not in text
    assert any(u in text for u in ("mario", "paolo", "giulia"))


def test_profile_page_requires_auth(client: TestClient) -> None:
    """Senza sessione, /profile redirige al login."""
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/login")


def test_profile_page_shows_user_data(client: TestClient) -> None:
    """La pagina profilo mostra i dati dell'utente loggato."""
    _login(client, "mario")
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert "Mario" in resp.text  # first_name
    assert "Bianchi" in resp.text  # last_name
    assert "mario@efftrack.local" in resp.text


def test_change_password_flow(client: TestClient, db_session) -> None:
    """L'utente cambia password e può rientrare con quella nuova."""
    _login(client, "mario")
    resp = client.post(
        "/profile/change-password",
        data={
            "current_password": "test",
            "new_password": "nuovapassword",
            "confirm_password": "nuovapassword",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/profile?pwd_ok=1" in resp.headers["location"]

    _logout(client)

    # Login con la vecchia password fallisce.
    resp = client.post(
        "/login", data={"username": "mario", "password": "test"}
    )
    assert resp.status_code == 200
    assert "Credenziali non valide" in resp.text

    # Login con la nuova password funziona.
    _login(client, "mario", password="nuovapassword")
    resp = client.get("/")
    assert resp.status_code == 200
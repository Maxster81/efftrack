# System Patterns — Effort Tracking

## Architettura

### Stack
- **Backend**: Python 3.10+, FastAPI, Uvicorn.
- **Template**: Jinja2 server-side.
- **ORM**: SQLAlchemy 2.x.
- **DB**: SQLite3, modalità WAL + foreign keys ON su ogni connessione.
- **Static**: CSS vanilla + JS vanilla, in `app/static/`.
- **Configurazione**: `python-dotenv` per caricare `.env` (sviluppo). In produzione systemd `EnvironmentFile`.
- **Logging**: modulo `logging` standard, configurato centralmente in `app/core/logging_config.py`.

### Struttura directory
```
efftrack/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, mount static, include routers
│   ├── config.py               # env vars, path DB, SECRET_KEY placeholder
│   ├── db.py                   # engine, SessionLocal, Base, get_db, PRAGMA WAL/FK
│   ├── dependencies.py         # get_db, futuri get_current_user
│   ├── core/                   # costanti, validazioni condivise, logging_config, seed
│   ├── models/                 # ORM SQLAlchemy
│   ├── repositories/           # accesso dati
│   ├── services/               # logica business (es. derivazione mese)
│   ├── schemas/                # Pydantic input/output
│   ├── routers/
│   │   ├── web.py              # pagine HTML (Jinja2)
│   │   └── api.py              # endpoint REST (futuro)
│   ├── templates/              # base.html, index.html, partials/
│   └── static/                 # css, js vanilla
├── systemd/                    # template service (NON attivato automaticamente)
├── data/                       # file SQLite (gitignored)
├── tests/                      # test (da Fase 4 in poi)
├── memory-bank/                # documentazione persistente
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── VERSION
```

### Layer e responsabilità
- **routers/**: gestiscono HTTP, parsing parametri, risposte HTML/JSON. Non contengono logica di business.
- **services/**: logica di business (validazioni dominio, derivazione mese, regole di show/hide campi).
- **repositories/**: unico punto che parla con SQLAlchemy. Le route chiamano i repository, mai il modello direttamente.
- **schemas/**: Pydantic per input form e output API.
- **models/**: definizioni ORM.
- **core/**: costanti e funzioni condivise.

### Pattern FastAPI
- `lifespan` con `@asynccontextmanager` per init/shutdown.
- `APIRouter(prefix=...)` per ogni modulo.
- `Depends(get_db)` per la sessione DB.
- Distinzione netta tra router web (HTML) e router api (JSON).
- In `lifespan`: `setup_logging()` (da `app/core/logging_config.py`) prima di qualsiasi log applicativo.

## Logging (Fase 9)
- Configurazione centralizzata in `app/core/logging_config.py` (`setup_logging()` idempotente).
- Livello da env `EFFORT_TRACKING_LOG_LEVEL` (default INFO).
- Formato `%(asctime)s %(levelname)s [%(name)s] %(message)s` (leggibile console/journald).
- I logger prendono il nome del modulo via `logging.getLogger(__name__)`.
- I log applicativi escono su stdout → catturati da journald in systemd.

## Ciclo di completamento fasi

1. Implementazione della fase.
2. Verifiche tecniche interne di Cline.
3. **STOP** di Cline, attesa conferma utente.
4. Aggiornamento `progress.md` e `activeContext.md` con stato "completata".
5. Bump `VERSION` (unico file di versione) se necessario.
6. Commit su `develop` con messaggio `type(scope): description`.
7. Tag annotato `vX.Y.Z` sullo stesso commit.
8. Solo allora la fase si considera chiusa e il memory bank riflette lo stato reale.

## Persistenza

### Vincoli SQLite
- `PRAGMA journal_mode=WAL` su ogni connessione.
- `PRAGMA foreign_keys=ON` su ogni connessione.
- DB file in `data/efftrack.db`, fuori dal versionamento.

### Modello dati (completo dalla Fase 4; auth in Fase 10)
- `clients(id, name UNIQUE)` — seed: INAIL, MDS. (Solo `name`: la colonna `code` è stata rimossa in Fase 4 su decisione utente.)
- `groups(id, name UNIQUE)` — seed: GRUPPO SOC.
- `activities(id, name UNIQUE, requires_description BOOL)` — seed: SOC-Conduzione (no), SOC-Supporto Specialistico (sì).
- `effort_entries(id, user_id NULL senza FK, client_id FK, group_id FK, activity_id FK, work_date DATE, hours_spent NUMERIC(4,2) CHECK >0 AND <=24, notes TEXT NULL, description TEXT NULL, created_at, updated_at)`.
- `users(id, username UNIQUE, password_hash, role)` — Fase 10 (role: admin/manager/user, usato da Fase 12).
- `Mese` **mai** persistito, derivato da `work_date` via service helper.
- **Seed**: `app/core/seed_lookup_tables(db)` + `seed_admin_user(db)` idempotenti, eseguiti nel lifespan di `main.py` dopo `create_all`.
- **Test**: `tests/test_models.py` (pytest + SQLite in-memory isolato).

### Migrazioni
- Fase 0–8: `CREATE TABLE IF NOT EXISTS` + seed idempotente + (se serve) `ALTER TABLE` controllato a startup, documentato in `progress.md`. NB: la rimozione di una colonna (come `code` in Fase 4) non è gestita automaticamente — va rigenerato il DB.
- Se la complessità cresce: introduzione Alembic (proposta con analisi pro/contro, decisione documentata).

## Tema e CSS
- Variabili CSS in `:root` + blocchi `[data-theme="light"]` e `[data-theme="dark"]` (palette blu navy + grigi neutri).
- Toggle dark/light funzionante (Fase 9b): due modalità, preferenza salvata in `localStorage["theme-preference"]`, default light. Nessun rilevamento automatico di sistema.
- Script inline anti-FOUC nel `<head>` di `base.html` applica il tema salvato prima del rendering.
- `app/static/theme.js` gestisce il toggle e aggiorna `data-theme="dark"` su `<html>`.

## Autenticazione (Fase 10)
- Sessione HTTP firmata via `starlette.middleware.sessions.SessionMiddleware` con `SECRET_KEY` da config.
- Route: `GET/POST /login`, `GET /logout` (router `app/routers/auth.py`).
- Password hashate con `passlib[bcrypt]` (`bcrypt` pinnato `<4.1` per compatibilità passlib 1.7.4).
- Dependency `get_current_user` in `app/dependencies.py` legge `request.session["user_id"]` e carica l'utente.
- Route business (`/`, `/export`, POST) protette: se `AUTH_ENABLED` e niente sessione → redirect a `/login` (`_require_auth`).
- Campo User del form forzato lato server allo username della sessione (readonly client).
- `/health` resta pubblico.
- Seed utente admin idempotente (primo utente master) con username/password da config (env var).

## Sicurezza
- `SECRET_KEY` letto da env var, default di sviluppo con placeholder esplicito.
- Validazione server-side obbligatoria su tutti gli input in persistenza.
- Campi numerici limitati a range consentiti (es. `hours_spent` 1..24).
- Dropdown validati lato server, mai fidarsi dei valori del browser.
- Password mai in chiaro: solo hash bcrypt in `users.password_hash`.
- La password admin in produzione va cambiata via env var (mai lasciare admin/admin).

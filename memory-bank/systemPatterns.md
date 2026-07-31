# System Patterns — Effort Tracking

## Architettura

### Stack
- **Backend**: Python 3.10+, FastAPI, Uvicorn.
- **Template**: Jinja2 server-side.
- **ORM**: SQLAlchemy 2.x.
- **DB**: SQLite3, modalità WAL + foreign keys ON su ogni connessione.
- **Static**: CSS vanilla + JS vanilla, in `app/static/`.

### Struttura directory
```
efftrack/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, mount static, include routers
│   ├── config.py               # env vars, path DB, SECRET_KEY placeholder
│   ├── db.py                   # engine, SessionLocal, Base, get_db, PRAGMA WAL/FK
│   ├── dependencies.py         # get_db, futuri get_current_user
│   ├── core/                   # costanti e validazioni condivise
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

### Modello dati (previsto, completo in Fase 4)
- `clients(id, code, name)` — seed: INAIL, MDS.
- `groups(id, code, name)` — seed: GRUPPO SOC.
- `activities(id, code, name, requires_description BOOL)` — seed: SOC-Conduzione (no), SOC-Supporto Specialistico (sì).
- `effort_entries(id, user_id NULL FK, client_id FK, group_id FK, activity_id FK, work_date DATE, hours_spent NUMERIC(4,2) CHECK 1..24, notes TEXT NULL, description TEXT NULL, created_at, updated_at)`.
- `Mese` **mai** persistito, derivato da `work_date` via service helper.

### Migrazioni
- Fase 0–8: `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE` controllato a startup, documentato in `progress.md`.
- Se la complessità cresce: introduzione Alembic (proposta con analisi pro/contro, decisione documentata).

## Tema e CSS
- Variabili CSS in `:root` con palette blu navy + grigi neutri.
- Struttura predisposta per `data-theme="dark"` (variabili alternative), toggle UI rimandato a Fase 9.

## Sicurezza
- `SECRET_KEY` letto da env var, default di sviluppo con placeholder esplicito.
- Validazione server-side obbligatoria su tutti gli input in persistenza.
- Campi numerici limitati a range consentiti (es. `hours_spent` 1..24).
- Dropdown validati lato server, mai fidarsi dei valori del browser.

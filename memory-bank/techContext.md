# Tech Context — Effort Tracking

## Ambiente di sviluppo
- **OS**: Ubuntu in **WSL** (Windows Subsystem for Linux), senza display grafico.
  - Niente `xdg-open`/`open` per aprire il browser: per verifiche visive l'utente apre l'URL dal browser sul lato Windows (es. `http://localhost:8000/`).
  - I comandi Cline devono usare tool CLI standard (`curl`, `pgrep`, `pkill`, `git`), mai comandi GUI.
- **Versione rilevata**: Python 3.12.3, pip 24.0.

## Linguaggio e runtime
- **Python**: 3.10+ (per `X | None` syntax e performance).
- **Virtualenv**: `python3 -m venv .venv`.
- **Package manager**: `pip` con `requirements.txt`.

## Framework e librerie principali
- **FastAPI** — web framework, tipizzazione nativa, `lifespan` pattern, router modulari.
- **Uvicorn** (con extra `standard`) — ASGI server, bind su `0.0.0.0` in dev, su `127.0.0.1` in prod dietro reverse proxy.
- **Jinja2** — template engine server-side.
- **SQLAlchemy 2.x** — ORM type-safe, predisposizione a migrazione PostgreSQL.
- **Pydantic v2** — validazione input/output.
- **python-multipart** — parsing form data.
- **python-dotenv** — carica `.env` in sviluppo (dalla Fase 9).
- **pytest** — framework di test (dipendenza DEV, in `requirements-dev.txt`).

## Database
- **SQLite3** in `data/efftrack.db` (gitignored).
- `PRAGMA journal_mode=WAL` e `PRAGMA foreign_keys=ON` su ogni connessione.
- Migrazione futura a PostgreSQL: cambiare solo `DATABASE_URL` in config, niente refactoring di repository/service.

## Setup di sviluppo (Ubuntu)
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd /home/mbocchini/efftrack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Avvio in sviluppo
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Poi:
- `http://localhost:8000/` → pagina indice
- `http://localhost:8000/health` → health check (status app + check DB)
- `http://localhost:8000/docs` → documentazione OpenAPI automatica di FastAPI

## Configurazione via env vars
- `EFFORT_TRACKING_SECRET_KEY` — chiave segreta per future firme JWT/sessioni (placeholder in Fase 0).
- `EFFORT_TRACKING_DB_URL` — default `sqlite:///./data/efftrack.db`.
- `EFFORT_TRACKING_HOST` — default `0.0.0.0` in dev.
- `EFFORT_TRACKING_PORT` — default `8000`.
- `EFFORT_TRACKING_LOG_LEVEL` — default `INFO` (DEBUG, INFO, WARNING, ERROR).

### File `.env`
- Il file `.env` (gitignored) viene caricato automaticamente da `config.py` via `load_dotenv()`.
- Il template di riferimento è `.env.example` (committato).
- In produzione systemd usa `EnvironmentFile=/etc/efftrack.env`; NON si usa il `.env` locale.

## Vincoli di deploy
- **No Docker** come prerequisito.
- Deploy target: **Ubuntu con `systemd`** (template `systemd/efftrack.service` pronto, non attivato di default).
- Reverse proxy consigliato in produzione (nginx/Caddy) davanti a Uvicorn.

## Vincoli di sicurezza
- Tutti i secrets da env var, mai hardcodati.
- `.env.example` con placeholder espliciti, `.env` reale **mai** in git.
- Validazione server-side obbligatoria.
- Dropdown mai fidati: validati lato server prima della persistenza.
- Campi numerici vincolati a range consentiti.

## Test
- **Framework**: `pytest` (dalla Fase 9), in `requirements-dev.txt` (dipendenza solo di sviluppo).
- **Installazione**: `.venv/bin/pip install -r requirements-dev.txt`
- **Esecuzione**: `.venv/bin/python -m pytest tests/ -v`
- **DB di test**: SQLite in-memory isolato (`tests/test_models.py`), separato dal DB di sviluppo `data/efftrack.db`.
- `pytest` non è in `requirements.txt` (produzione pulita).

## Rigenerazione DB di sviluppo
- Il DB `data/efftrack.db` è **gitignored** e viene creato/seeded automaticamente al primo avvio (lifespan di `app/main.py`).
- Se cambia lo schema (es. rimozione colonna), il DB va **cancellato** (`rm -f data/efftrack.db data/efftrack.db-shm data/efftrack.db-wal`) e rigenerato riavviando il server.

## Tool di sviluppo
- `git` per versionamento, branching su `develop`.
- `pip` per dipendenze.
- `pytest` per i test automatici.
- Nessun tool esotico: editor + browser + curl.

## Note di compatibilità
- Codice Python con type hints stile 3.10+ (`X | None`).
- Stile descrittivo semplice nei docstring.
- Repository dedicati per accesso dati (nessuna query sparsa nei router).

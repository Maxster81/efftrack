# Progress — Effort Tracking

## Stato globale
- **Ultima fase completata**: Fase 2 ✅ completata il 2026-07-31.
- **Fase in corso**: nessuna. In attesa di task per la Fase 3.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.2.0` (tag `v0.2.0` annotato su `develop`).

## Roadmap

### Fase 0 — Bootstrap progetto
- **Stato**: ✅ completata.
- **Cosa è stato fatto**:
  - Inizializzazione progetto e struttura directory.
  - Creazione venv e `requirements.txt`.
  - Server di test con route `/` e `/health`.
  - Memory bank iniziale (i 6 file core).
  - Template `systemd/efftrack.service` (non attivato).
  - `README.md` tecnico minimale, `VERSION` 0.1.0, `.env.example`, `.gitignore`.
  - Commit `chore(bootstrap): phase 0 scaffolding` su `main` (con successiva creazione di `develop`).
  - Tag annotato `v0.1.0`.

### Fase 1 — Pagina HTML statica raggiungibile
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: `GET /` restituisce una pagina HTML statica "server raggiungibile" via browser.
- **Cosa è stato fatto**:
  - Refactor routing: `GET /` e `GET /health` spostate in `app/routers/web.py` come `APIRouter(tags=["web"])`.
  - Nuovo `app/routers/api.py` con `APIRouter(prefix="/api", tags=["api"])` come placeholder.
  - `app/main.py` snellito: solo app, lifespan, mount static, include router.
  - `app/config.py` esteso con `TEMPLATES_DIR` e `STATIC_DIR`.
  - Verifiche curl su `127.0.0.1:8000`: `/` (200), `/health` (200), `/docs` (200), `/static/style.css` (200).
  - Convenzione di porta operativa: verifiche su `127.0.0.1:8000`.
- **Versioning**: bump `VERSION` `0.1.0` → `0.1.1` (PATCH).
- **Branch**: commit su `develop`, tag annotato `v0.1.1`. Niente `main`.
- **Commit**: `refactor(routing): phase 1 web router extraction`.

### Fase 2 — Layout statico stile effort tracking
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: replicare la struttura del mock (form in alto, tabella sotto) con CSS variabili, niente logica reale, niente salvataggio.
- **Cosa è stato fatto**:
  - **`base.html`**: aggiunta icona utente decorativa (SVG) nell'header, placeholder per il futuro login (Fase 10).
  - **`index.html`**: layout reale a due sezioni:
    - Form di inserimento (card) con campi User, Data, Cliente, Gruppo, Attività, Ore Spese, Note, Descrizione + pulsante Salva centrale.
    - Tabella elenco (card) con header a 7 colonne (Data, Cliente, Gruppo, Attività, Ore, Note, Descrizione), contatore `({{ records|length }} record)` e stato vuoto "Nessuna registrazione presente."
    - Campo **Descrizione** sempre visibile in Fase 2 (show/hide condizionale in Fase 3).
  - **`style.css`**: rimosse regole welcome card, aggiunte regole form grid 2 colonne responsive (breakpoint 720px), focus ring, pulsante Salva, tabella con header blu navy, righe alternate/hover, messaggio vuoto.
  - **`web.py`**: label fase aggiornata a "Fase 2 — Layout statico stile effort tracking", context `records: []` (predisposizione Fase 6).
  - **`config.py`**: `APP_VERSION` allineata da `0.1.0` a `0.2.0` (corretta discrepanza residua dalla Fase 1).
  - **Venv**: ricreato `.venv` su nuovo OS (Python 3.12.3), dipendenze installate da `requirements.txt`.
  - Verifiche curl su `127.0.0.1:8000`: `/` (200, 4949 byte, struttura HTML verificata), `/health` (200, `version:0.2.0`), `/docs` (200), `/static/style.css` (200).
- **Versioning**: bump `VERSION` `0.1.1` → `0.2.0` (MINOR: nuovo layout UI).
- **Branch**: commit su `develop`, tag annotato `v0.2.0`. Niente `main`.
- **Commit**: `feat(ui): phase 2 static effort tracking layout`.

### Fase 3 — Form interattivo con lookup hardcoded
- **Stato**: non iniziata.
- **Obiettivo**: form reale con dropdown hardcoded, validazione base, show/hide campo Descrizione. Primo JS vanilla (`static/*.js`).

### Fase 4 — Database e seed lookup
- **Stato**: non iniziata.
- **Obiettivo**: SQLAlchemy + SQLite + tabelle lookup + tabella `effort_entries` + seed iniziale.

### Fase 5 — Salvataggio record
- **Stato**: non iniziata.
- **Obiettivo**: POST di salvataggio con validazione server-side e messaggi di esito.

### Fase 6 — Elenco record
- **Stato**: non iniziata.
- **Obiettivo**: tabella inferiore caricata dal DB, ordinata per data decrescente.

### Fase 7 — Selezione record e update
- **Stato**: non iniziata.
- **Obiettivo**: click su riga → form precompilato → update.

### Fase 8 — Export CSV / XLSX
- **Stato**: non iniziata.
- **Obiettivo**: export con filtri base.

### Fase 9 — Refactoring, logging, env, systemd
- **Stato**: non iniziata.
- **Obiettivo**: pulizia, logging strutturato, `.env.example`, systemd, toggle dark/light.

### Fase 10 — Autenticazione locale
- **Stato**: non iniziata.
- **Obiettivo**: login user/password con password hashate e sessione.

### Fase 11 — Multiutente e segregazione
- **Stato**: non iniziata.
- **Obiettivo**: `user_id` valorizzato, segregazione dei dati, predisposizione ruoli.

### Fase 12 — Hardening produzione
- **Stato**: non iniziata.
- **Obiettivo**: controllo validazioni, gestione errori, backup SQLite, note migrazione PostgreSQL.

## Decisioni di versioning
- **Strategia**: SemVer. Versione tracciata solo nel file `VERSION` (unico servizio, niente repliche in `__init__.py`).
- **Bump ad ogni commit funzionale**, tag annotato `vX.Y.Z` sullo stesso commit.
- **MAJOR** = breaking changes architetturali.
- **MINOR** = nuove funzionalità retrocompatibili.
- **PATCH** = bug fix, refactoring interno, miglioramenti UI.

## Cose note / limitazioni accettate
- Tema dark/light solo come struttura CSS variabili fino a Fase 9.
- Migrazioni schema con `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE` controllato fino a Fase 9; Alembic proposto se la complessità cresce.
- Nessun test automatico fino a Fase 4.
- `user_id` nullable in `effort_entries` dal suo inserimento, valorizzato in Fase 11.
- Import `Engine` non usato in `app/routers/web.py` (da ripulire in refactor futuro).
# Progress — Effort Tracking

## Stato globale
- **Ultima fase completata**: Fase 4 ✅ completata il 2026-07-31.
- **Fase in corso**: nessuna. In attesa di task per la Fase 5.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.4.0` (tag `v0.4.0` annotato su `develop`).

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
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: form reale con dropdown hardcoded, validazione base, show/hide campo Descrizione. Primo JS vanilla (`static/*.js`).
- **Cosa è stato fatto**:
  - **`app/static/form.js`** (nuovo): show/hide "Descrizione attività" se attivita = "SOC-Supporto Specialistico"; validazione client-side (User, Data, Cliente, Gruppo, Attività, Ore obbligatori; Ore 0.25..24 step 0.25 con virgola; Descrizione attività obbligatoria solo se visibile; Note opzionale); errori `.is-invalid` + banner `#form-error role="alert"` + focus primo campo non valido.
  - **`app/static/style.css`**: aggiunte `.is-hidden`, `.form-group.is-invalid *`, `.form-error`.
  - **`app/templates/index.html`**: area errore, label e header tabella rinominati "Descrizione attività", gruppo descrizione inizialmente `is-hidden`, `novalidate`, script `form.js` con `defer`.
  - **`app/templates/base.html`**: aggiunto blocco `{% block scripts %}`.
  - **Binding corretto**: server riavviato su `0.0.0.0:8000` (prima era erroneamente su 127.0.0.1, non raggiungibile dal browser Windows). Verificato accesso da IP host WSL (172.20.144.1).
  - Verifiche curl: `/` (200, 5155 byte), `/health` (200), `/static/form.js` (200 text/javascript), `/static/style.css` (200).
  - **Verifica utente (browser)**: warning su submit vuoto; show/hide Descrizione attività con Supporto Specialistico; submit completo → method not allowed (atteso fino a Fase 5).
- **Versioning**: bump `VERSION` `0.2.0` → `0.3.0` (MINOR: nuova funzionalità).
- **Branch**: commit su `develop`, tag annotato `v0.3.0`. Niente `main`.
- **Commit**: `feat(ui): phase 3 interactive form with validation`.

### Fase 4 — Database e seed lookup
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: SQLAlchemy + SQLite + tabelle lookup (`clients`, `groups`, `activities`) + tabella `effort_entries` + seed iniziale. Sostituire dropdown hardcoded con contenuto DB. Predisposizione test automatici.
- **Cosa è stato fatto**:
  - **Modelli ORM** (nuovi in `app/models/`): `Client`, `Group`, `Activity` (con `requires_description`) e `EffortEntry` (FK su clients/groups/activities, `work_date`, `hours_spent` CHECK `>0 AND <=24`, `notes`/`description` nullable, `created_at`/`updated_at` UTC naive, `user_id` nullable senza FK).
  - **`app/core/seed.py`** (nuovo): `seed_lookup_tables` idempotente — clients INAIL/MDS, groups GRUPPO SOC, activities SOC-Conduzione(false)/SOC-Supporto Specialistico(true).
  - **`app/main.py`**: nel lifespan, dopo `create_all`, chiama il seed; `import app.models` per registrare lo schema.
  - **`app/routers/web.py`**: `index` carica i lookup dal DB (order_by name) e passa `today` per il default data.
  - **`app/templates/index.html`**: dropdown dinamici (solo `name`, valori = FK id), campo Data con `value=today`.
  - **`app/static/form.js`**: show/hide Descrizione attività basato su `data-requires-description` (non più su stringa).
  - **`tests/test_models.py`** (nuovo): 6 test unittest (schema, seed, seed idempotente, inserimento EffortEntry) su SQLite in-memory isolato. Tutti OK.
  - **Decisione utente**: rimossa colonna `code` dai lookup (basta `name` UNIQUE) — eliminata duplicazione nei dropdown. DB di sviluppo rigenerato.
  - **Data odierna**: campo Data prepopolato con `date.today()` lato server.
  - Verifica utente: dropdown puliti, data odierna, "Salva" → 405 atteso (persistenza Fase 5).
- **Versioning**: bump `VERSION` `0.3.0` → `0.4.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.4.0`. Niente `main`.
- **Commit**: `feat(db): phase 4 database schema and lookup seed`.

### Fase 5 — Salvataggio record
- **Stato**: non iniziata.
- **Obiettivo**: POST di salvataggio con validazione server-side (Pydantic) e messaggi di esito; requisito Descrizione attività vincolato a `requires_description`.

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
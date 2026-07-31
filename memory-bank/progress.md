# Progress — Effort Tracking

## Stato globale
- **Ultima fase completata**: Fase 0 ✅ completata il 2026-07-31.
- **Fase in corso**: **Fase 1** — Pagina HTML statica raggiungibile.
- **Stato**: in attesa di nuovo task.

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
- **Stato**: in corso.
- **Obiettivo**: `GET /` restituisce una pagina HTML statica "server raggiungibile" via browser (in pratica già in piedi dalla Fase 0, da consolidare).

### Fase 2 — Layout statico stile effort tracking
- **Stato**: non iniziata.
- **Obiettivo**: replicare la struttura del mock (form in alto, tabella sotto) con CSS variabili, niente logica reale, niente salvataggio.

### Fase 3 — Form interattivo con lookup hardcoded
- **Stato**: non iniziata.
- **Obiettivo**: form reale con dropdown hardcoded, validazione base, show/hide campo Descrizione.

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
- Nessun test automatico in Fase 0 (previsti da Fase 4).
- `user_id` nullable in `effort_entries` dal suo inserimento, valorizzato in Fase 11.

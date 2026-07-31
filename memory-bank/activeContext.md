# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 4 ✅ (2026-07-31).
- **Fase in corso**: nessuna. In attesa di task per la Fase 5.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.4.0` (tag `v0.4.0` annotato su `develop`).
- **Nota ambiente**: sviluppo su **Ubuntu in WSL** (Python 3.12.3, pip 24.0). Venv ricreato in questa macchina. Dipendenze: fastapi 0.141.1, uvicorn 0.52.0, sqlalchemy 2.0.51, pydantic 2.13.4, jinja2 3.1.6, python-multipart 0.0.32.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: struttura CSS variabili presente; toggle dark/light rimandato a Fase 9.
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Bump confermato a `0.4.0` per la Fase 4 (MINOR: nuova funzionalità di persistenza).
- **Campo User**: scrivibile nelle fasi pre-auth (intenzionale). In Fase 10 diventerà read-only derivato dalla sessione.
- **Etichetta descrizione**: "Descrizione attività" per coerenza col vecchio tool. **Note** opzionale; **Descrizione attività** obbligatoria solo quando l'attività richiede descrizione (`requires_description`).
- **Modello dati lookup**: non servono `code` e `name`, basta il `name` (con UNIQUE). Rimossa la colonna `code` in Fase 4 su decisione utente. I dropdown mostrano solo `name`.
- **Data default**: il campo Data del form è pre-popolato con `date.today()` lato server (`today` nel context).
- **Bind server**: in sviluppo bind su `0.0.0.0` (accessibile da browser Windows via WSL).
- **Test automatici**: da Fase 4 in poi, `unittest` (stdlib) con SQLite in-memory isolato. Nessuna dipendenza di test extra.

## Modifiche di Fase 4 (database e seed lookup)
- **Nuovi modelli ORM** in `app/models/`:
  - `client.py` → `Client` (tabella `clients`, colonna `name` UNIQUE)
  - `group.py` → `Group` (tabella `groups`, colonna `name` UNIQUE)
  - `activity.py` → `Activity` (tabella `activities`, colonna `name` UNIQUE, `requires_description` BOOL)
  - `effort_entry.py` → `EffortEntry` (tabella `effort_entries`: `user_id` nullable senza FK, FK su clients/groups/activities, `work_date`, `hours_spent` NUMERIC(4,2) con CHECK `>0 AND <=24`, `notes` nullable, `description` nullable, `created_at`/`updated_at` con helper UTC naive che evita la deprecation di `datetime.utcnow`)
- **`app/models/__init__.py`**: esporta tutti i modelli (registra le tabelle su `Base.metadata`).
- **`app/core/seed.py`** (NUOVO): `seed_lookup_tables(db)` idempotente (solo name): clients INAIL/MDS, groups GRUPPO SOC, activities SOC-Conduzione (requires_desc=false) / SOC-Supporto Specialistico (requires_desc=true).
- **`app/main.py`**: nel `lifespan` dopo `create_all`, chiama `seed_lookup_tables(db)`. Incluso `import app.models` per registrare lo schema.
- **`app/routers/web.py`**: `index` carica i lookup dal DB (order_by `name`) e passa `clients`, `groups`, `activities` al template; aggiunto `today` (data odierna) per il default del campo Data; rimosso l'import `Engine` inutilizzato. Label fase "Fase 4 — Database e seed lookup".
- **`app/templates/index.html`**: dropdown popolati dai lookup (mostrano solo `name`), valori = FK id; campo Data con `value="{{ today }}"`.
- **`app/static/form.js`**: show/hide Descrizione attività ora usa `data-requires-description` della option (non più confronto su stringa fissa), poiché il valore del select è l'id numerico dell'attività.
- **`tests/test_models.py`** (NUOVO): 6 test unittest su schema, seed (idempotente) e inserimento EffortEntry, su SQLite in-memory isolato.
- **DB di sviluppo**: cancellato e rigenerato con lo schema nuovo (senza colonna code).

## Verifiche Fase 4 (test + curl su 0.0.0.0:8000)
- **Test**: `unittest discover -s tests` → 6 test OK.
- `GET /health` → 200 `db:ok`.
- `GET /` → dropdown clienti `INAIL`, `MDS`; gruppi `GRUPPO SOC`; attività `SOC-Conduzione`(false)/`SOC-Supporto Specialistico`(true); campo Data `value="2026-07-31"` (data odierna).
- **Verifica utente (browser)**: dropdown puliti (solo name), data odierna prepopolata, "Salva" → 405 atteso (persistenza in Fase 5).

## Separazione backend / frontend (Fase 4)
- **Area applicativa**: modelli ORM, seed, `main.py` (lifespan), `web.py` (lookup + today), test.
- **Area UI**: `index.html` (dropdown dinamici, data default), `form.js` (show/hide su data-attribute).
- **Area documentale**: aggiornamento `activeContext.md`, `progress.md`, `systemPatterns.md`, `techContext.md`.

## Convenzione operativa: porta e binding
- **Porta canonica**: `8000`. **Binding in sviluppo**: `0.0.0.0` (raggiungibile dal browser Windows).
- Se la 8000 è occupata, kill e riavvio.
- **Ambiente**: Ubuntu in WSL, niente display grafico; niente `xdg-open`/`open`. Per verifiche visive l'utente apre `http://localhost:8000/` nel browser Windows. Tool CLI standard solo (`curl`, `pgrep`, `pkill`, `git`).

## Regola operativa attiva (workflow)
1. Implemento la fase corrente. 2. Verifiche tecniche. 3. Se per completare una fase servono modifiche richieste dall'utente, le applico e verifico. 4. **Solo dopo conferma esplicita**: aggiorno memory bank + bump VERSION + commit su develop + tag annotato.

## Decisione speciale di Fase 0 (eccezione una tantum)
- Committ iniziale su `main` autorizzato; poi branch `develop`. `main` non si tocca senza autorizzazione esplicita nel messaggio corrente.

## Prossima fase (Fase 5)
- **Salvataggio record**: POST di salvataggio con validazione server-side (Pydantic), requisito Descrizione attività vincolato a `requires_description`, messaggi di esito. Persistenza su `effort_entries`.

## Rischi / punti aperti
- Tema dark/light rimandato a Fase 9.
- Migrazioni schema: `CREATE TABLE IF NOT EXISTS` / seed idempotente fino a Fase 9; poiché `code` è stato rimosso dopo la prima creazione, il DB va rigenerato se cambia schema (nessun ALTER automatico gestisce la rimozione colonna). Da valutare `ALTER TABLE` controllato o Alembic se cresce la complessità.
- `user_id` nullable senza FK in `effort_entries`, valorizzato in Fase 11.
- POST "method not allowed" al submit del form: atteso, sarà implementato in Fase 5.
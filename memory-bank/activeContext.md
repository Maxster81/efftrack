# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 6 ✅ (2026-07-31).
- **Fase in corso**: nessuna. In attesa di task per la Fase 7.
- **Stato**: idle, pronto per nuovo task. Merge autorizzato su `main` (2026-07-31).
- **Versione corrente**: `0.8.0` (tag `v0.8.0` annotato su `develop`).
- **Roadmap estesa**: aggiunte Fase 4b (sidebar hamburger), Fase 5b (copia su settimana), Fase 12 (Admin), Fase 13 (Manager); hardening slitta a Fase 14. Vedi `progress.md`/`projectbrief.md`.
- **Nota**: la tabella `effort_entries` ha la colonna `user_text` (String 128 nullable). Contiene dati reali (106 record: 100 fixture gen-lug 2026 + 6 preesistenti). Merge su `main` autorizzato dall'utente.
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

## Modifiche di Fase 4b (sidebar navigazione con hamburger menu)
- **`app/templates/base.html`**: pulsante hamburger (SVG) nell'header a sinistra del titolo (`#nav-toggle`, `aria-controls="app-sidebar"`); sidebar `<nav id="app-sidebar">` con header "Menu" + pulsante ✕ (`#sidebar-close`) e `<ul class="sidebar__menu">` vuoto (commento Jinja2 per voci in base al ruolo nelle Fasi 12-13); overlay `#sidebar-overlay`; `nav.js` incluso globalmente con `defer` prima di `</body>`.
- **`app/static/nav.js`** (NUOVO): toggle sidebar via hamburger (toggle), ✕ (close), click overlay (close) e tasto ESC (close); aggiorna `aria-expanded`/`aria-label`. Vanilla JS, nessuna dipendenza.
- **`app/static/style.css`**: regole per hamburger, overlay (z-index 40), sidebar fissa da sinistra (260px, max 85vw, z-index 50, transizione slide, `is-open`), header navy, close button, voci menu hover. Responsive (mobile incluso), basate sulle variabili CSS esistenti.

## Verifiche Fase 4b (curl su 0.0.0.0:8000 + browser)
- Struttura: hamburger + `aria-controls`, sidebar (`#app-sidebar`, `sidebar__header`, `sidebar__close`, `sidebar__menu`), overlay presenti. `form.js` e `nav.js` entrambi prima di `</body>`. `/static/nav.js` 200 text/javascript, `/static/style.css` 200, `/health` 200 `db:ok`.
- **Verifica utente (browser)**: apertura/chiusura sidebar funzionante (hamburger, ✕, overlay, ESC).

## Modifiche di Fase 5 (salvataggio record)
- **`app/schemas/effort.py`** (NUOVO): `EffortEntryCreate` Pydantic — user non vuoto, date, FK>0, hours 0.25-24 multiplo 0.25, notes/description normalizzati da vuoto a None.
- **`app/routers/web.py`**: nuova `POST /` (`save_entry`) con `Annotated[EffortEntryCreate, Form()]` — valida, verifica `requires_description` dell'attività, salva `EffortEntry` e redirect 303. `GET /` gestisce `success`/`error` per i banner. Label fase "Fase 5 — Salvataggio record".
- **`app/models/effort_entry.py`**: aggiunta colonna `user_text` (String 128 nullable) per persistere il campo User pre-auth.
- **`app/templates/index.html`**: `action="/"` (POST reale), banner `.form-success` e banner errore descrizione.
- **`app/static/style.css`**: aggiunta `.form-success` (verde).

## Verifiche Fase 5 (curl end-to-end)
- POST valido (attività 1, no desc) → 303 `/?success=1`; record salvato con `user_text="Mario"` e `hours_spent=7.5`.
- POST attività 2 (desc obbligatoria) senza descrizione → 303 `/?error=descrizione`, nessun record.
- Banner: `?success=1` mostra `.form-success` + messaggio; `?error=descrizione` mostra errore; GET normale nessun banner.
- DB rigenerato con colonna `user_text`.

## Modifiche di Fase 5b (inserimento bulk "copia su settimana")
- **`app/routers/web.py`**: parametro `action` nel form (`single`/`week`), funzione `_save_week` (calcola il lunedì della settimana della data e crea 5 record lun→ven), fattorizzata `_save_single`. **Fix FastAPI**: `Annotated[EffortEntryCreate, Form()]` combinato con altri `Form()` causava 422 → campi form dichiarati singolarmente + costruzione del modello Pydantic dentro la funzione (validazione server-side completa). Aggiunto `error=validazione` con relativo banner.
- **`app/templates/index.html`**: pulsante "Copia su settimana" (`name="action" value="week"`) accanto a "Salva" (`value="single"`); banner `validazione`.
- **`app/static/style.css`**: classe `.btn-secondary` (outline navy) + gap in `.form-actions`.

## Verifiche Fase 5b (curl end-to-end + browser)
- POST `action=week` con data 31/07/2026 → 303 `/?success=1`; creati 5 record lun 27→ven 31 (user 'Bulk', 8h, notes 'batch').
- POST `action=week` con attività Supporto Specialistico senza descrizione → 303 `/?error=descrizione`, 0 record.
- **Verifica utente (browser)**: "Copia su settimana" → banner verde; confermato nel DB 5 record settimana (user Metro, 8h, lun 06→ven 10/07/2026).

## Modifiche di Fase 6 (elenco record con filtro mese/anno)
- **Fixture**: generati 100 record di test (gen→lug 2026), user fittizi variati (Giulio/Anna/Luca/Sara/Marco/Elena), clienti/attività alternati, ore step 0.25, descrizione per Supporto. Totale DB 106.
- **`app/routers/web.py`**: `GET /` calcola mesi distinti (`SELECT DISTINCT strftime('%Y-%m', work_date)`), carica record con eager-load, filtra con `?month=YYYY-MM`, formatta nomi mesi in italiano (lista `_MESI_ITALIANI`). Label "Fase 6 — Elenco record con filtro mese/anno".
- **`app/templates/index.html`**: dropdown filtro (form GET, auto-submit `onchange`), tabella popolata (colonna Utente), contatore reale.
- **`app/static/style.css`**: stile `.filter-bar`.

## Verifiche Fase 6 (curl + browser + test)
- `GET /` → 200, 106 righe; dropdown con 7 opzioni mese; `?month=2026-01` → 11 righe. Test 6 OK.
- **Verifica utente (browser)**: filtro mese/anno funzionante.

## Prossima fase (Fase 7)
- **Selezione record e update**: click su riga → form precompilato → update. Sostituirà l'inserimento con l'aggiornamento del record selezionato. Il pulsante "Salva" gestirà sia insert che update (come da productContext).

## Fasi successive (dopo 4b)
- **Fase 5 — Salvataggio record**: POST di salvataggio con validazione server-side (Pydantic), requisito Descrizione attività vincolato a `requires_description`, messaggi di esito. Persistenza su `effort_entries`.
- **Fase 5b — Inserimento bulk "copia su settimana"**: pulsante che crea record per lunedì→venerdì della settimana corrente con i valori del form corrente.
- **Fasi 6–9**: invariati (elenco, update, export, refactoring).
- **Fasi 10–11**: auth locale, multiutente/segregazione.
- **Fase 12 — Admin**: tabella `roles`, CRUD utenti + assegnazione ruoli, CRUD lookup, sezione `/admin`.
- **Fase 13 — Manager**: vista/export dei record del proprio gruppo, senza gestione lookup/utenti.
- **Fase 14 — Hardening**: ex Fase 12.

## Rischi / punti aperti
- Tema dark/light rimandato a Fase 9.
- Migrazioni schema: `CREATE TABLE IF NOT EXISTS` / seed idempotente fino a Fase 9; poiché `code` è stato rimosso dopo la prima creazione, il DB va rigenerato se cambia schema (nessun ALTER automatico gestisce la rimozione colonna). Da valutare `ALTER TABLE` controllato o Alembic se cresce la complessità.
- `user_id` nullable senza FK in `effort_entries`, valorizzato in Fase 11.
- POST "method not allowed" al submit del form: atteso, sarà implementato in Fase 5.
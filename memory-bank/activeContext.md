# Active Context — Effort Tracking

## Stato corrente
- **Ultima sottofase completata**: Fase 13a ✅ (2026-08-03) — funzionalità admin (disabilita utente + assegnazione gruppo).
- **Fase in corso**: nessuna. Prossima: Fase 13b (sicurezza e robustezza).
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.19.0`.
- **Scomposizione Fase 12**: completata integralmente (12a-12d). Hardening = Fase 13, ora riorganizzata.
- **Scomposizione Fase 13 (riorganizzata 2026-08-03)**: 13a (ex 13b, funzionalità admin: Issue K+L, S8 ✅), 13b (ex 13c, sicurezza: 404/500, ore 1-12, XSS, headers + S4 filtro anno+mese), 13c (ex 13d, test+produzione), 13d (ex 13a, fix stilistici/UX, rimandata perché richiede screenshot).
- **DB di sviluppo**: rigenerato con dataset multi-gruppo (Fase 12c). 2 gruppi (SOC, NOC), 6 utenti di test con ~20 record ciascuno, password `test`. Admin resta utente di sola gestione (group_id NULL).
- **Roadmap estesa**: aggiunte Fase 4b (sidebar hamburger), Fase 5b (copia su settimana), Fase 12 (Admin), Fase 13 (Manager); hardening slitta a Fase 14. La Fase 9 è stata **sdoppiata** su richiesta utente: **Fase 9** (refactoring, logging, .env, systemd — solo backend) e **Fase 9b** (toggle dark/light, aggiornamento dipendenze — solo frontend). Vedi `progress.md`/`projectbrief.md`.
- **Nota**: la tabella `effort_entries` **non ha più** la colonna `user_text` (rimossa in Fase 11). `user_id` è ora una FK verso `users.id` (ON DELETE SET NULL). DB di sviluppo (Fase 12c): 2 gruppi (SOC, NOC), 6 utenti di test + admin, 120 record. **Merge su `main` autorizzato in Fase 9 (due volte) e Fase 9b**: `main` include le fasi 1–9b, v0.12.0. Le fasi 10+ sono solo su `develop`.
- **Nota ambiente**: sviluppo su **Ubuntu in WSL** (Python 3.12.3, pip 24.0). Venv ricreato in questa macchina. Dipendenze: fastapi 0.141.1, uvicorn 0.52.1, sqlalchemy 2.0.51, pydantic 2.13.4 (pydantic-core 2.46.4, pin compatibile), jinja2 3.1.6, python-multipart 0.0.32, python-dotenv 1.2.2, pytest 9.1.1 (in dev, non in produzione). `pydantic-core` 2.47.0 NON è adottato: incompatibile con pydantic 2.13.4.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: toggle dark/light **funzionante** dalla Fase 9b (due modalità dark/light, preferenza in localStorage `theme-preference`, default light).
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Bump confermato a `0.4.0` per la Fase 4 (MINOR: nuova funzionalità di persistenza).
- **Campo User**: scrivibile nelle fasi pre-auth (intenzionale). In Fase 10 diventerà read-only derivato dalla sessione.
- **Etichetta descrizione**: "Descrizione attività" per coerenza col vecchio tool. **Note** opzionale; **Descrizione attività** obbligatoria solo quando l'attività richiede descrizione (`requires_description`).
- **Modello dati lookup**: non servono `code` e `name`, basta il `name` (con UNIQUE). Rimossa la colonna `code` in Fase 4 su decisione utente. I dropdown mostrano solo `name`.
- **Data default**: il campo Data del form è pre-popolato con `date.today()` lato server (`today` nel context).
- **Bind server**: in sviluppo bind su `0.0.0.0` (accessibile da browser Windows via WSL).
- **Test automatici**: pytest da Fase 9 in poi, con SQLite in-memory isolato. Dipendenza di sviluppo separata in `requirements-dev.txt`.
- **Logging**: `app/core/logging_config.py` con `setup_logging()` chiamato nel lifespan; livello da `EFFORT_TRACKING_LOG_LEVEL` (default INFO); formato leggibile console/journald.
- **Configurazione**: `app/config.py` carica `.env` via `python-dotenv` (`load_dotenv`); `DATA_DIR` centralizzato. Il `.env` reale NON è committato (in `.gitignore`); template in `.env.example`.

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

## Modifiche di Fase 7 (selezione record e update/delete)
- **`app/routers/web.py`**:
  - Campi del form (`user`, `date`, `client_id`, `group_id`, `activity_id`, `hours`, `notes`, `description`) resi **opzionali** nella firma della route; validazione completa demandata a `EffortEntryCreate` (Pydantic) dentro il try. Necessario perché `action=delete` richiede solo `record_id` (prima FastAPI dava 422 sui campi obbligatori).
  - `POST /` accetta `record_id` (hidden field nel form). Con `record_id` valorizzato e `action=single`, `_save_single` **aggiorna** il record esistente → redirect `/?success=2`. Con `action=delete`, `_delete_entry(record_id, db)` elimina il record → `/?success=3`; se id assente/inesistente → `/?error=validazione`.
  - `action=week` è bloccato in modalità modifica (`?error=validazione`) — la copia bulk vale solo in inserimento.
  - Banner `success=1` (inserito), `success=2` (aggiornato), `success=3` (eliminato). Label "Fase 7 — Selezione record e update".
- **`app/templates/index.html`**: input hidden `#record-id` (dentro il `<form>`, fixato dopo bug iniziale in cui era fuori e non veniva inviato); righe tabella cliccabili con `role="button" tabindex="0"` e `data-*` per popolare il form; titolo dinamico (Nuova/Modifica registrazione); pulsanti "Annulla modifica" (#edit-cancel) e "Elimina registrazione" (#edit-delete, `is-hidden` di default) + hide di #week-action in modifica.
- **`app/static/row-select.js`** (NUOVO): click riga/tastiera (Enter/Spazio) → popola form + modalità modifica; "Annulla modifica" resetta; `window.confirm` prima della cancellazione; espone `EffortTrack.clearEdit`/`isEditMode`.
- **`app/static/form.js`**: espone `EffortTrack.syncDescriptionVisibility`; salta la validazione client-side quando il submit viene da `#edit-delete`.
- **`app/static/style.css`**: `.is-selected` (riga evidenziata), `:focus-visible`, `.btn-tertiary` (annulla), `.btn-danger` (elimina rosso), `.card-title__edit`.
- **`tests/test_models.py`**: nuovo test `test_update_entry` (7 test totali OK).
- **Bug fix**: input hidden `record_id` era fuori dal `<form>` → spostato dentro (i POST senza di esso creavano sempre nuovi record).

## Verifiche Fase 7 (test + curl end-to-end)
- **Test**: 7/7 OK.
- Update: POST `record_id=106` → 303 `/?success=2`, record aggiornato (nessun duplicato).
- Delete: POST `action=delete` → 303 `/?success=3`; record eliminato dal DB (verificato: i record del 31/07/2026 eliminati dall'utente non risultano più in `effort_entries`).
- Retrocompatibilità: insert senza `record_id` → `/?success=1`; banner success=2 e success=3 renderizzati.
- Static: row-select.js/form.js/style.css 200.

## Modifiche di Fase 8 (export CSV)
- **`app/routers/web.py`**:
  - Nuova route `GET /export` (`export_csv`, nome `export_csv`): accetta `month` opzionale (`?month=YYYY-MM`), carica i record con eager-load e ordina per data crescente, filtra per mese se presente.
  - Nuova funzione `_build_csv(records)` separata dall'endpoint per testabilità: genera il contenuto CSV con BOM UTF-8 (`\ufeff`), header `_CSV_HEADER` (Data, Cliente, Gruppo, Attività, Utente, Ore, Note, Descrizione attività), date in formato `DD/MM/YYYY`.
  - `StreamingResponse` con `media_type="text/csv; charset=utf-8"` e `Content-Disposition: attachment; filename="effort_YYYY-MM.csv"` (o `effort_tutti.csv` senza filtro).
  - Costante `_CSV_HEADER` aggiunta in cima al modulo.
- **`app/templates/index.html`**: nella `filter-bar`, aggiunto `<span class="filter-bar__spacer">` (flessibile) e link `<a class="filter-bar__export" role="button">Esporta CSV</a>` all'estrema destra; href `/export` con `?month={{ selected_month }}` se un mese è selezionato. Commento intestazione aggiornato a "Fase 8 — Export CSV".
- **`app/static/style.css`**: classi `.filter-bar__spacer` (flex: 1 1 auto, spinge il pulsante a destra) e `.filter-bar__export` (stile outline navy coerente con `.btn-secondary`, hover con sfondo accent, focus-visible).
- **`tests/test_models.py`**: nuova classe `TestExportCsv` con test `test_build_csv_header_and_row` che verifica BOM, header e riga formattata (date DD/MM/YYYY, campi presenti). Totale 8 test.
- **Label fase**: aggiornata a "Fase 8 — Export CSV".

## Verifiche Fase 8 (test + curl)
- **Test**: 8/8 OK.
- `GET /export` → 200, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="effort_tutti.csv"`, BOM presente, header corretto, dati presenti.
- `GET /export?month=2026-01` → 200, `filename="effort_2026-01.csv"`, 11 record + header.
- `GET /` → contiene label "Fase 8 — Export CSV" e link "Esporta CSV".
- **Verifica utente (browser)**: pulsante "Esporta CSV" a destra del dropdown mese; download del CSV; il download rispetta il filtro mese selezionato.

## Modifiche di Fase 9 (refactoring, logging, env, systemd)
- **`app/config.py`**: aggiunto `load_dotenv()` (carica `.env` se presente); nuova costante `DATA_DIR` (centralizza `BASE_DIR / "data"`); nuove costanti logging `LOG_LEVEL` (da env `EFFORT_TRACKING_LOG_LEVEL`, default INFO) e `LOG_FORMAT`; `APP_VERSION` → `0.11.0`.
- **`app/core/logging_config.py`** (NUOVO): `setup_logging()` idempotente — configura handler StreamHandler con formato `%(asctime)s %(levelname)s [%(name)s] %(message)s` e livello da config.
- **`app/main.py`**: nel `lifespan` chiama `setup_logging()` e aggiunge log di avvio/arresto dell'app, verifica schema e lookup; usa `DATA_DIR` centralizzato.
- **`app/core/seed.py`**: nuovo log `info` quando il seed popola le lookup, `debug` quando sono già popolate.
- **`app/routers/web.py`**: introdotto `logger`; log `warning` su validazione fallita/descrizione mancante/id inesistente, `info` su creazione/aggiornamento/eliminazione record, copia settimanale ed export CSV; log `error` su health check degradato. Label fase "Fase 9 — Refactoring, logging, env".
- **`requirements.txt`**: aggiunto `python-dotenv>=1.0.0`.
- **`requirements-dev.txt`** (NUOVO): include `requirements.txt` + `pytest>=8.0.0` (dipendenza solo di sviluppo).
- **`.env.example`**: aggiunto `EFFORT_TRACKING_LOG_LEVEL=INFO`.
- **`.env`** (REALE, NON committato): creato da `.env.example` + `EFFORT_TRACKING_LOG_LEVEL=INFO`.
- **`systemd/efftrack.service`**: documentazione estesa — elenco esplicito delle variabili in `/etc/efftrack.env`, nota che in produzione NON si usa il `.env` locale (variabili solo da EnvironmentFile), nota log su journald (`journalctl -u efftrack -f`).
- **`VERSION`**: `0.10.0` → `0.11.0` (MINOR: funzionalità di configurazione/logging retrocompatibili).

## Verifiche Fase 9 (test + curl + avvio)
- **Test**: 8/8 OK (pytest installato come dev dep; ripulita nota precedente su `unittest`).
- Avvio uvicorn: log di startup/shutdown corretti (`Avvio Effort Tracking v0.11.0`, `Schema database verificato`, `Avvio completato`, `Arresto`).
- `GET /health` → 200 `{"app":"Effort Tracking","version":"0.11.0","status":"ok","db":"ok"}`.
- `GET /` → 200; `GET /export` → 200 con log `Export CSV generato (record=110, mese=tutti)`.

## Modifiche di Fase 9b (toggle dark/light + dipendenze)
- **`app/static/theme.js`** (NUOVO): toggle bistabile dark/light (nessun rilevamento di sistema). Salva in `localStorage["theme-preference"]`, legge al caricamento, applica `data-theme="dark"` su `<html>`, aggiorna icona/label del pulsante. Default light.
- **`app/templates/base.html`**: pulsante `.app-header__theme-toggle` (#theme-toggle) con icona ☀️/🌙 dentro `.app-header__actions` (tra fase e icone utente); script inline anti-FOUC nel `<head>` che applica il tema salvato **prima** del rendering; `theme.js` incluso con `defer` prima di `</body>`.
- **`app/static/style.css`**: blocco `[data-theme="light"]` esplicito (replica :root per coerenza a tre-blocco: :root, light, dark); stile `.app-header__theme-toggle` e `.app-header__theme-icon` coerenti con `.app-header__user`; commento dark aggiornato.
- **`app/routers/web.py`**: label fase → "Fase 9b — Toggle dark/light".
- **Dipendenze**: `uvicorn` 0.52.0 → 0.52.1 (PATCH stabilità). `pydantic-core` tentativo di 2.47.0 **scartato e ripristinato a 2.46.4** per compatibilità con pydantic 2.13.4 (`pip check` OK).
- **`VERSION`**: `0.11.0` → `0.12.0` (MINOR: nuova funzionalità toggle tema).

## Verifiche Fase 9b (test + curl + avvio)
- **Test**: 8/8 OK (pytest).
- `GET /health` → 200 `v0.11.0` (la versione nel payload è quella di config; aggiornamento a 0.12.0 dopo bump).
- `GET /` → label "Fase 9b — Toggle dark/light"; elemento `id="theme-toggle"` presente; script anti-FOUC (`theme-preference`) presente.
- `/static/theme.js` → 200 `text/javascript`; `/static/style.css` → 200 `text/css`.
- **Verifica utente (browser)**: click toggle alterna dark/light, preferenza persistita in localStorage, nessun flash al reload.

## Modifiche di Fase 10 (autenticazione locale)
- **`app/models/user.py`** (NUOVO): tabella `users` (id, username UNIQUE, password_hash, role).
- **`app/models/__init__.py`**: import `User`.
- **`app/core/seed.py`**: `seed_admin_user(db)` idempotente — utente admin creato se tabella users vuota; username/password da config.
- **`app/config.py`**: `AUTH_ENABLED` (default true), `ADMIN_USERNAME`/`ADMIN_PASSWORD` (default admin/admin) da env var.
- **`app/dependencies.py`** (NUOVO): `get_current_user` — legge `request.session["user_id"]`, carica l'utente; session DB non chiusa (dependency pura, evita autoclose).
- **`app/routers/auth.py`** (NUOVO): login/logout con sessione; verifiche bcrypt; `Response` come return type di POST (evita errore FastAPI con Union di risposte).
- **`app/main.py`**: `SessionMiddleware` con `SECRET_KEY`; `seed_admin_user` nel lifespan; include router auth.
- **`app/routers/web.py`**: `_require_auth` + `Depends(get_current_user)` su `/`, `/export`, POST; campo User forzato allo username sessione; context `current_username`/`auth_enabled`; label "Fase 10 — Autenticazione"; `/health` pubblico.
- **`app/templates/login.html`** (NUOVO): form di login.
- **`app/templates/base.html`**: area utente (username + Esci) o link Accedi.
- **`app/templates/index.html`**: campo User `readonly` con `current_username` quando auth.
- **`app/static/form.js`**: validazione User saltata se readonly.
- **`app/static/style.css`**: `.login-card`, `.login-form`, `.app-header__user-auth`, `.app-header__logout/.login`.
- **`requirements.txt`**: `passlib[bcrypt]>=1.7`, `bcrypt<4.1`, `itsdangerous>=2.0.0`.
- **`.env.example` / `.env`**: `EFFORT_TRACKING_AUTH_ENABLED`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.
- **`tests/test_models.py`**: 3 nuovi test admin (creazione, hash valido, idempotenza) + tabella users nello schema. Totale 11 test.
- **`VERSION`**: `0.12.0` → `0.13.0` (MINOR).

## Verifiche Fase 10 (test + curl + avvio)
- **Test**: 11/11 OK; `pip check` pulito.
- Log avvio: `Utente admin creato: username=admin`.
- Curl: GET / senza sessione → 303 /login; GET /export senza sessione → 303 /login; POST /login errato → "Credenziali non valide"; POST /login admin/admin → 303 /; GET / loggato → 200 (username admin + campo User readonly); GET /logout → 303 /login; GET / dopo logout → 303 /login.
- **Verifica utente (browser)**: login/logout, campo User bloccato e precompilato.

## Modifiche di Fase 11 (multiutente e segregazione)
- **`app/models/effort_entry.py`**: `user_id` ora FK verso `users.id` (ON DELETE SET NULL) + indice; rimossa colonna `user_text`; aggiunta relazione `user`.
- **`app/core/migrations.py`** (NUOVO): `run_schema_migrations` idempotente — ricrea `effort_entries` se presente `user_text` (dati di sviluppo eliminati). Eseguita prima di `create_all` nel lifespan.
- **`app/core/seed.py`**: `seed_test_users` (mario/giulia/luca, pass `test`) e `seed_test_records` (~20 record/utente). Idempotenti.
- **`app/routers/web.py`**: `_is_admin`/`_filter_by_user`; `user_id` valorizzato su insert; **regola aziendale**: update/delete bloccati per record altrui per TUTTI (admin inclusi); `_build_csv` usa username via JOIN; fix `_with_month` (ignora `"None"`).
- **`app/templates/index.html`**: colonna Utente solo per admin; fix campo hidden `month` (`selected_month or ''`).
- **`tests/test_models.py`**: 22 test OK (schema, seed, segregazione, regola aziendale, export).

## Fasi successive (scomposizione Fase 13 riorganizzata 2026-08-03)
L'ordine delle sottofasi è stato cambiato (13d rimandata per ultima perché richiede screenshot non supportati dal modello attuale).
- **Fase 13a — Funzionalità admin** ✅ completata (2026-08-03): colonna `disabled` su User (login bloccato, record intatti) + migrazione; endpoint toggle disabilita/abilita; assegnazione `group_id` in creazione e modifica utente (Issue K + Issue L rivista); avvisi ed eliminazione solo per utenti disabilitati (Suggestion 8). Suggestion 4 (filtro anno+mese) rinviata a 13b.
- **Fase 13b — Sicurezza e robustezza** (da fare): pagine errore 404/500, validazione ore 1-12 + vincoli Supporto Specialistico, verifica anti-XSS, security headers HTTP, **Suggestion 4 (filtro anno+mese)**.
- **Fase 13c — Test, doc e preparazione produzione** (da fare): test funzionali con pytest, eventuale riposizionamento Export, review systemd, README deploy, note PostgreSQL.
- **Fase 13d — Fix stilistici e UX** (rinviata): Issue I (stile admin utenti), Issue J (stile admin lookup), Suggestion 1 (hamburger login), Suggestion 2 (step ore 0.5), Suggestion 5 (evidenzia record). Richiede screenshot.

## Rischi / punti aperti
- **`memory-bank/Issue-Suggestion.md`** traccia issue minori e suggerimenti raccolti dai test utente (priorità molto bassa). Attualmente: **Suggestion 1** (hamburger in login), **Suggestion 2** (incremento ore), **Suggestion 3** (menu su immagine utente), **Suggestion 4** (filtro anno+mese), **Suggestion 5** (evidenzia record modificato), **Suggestion 6** (checkbox ferie). Nessuna issue aperta (Issue 1 risolta in 0.13.1).
- Password admin di default `admin/admin`: va cambiata subito in produzione via env var (Sicurezza Fase 14).
- La sessione HTTP firmata richiede `SECRET_KEY` robusta in produzione (placeholder in sviluppo).
- `pydantic-core` pinnato a 2.46.4 per compatibilità con pydantic 2.13.4; quando pydantic sarà aggiornato, andrà aggiornato insieme.
- Migrazioni schema: `run_schema_migrations` gestisce le modifiche note (es. rimozione `user_text`); per cambi non gestiti (es. rimozione `code`) va rigenerato il DB. Alembic da valutare se la complessità cresce.
- `user_id` FK verso `users.id` dalla Fase 11; nessuno modifica/elimina record altrui (regola aziendale).
- La cancellazione è **permanente** e senza soft-delete/audit (da valutare in Fase 14/hardening).
- Il `.env` reale in produzione è sostituito dal `/etc/efftrack.env` di systemd (documentato nel template).

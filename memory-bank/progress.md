# Progress — Effort Tracking

## Stato globale
- **Ultima fase completata**: Fase 9 ✅ completata il 2026-08-03 (refactoring, logging, .env, systemd).
- **Fase in corso**: Fase 9b (toggle dark/light + aggiornamento dipendenze) — non avviata.
- **Stato**: in pausa tra la Fase 9 e la 9b.
- **Versione corrente**: `0.11.0` (tag `v0.11.0` annotato su `develop`).
- **Roadmap estesa**: aggiunte Fase 4b (sidebar hamburger), Fase 5b (copia su settimana), Fase 12 (Admin), Fase 13 (Manager); l'hardening passa da 12 a 14. La Fase 9 è stata **sdoppiata** su richiesta utente in **Fase 9** (backend) e **Fase 9b** (frontend toggle dark/light + dipendenze).

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

### Fase 4b — Sidebar navigazione con hamburger menu
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: barra laterale (drawer) con pulsante hamburger nell'header, visibile in tutto il web server e per tutti gli utenti. Contenitore vuoto per ora; le voci di menu verranno popolate in base al ruolo utente a partire dalle Fasi 12–13 (Admin/Manager/User).
- **Cosa è stato fatto**:
  - **`base.html`**: pulsante hamburger (SVG) nell'header a sinistra; sidebar `<nav id="app-sidebar">` con header "Menu" + ✕; overlay `#sidebar-overlay`; `nav.js` incluso globalmente con `defer`.
  - **`app/static/nav.js`** (nuovo): toggle sidebar via hamburger, ✕, click overlay e tasto ESC; aggiorna `aria-expanded`/`aria-label`. Vanilla JS.
  - **`app/static/style.css`**: stili hamburger, overlay (z-index 40), sidebar fissa da sinistra (260px, max 85vw, z-index 50, transizione slide), header navy, voci menu hover. Responsive.
  - Verifiche curl: hamburger + `aria-controls`, sidebar + overlay presenti, `nav.js` e `style.css` serviti (200), `form.js` e `nav.js` prima di `</body>`, health ok.
  - Verifica utente (browser): apertura/chiusura sidebar funzionante.
- **Versioning**: bump `VERSION` `0.4.0` → `0.5.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.5.0`. Niente `main`.
- **Commit**: `feat(ui): phase 4b sidebar navigation with hamburger menu`.

### Fase 5 — Salvataggio record
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: POST di salvataggio con validazione server-side (Pydantic) e messaggi di esito; requisito Descrizione attività vincolato a `requires_description`.
- **Cosa è stato fatto**:
  - **`app/schemas/effort.py`** (nuovo): `EffortEntryCreate` Pydantic con validazione server-side (user non vuoto, date, FK > 0, hours 0.25-24 multipli di 0.25, notes/description normalizzati da vuoto a None).
  - **`app/routers/web.py`**: nuova `POST /` (`save_entry`) che valida il form (Form), verifica `requires_description` dell'attività, crea e salva `EffortEntry` e fa redirect 303 a `/?success=1` (o `/?error=descrizione`). `GET /` gestisce `success`/`error` per i banner. Label fase "Fase 5 — Salvataggio record".
  - **`app/models/effort_entry.py`**: aggiunta colonna `user_text` (String 128, nullable) per persistere il campo User del form pre-auth.
  - **`app/templates/index.html`**: `action="/"` sul form (POST reale), banner successo (`.form-success`) e banner errore descrizione.
  - **`app/static/style.css`**: aggiunta classe `.form-success` (banner verde).
  - Verifiche curl: POST valido → 303 `/?success=1` + record salvato (user_text persistito); POST attività con descrizione obbligatoria senza descrizione → 303 `/?error=descrizione` senza salvare; banner renderizzati correttamente.
- **Versioning**: bump `VERSION` `0.5.0` → `0.6.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.6.0`. Niente `main`.
- **Commit**: `feat(db): phase 5 save effort entry with server validation`.

### Fase 5b — Inserimento bulk "copia su settimana"
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: pulsante "Copia su settimana" accanto a Salva: prende i valori del form corrente (cliente, gruppo, attività, ore) e crea un record per ogni giorno feriale (lunedì→venerdì) della settimana corrente, con data corrispondente. Stessi valori, date diverse. Validazione server-side per ciascun record.
- **Cosa è stato fatto**:
  - **`app/routers/web.py`**: parametro `action` nel form (`single`/`week`); funzione `_save_week` che calcola il lunedì della settimana della data e crea 5 record lun→ven; fattorizzata `_save_single`. **Fix**: `Annotated[EffortEntryCreate, Form()]` con altri `Form()` causava 422 → dichiarati i campi form singolarmente e costruito il modello Pydantic dentro la funzione. Banner per `error=validazione`.
  - **`app/templates/index.html`**: pulsante "Copia su settimana" (`name="action" value="week"`) accanto a "Salva" (`value="single"`); banner errore validazione.
  - **`app/static/style.css`**: classe `.btn-secondary` (outline navy) + gap nelle `.form-actions`.
  - Verifiche curl: POST `action=week` con data 31/07/2026 → 303 `/?success=1`; creati 5 record lun 27→ven 31 ('Bulk', 8h, notes batch). POST `action=week` con attività Supporto Specialistico senza descrizione → 303 `/?error=descrizione`, 0 record.
  - **Verifica utente (browser)**: "Copia su settimana" → banner verde, 5 record settimana (user Metro, 8h) salvati nel DB.
- **Versioning**: bump `VERSION` `0.6.0` → `0.7.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.7.0`. Niente `main`.
- **Commit**: `feat(db): phase 5b bulk copy effort on week`.

### Fase 6 — Elenco record
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: tabella inferiore caricata dal DB, ordinata per data decrescente + filtro mese/anno tramite dropdown basato sui mesi distinti presenti nei record.
- **Cosa è stato fatto**:
  - **Fixture**: generati 100 record di test (gennaio→luglio 2026), user fittizi variati (Giulio/Anna/Luca/Sara/Marco/Elena), clienti/attività alternati, ore step 0.25, descrizione per Supporto Specialistico. Totale DB 106 record.
  - **`web.py`**: `GET /` calcola i mesi distinti (`SELECT DISTINCT strftime('%Y-%m', work_date)` desc), carica i record con eager-load delle relazioni, filtra con `?month=YYYY-MM`; nomi mesi formattati in italiano lato server. Label "Fase 6 — Elenco record con filtro mese/anno".
  - **`index.html`**: dropdown filtro (form GET auto-submit via `onchange`), tabella popolata con colonna "Utente", contatore record reale.
  - **`style.css`**: stile `.filter-bar`. Rimosso vecchio commento "Fase 2".
  - Verifiche: `GET /` 200 con 106 righe; dropdown con 7 opzioni mese; `?month=2026-01` → 11 righe; test 6 OK.
  - **Verifica utente (browser)**: filtro mese/anno funzionante.
- **Versioning**: bump `VERSION` `0.7.0` → `0.8.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.8.0`. Merge autorizzato su `main` dall'utente.
- **Commit**: `feat(ui): phase 6 records list with month filter`.

### Fase 7 — Selezione record e update/delete
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: click su riga → form precompilato → update/delete. Il pulsante "Salva" gestisce sia insert che update in base alla presenza di `record_id`.
- **Cosa è stato fatto**:
  - **`web.py`**: campi form opzionali nella firma della route (validazione demandata a Pydantic `EffortEntryCreate`); parametro `record_id` (hidden field) per distinguere insert (None) da update (valorizzato). `_save_single` ora aggiorna il record se esiste `record_id` → `/?success=2`. Nuova `action=delete` con `_delete_entry` → `/?success=3` (o `/?error=validazione` se id assente/inesistente). `action=week` bloccato in modifica. Banner per `success=1/2/3`. Label "Fase 7 — Selezione record e update".
  - **`index.html`**: input hidden `#record-id` dentro il form; righe tabella cliccabili (`role="button"`, `tabindex="0"`, `data-*` per popolare il form); titolo dinamico (Nuova/Modifica registrazione); pulsanti "Annulla modifica" e "Elimina registrazione" (visibili solo in modifica); hide di "Copia su settimana" in modifica.
  - **`row-select.js`** (nuovo): popolamento form al click riga/tastiera, modalità modifica, annulla, `window.confirm` prima della cancellazione, espone helper `EffortTrack`.
  - **`form.js`**: espone `syncDescriptionVisibility`; salta la validazione client-side su `#edit-delete`.
  - **`style.css`**: `.is-selected`, `:focus-visible`, `.btn-tertiary`, `.btn-danger`, `.card-title__edit`.
  - **`tests/test_models.py`**: nuovo test `test_update_entry`.
  - **Bug fix**: l'input hidden `record_id` era inizialmente fuori dal `<form>` (non inviato nella POST, con la creazione di record duplicati) → spostato dentro il form.
  - Verifiche: 7/7 test OK; update via curl (`record_id=106`) → `/?success=2` senza duplicati; delete via curl → `/?success=3` con rimozione dal DB; retrocompatibilità insert → `/?success=1`; banner success=2/3 renderizzati; eliminazione dal browser confermata nel DB (record 31/07/2026 rimossi da `effort_entries`).
- **Versioning**: bump `VERSION` `0.8.0` → `0.9.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.9.0`. Niente `main`.
- **Commit**: `feat(db): phase 7 record select, update and delete`.

### Fase 8 — Export CSV / XLSX
- **Stato**: ✅ completata il 2026-07-31.
- **Obiettivo**: export con filtri base.
- **Decisione utente**: export **sempre mensile**, pulsante a destra del dropdown mese (estremamente destra della card); formato **solo CSV** per ora (XLSX rimandato). Tutte le colonne della tabella.
- **Cosa è stato fatto**:
  - **`web.py`**: nuova route `GET /export` (`export_csv`) con filtro `?month=YYYY-MM`; funzione testabile `_build_csv(records)` (BOM UTF-8, header `_CSV_HEADER`, date DD/MM/YYYY); `StreamingResponse` con `Content-Disposition: attachment` e filename `effort_YYYY-MM.csv` / `effort_tutti.csv`. Label "Fase 8 — Export CSV".
  - **`index.html`**: nella `filter-bar`, `<span class="filter-bar__spacer">` + link `<a class="filter-bar__export" role="button">Esporta CSV</a>` all'estrema destra; href `/export` con `?month=` se mese selezionato.
  - **`style.css`**: classi `.filter-bar__spacer` (flex flexibile) e `.filter-bar__export` (outline navy, hover accent, focus-visible).
  - **`tests/test_models.py`**: classe `TestExportCsv` (BOM, header, riga formattata). Totale 8 test.
  - **Verifiche**: 8/8 test OK; `/export` 200 con `effort_tutti.csv` (BOM + header + dati); `/export?month=2026-01` 200 con `effort_2026-01.csv` (11 record + header); `/` contiene label e link "Esporta CSV". Verifica utente (browser) positiva.
- **Versioning**: bump `VERSION` `0.9.0` → `0.10.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.10.0`. Niente `main`.
- **Commit**: `feat(db): phase 8 csv export with month filter`.

### Fase 9 — Refactoring, logging, env, systemd
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: refactoring, logging strutturato, `.env` operativo, validazione systemd. (Il toggle dark/light è slittato alla nuova **Fase 9b**.)
- **Cosa è stato fatto**:
  - **`app/config.py`**: `load_dotenv()` (carica `.env`); nuova `DATA_DIR`; costanti logging `LOG_LEVEL`/`LOG_FORMAT`; `APP_VERSION` → `0.11.0`.
  - **`app/core/logging_config.py`** (nuovo): `setup_logging()` idempotente (StreamHandler, formato asctime/livello/logger/messaggio, livello da env).
  - **`app/main.py`**: `setup_logging()` nel lifespan; log di avvio/arresto, schema verificato; usa `DATA_DIR`.
  - **`app/core/seed.py`**: log `info` su seed eseguito, `debug` se già popolato.
  - **`app/routers/web.py`**: `logger`; warning su validazione/descrizione/id mancanti; info su create/update/delete/week/export; error su health degradato. Label "Fase 9 — Refactoring, logging, env".
  - **`requirements.txt`**: `python-dotenv>=1.0.0`.
  - **`requirements-dev.txt`** (nuovo): `pytest>=8.0.0` (solo dev).
  - **`.env.example`**: aggiunto `EFFORT_TRACKING_LOG_LEVEL=INFO`.
  - **`.env`** (reale, non committato): creato da template + log level.
  - **`systemd/efftrack.service`**: doc estesa (variabili env, niente `.env` in produzione, log su journald).
  - **`VERSION`**: `0.10.0` → `0.11.0` (MINOR).
  - **Merge su `main` autorizzato dall'utente** prima di iniziare la fase: `main` include fasi 7–9 (v0.11.0).
- **Verifiche**: 8/8 test OK (pytest); avvio uvicorn con log startup/shutdown corretti; `/health` 200 v0.11.0 `db:ok`; `/` 200; `/export` 200 (log 110 record).
- **Versioning**: bump `VERSION` `0.10.0` → `0.11.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.11.0`. Niente `main` (merge già fatto prima).
- **Commit**: previsto `feat(core): phase 9 logging, dotenv, systemd`.

### Fase 9b — Toggle dark/light + aggiornamento dipendenze
- **Stato**: non iniziata.
- **Obiettivo**: toggle dark/light funzionante nell'header; aggiornamento dipendenze (`pip list --outdated`).

### Fase 10 — Autenticazione locale
- **Stato**: non iniziata.
- **Obiettivo**: login user/password con password hashate e sessione.

### Fase 11 — Multiutente e segregazione
- **Stato**: non iniziata.
- **Obiettivo**: `user_id` valorizzato, segregazione dei dati, predisposizione ruoli.

### Fase 12 — Gestione ruoli e amministrazione (Admin)
- **Stato**: non iniziata.
- **Obiettivo**: tabella `roles` (admin/manager/user) e FK su `users`. L'Admin può: CRUD utenti e assegnazione ruoli; CRUD lookup (clienti, gruppi, attività). Sezione `/admin` visibile solo al ruolo admin. I dropdown non saranno più statici dopo il seed.

### Fase 13 — Export manager e gestione gruppo (Manager)
- **Stato**: non iniziata.
- **Obiettivo**: il Manager vede i record di tutti gli utenti del proprio gruppo e può esportarne i dati (CSV/XLSX), ma NON modifica lookup né gestisce utenti (quello è admin). Serve associazione utente→gruppo.

### Fase 14 — Hardening produzione
- **Stato**: non iniziata.
- **Obiettivo**: controllo validazioni, gestione errori, backup SQLite, note migrazione PostgreSQL.

## Decisioni di versioning
- **Strategia**: SemVer. Versione tracciata solo nel file `VERSION` (unico servizio, niente repliche in `__init__.py`).
- **Bump ad ogni commit funzionale**, tag annotato `vX.Y.Z` sullo stesso commit.
- **MAJOR** = breaking changes architetturali.
- **MINOR** = nuove funzionalità retrocompatibili.
- **PATCH** = bug fix, refactoring interno, miglioramenti UI.

## Cose note / limitazioni accettate
- Tema dark/light solo come struttura CSS variabili fino a Fase 9b (toggle non ancora implementato).
- Migrazioni schema con `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE` controllato; Alembic proposto se la complessità cresce.
- `user_id` nullable in `effort_entries` dal suo inserimento, valorizzato in Fase 11.
- La cancellazione è **permanente** e senza soft-delete/audit (da valutare in Fase 14/hardening).
- I campi del form sono opzionali nella firma della route `POST /`: la validazione obbligatoria avviene comunque server-side via `EffortEntryCreate` per le azioni che creano/aggiornano record.
- DB di sviluppo: per le prove la fixture è variata (ora 110 record).
- Configurazione: il `.env` locale è per lo sviluppo; in produzione systemd legge `/etc/efftrack.env` (EnvironmentFile). Livello log controllato da `EFFORT_TRACKING_LOG_LEVEL`.

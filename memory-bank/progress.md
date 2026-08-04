# Progress — Effort Tracking

## Stato globale
- **Ultimo task completato**: Restyle grafico header ✅ completato il 2026-08-04 — header a griglia full-width (`1fr auto 1fr`): hamburger all'estrema sinistra della pagina, titolo "EFFORT TRACKING" centrato nella barra, azioni (fase, toggle tema, menù utente) allineate a destra. Ingranditi hamburger (45px) e menù utente/icona utente (+25%).
- **Fase in corso**: nessuna. Prossima: Fase 13d (hardening e sicurezza).
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.23.2` (bump con commit restyle).
- **Roadmap estesa**: aggiunte Fase 4b (sidebar hamburger), Fase 5b (copia su settimana), Fase 12 (Admin, scomposta in 12a/12b/12c/12d); l'hardening passa a **Fase 13**, ora scomposta in 13a-13d. La Fase 9 è stata **sdoppiata** su richiesta utente in **Fase 9** (backend) e **Fase 9b** (frontend toggle dark/light + dipendenze).
- **Scomposizione Fase 12 (riorganizzata 2026-08-03)**: approccio "dal basso verso l'alto". 12a-12d ✅ completate. Hardening = Fase 13.
- **Scomposizione Fase 13 (riorganizzata 2026-08-03)**: 13a (funzionalità admin ✅), 13b (sicurezza ✅), 13c (fix stilistici e UX ✅, 2026-08-03), 13d (hardening sicurezza — da fare), 14 (produzione/documentazione — SEMPRE ultima, da fare).
- **DB di sviluppo**: rigenerato in Fase 12c con dataset multi-gruppo (2 gruppi SOC/NOC, 6 utenti di test con ~20 record ciascuno).

> **⚠️ NOTA OPERATIVA — Issue e Suggerimenti:** le issue e i suggerimenti raccolti dai test utente sono tracciati **esclusivamente** in `memory-bank/Issue-Suggestion.md`. Prima di iniziare **ogni fase**, consultare quel file. Quando una voce viene risolta, va **rimossa** da lì nello stesso commit che la risolve. Prima di riportare in questo file eventuali checklist "da fare", verificare se esistono già in `Issue-Suggestion.md` per evitare duplicati o disallineamenti.

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
  - **Merge su `main` autorizzato dall'utente due volte**: prima di iniziare la fase (baseline stabile Fase 8) e a fine fase dopo conferma esplicita.
- **Verifiche**: 8/8 test OK (pytest); avvio uvicorn con log startup/shutdown corretti; `/health` 200 v0.11.0 `db:ok`; `/` 200; `/export` 200 (log 110 record).
- **Versioning**: bump `VERSION` `0.10.0` → `0.11.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.11.0`. **Merge finale su `main` eseguito** (`29e61cd Merge branch 'develop'`), poi rientro su `develop`.
- **Commit**: `feat(core): phase 9 logging, dotenv, systemd`.

### Fase 9b — Toggle dark/light + aggiornamento dipendenze
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: toggle dark/light funzionante nell'header (due sole modalità dark/light, nessun rilevamento sistema); aggiornamento dipendenze (`pip list --outdated`).
- **Cosa è stato fatto**:
  - **`app/static/theme.js`** (nuovo): toggle bistabile dark/light, salva in `localStorage["theme-preference"]` (default light), applica `data-theme="dark"` su `<html>`, aggiorna icona/label. Nessun matchMedia.
  - **`app/templates/base.html`**: pulsante `.app-header__theme-toggle` (#theme-toggle) con icona ☀️/🌙 dentro `.app-header__actions`; script inline anti-FOUC nel `<head>` che applica il tema salvato prima del rendering; `theme.js` incluso con `defer`.
  - **`app/static/style.css`**: blocco `[data-theme="light"]` esplicito; stile `.app-header__theme-toggle`/`.app-header__theme-icon` coerenti con `.app-header__user`; commento dark aggiornato.
  - **`app/routers/web.py`**: label fase "Fase 9b — Toggle dark/light".
  - **Dipendenze**: `uvicorn` 0.52.0 → 0.52.1 (PATCH). Tentativo `pydantic-core` 2.47.0 **scartato** (incompatibile con pydantic 2.13.4) → ripristinato 2.46.4, `pip check` OK.
  - **`VERSION`**: `0.11.0` → `0.12.0` (MINOR).
- **Verifiche**: 8/8 test OK; `GET /` label Fase 9b + `#theme-toggle` presente + script anti-FOUC; `/static/theme.js` e `/static/style.css` 200. Verifica utente (browser) raccomandata per il toggle.
- **Versioning**: bump `VERSION` `0.11.0` → `0.12.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.12.0`. **Merge su `main` autorizzato dall'utente** a fine fase (`7831283 Merge branch 'develop'`), poi rientro su `develop`.
- **Commit**: `feat(ui): phase 9b theme toggle and deps update`.

### Fase 10 — Autenticazione locale
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: login user/password con password hashate (bcrypt) e sessione HTTP firmata.
- **Cosa è stato fatto**:
  - **`app/models/user.py`** (nuovo): tabella `users` (id, username UNIQUE, password_hash, role).
  - **`app/models/__init__.py`**: import `User`.
  - **`app/core/seed.py`**: `seed_admin_user(db)` idempotente — crea l'utente admin (role=admin) se la tabella users è vuota; password/username da `config`.
  - **`app/config.py`**: `AUTH_ENABLED` (env `EFFORT_TRACKING_AUTH_ENABLED`, default true), `ADMIN_USERNAME`/`ADMIN_PASSWORD` (env, default admin/admin).
  - **`app/dependencies.py`** (nuovo): `get_current_user` (dependency FastAPI che legge la sessione e carica l'utente).
  - **`app/routers/auth.py`** (nuovo): `GET /login`, `POST /login` (verifica bcrypt, crea sessione), `GET /logout` (cancella sessione). Use `Response` come return type di POST per evitare l'errore FastAPI con Union di risposte.
  - **`app/main.py`**: `SessionMiddleware` con `SECRET_KEY`; chiama `seed_admin_user` nel lifespan; registra il router auth.
  - **`app/routers/web.py`**: route `/`, `/export`, `POST /` protette con `_require_auth` (redirect a `/login` se manca sessione); campo User forzato allo username della sessione quando auth attiva; passa `current_username`/`auth_enabled` al template; label "Fase 10 — Autenticazione". `/health` resta pubblico.
  - **`app/templates/login.html`** (nuovo): form di login.
  - **`app/templates/base.html`**: area utente con username + "Esci" se loggato, link "Accedi" se no.
  - **`app/templates/index.html`**: campo User `readonly` con `current_username` quando auth attiva.
  - **`app/static/form.js`**: validazione User saltata quando il campo è readonly.
  - **`app/static/style.css`**: stili `.login-card`, `.login-form`, `.app-header__user-auth`, `.app-header__logout/.login`.
  - **`requirements.txt`**: `passlib[bcrypt]>=1.7`, `bcrypt<4.1` (pin per compatibilità passlib 1.7.4), `itsdangerous>=2.0.0` (richiesto da SessionMiddleware).
  - **`.env.example` / `.env`**: `EFFORT_TRACKING_AUTH_ENABLED`, `EFFORT_TRACKING_ADMIN_USERNAME`, `EFFORT_TRACKING_ADMIN_PASSWORD`.
  - **`VERSION`**: `0.12.0` → `0.13.0` (MINOR).
- **Decisioni tecniche**:
  - Sessione HTTP firmata (SessionMiddleware) invece di JWT: più semplice e adatto a app server-rendered (vedi clinerules 06-security).
  - Campo User del form forzato lato server → `readonly` lato client.
  - `bcrypt` pinnato `<4.1` per il bug noto di passlib 1.7.4 (`detect_wrap_bug`).
- **Verifiche**: 11/11 test OK (8 precedenti + 3 nuovi: creazione admin, hash valido, idempotenza); `pip check` pulito; flusso curl completo: GET / senza sessione → 303 /login; POST /login errato → errore; POST /login admin/admin → 303 /; GET / loggato → 200 con username admin + campo User readonly; GET /logout → 303 /login; GET / dopo logout → 303 /login.
- **Versioning**: bump `VERSION` `0.12.0` → `0.13.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.13.0`. Niente `main`.
- **Commit**: `feat(auth): phase 10 local authentication with session`.

### Fase 11 — Multiutente e segregazione
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: `user_id` valorizzato, segregazione dei dati, predisposizione ruoli. Nessuno (nemmeno admin/manager) modifica o elimina record altrui — regola aziendale.
- **Cosa è stato fatto**:
  - **`app/models/effort_entry.py`**: `user_id` ora è una **ForeignKey verso `users.id`** con `ON DELETE SET NULL` e indice; rimosse la colonna legacy `user_text` (dati di sviluppo eliminati su richiesta utente); aggiunta relazione `user`.
  - **`app/core/migrations.py`** (NUOVO): `run_schema_migrations(engine)` idempotente — ricrea `effort_entries` (DROP + create_all) se la colonna `user_text` è ancora presente. Dati di sviluppo eliminati (nessun backfill ad admin, che resta utente di sola gestione).
  - **`app/core/seed.py`**: `seed_test_users` (mario, giulia, luca, password `test`) e `seed_test_records` (~20 record/utente sui giorni feriali 2026, seed fisso riproducibile). Entrambe idempotenti.
  - **`app/main.py`**: nel lifespan esegue `run_schema_migrations` prima di `create_all`, poi chiama i nuovi seed.
  - **`app/routers/web.py`**:
    - Helper `_is_admin` e `_filter_by_user`: l'admin vede tutti i record (lettura/export), gli utenti normali solo i propri.
    - `_save_single`/`_save_week`: `user_id` valorizzato con l'utente della sessione su insert.
    - **Regola aziendale**: su update/delete il controllo `entry.user_id != current_user.id` vale per TUTTI, nessuna eccezione admin/manager (nessuno tocca i record degli altri).
    - `_build_csv`: colonna Utente con lo **username reale via JOIN**; vuota per record senza proprietario.
    - Fix `_with_month`: ignora la stringa `"None"` (bug che causava elenco vuoto dopo blocco delete admin senza filtro).
  - **`app/templates/index.html`**: colonna "Utente" visibile **solo all'admin**; `data-user` dalla relazione user; fix campo hidden `month` (`selected_month or ''`) — niente più `?month=None` nel redirect; label "Fase 11 — Multiutente e segregazione".
  - **`tests/test_models.py`**: 22 test OK — nuovi test per schema senza `user_text`, FK presente, seed utenti/record idempotenti, `test_admin_cannot_update_or_delete_others` (regola aziendale), export con username dal JOIN.
- **Decisioni**:
  - Eliminati i record di sviluppo (migrazione DROP + ricreazione vuota) e rimossa la colonna `user_text` come richiesto.
  - Admin NON assegnatario di record: resta utente di gestione con visibilità globale ma nessun record proprio.
  - Regola aziendale: **nessuno modifica/elimina record altrui**, nemmeno admin/manager (evita incomprensioni e responsabilità incrociate).
- **Verifiche**: 22/22 test OK; migrazione + seed al primo avvio (60 record di test); end-to-end curl: admin 62 record + colonna Utente, mario 20 record senza colonna, export segregato, admin bloccato su update/delete record di giulia; bug `month=None` risolto (elenco resta visibile dopo blocco).
- **Versioning**: bump `VERSION` `0.13.1` → `0.14.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.14.0`. Niente `main`.
- **Commit**: `feat(multiuser): phase 11 data segregation`.

### Scomposizione Fase 12 (riorganizzata su richiesta utente 2026-08-03)
La Fase 12 è stata scomposta in sottofasi, riorganizzate "dal basso verso l'alto" (per aggiunta di permessi). L'hardening scala a Fase 13.
- **Fase 12a** — Infrastruttura ruoli e permessi (✅ 2026-08-03)
- **Fase 12b** — Ruolo USER: consolidamento + last_login + sidebar (✅ 2026-08-03)
- **Fase 12c** — Ruolo MANAGER: group_id, vista gruppo, export (✅ 2026-08-03)
- **Fase 12d** — Ruolo ADMIN: pannello amministrativo (CRUD utenti + lookup + records) (✅ 2026-08-03)

### Scomposizione Fase 13 (riorganizzata su richiesta utente 2026-08-03, aggiornata)
La Fase 13 (hardening) è stata scomposta in sottofasi. Fase 14 (produzione/documentazione) è **sempre l'ultima**; l'hardening (13d) la precede.
- **Fase 13a** — Funzionalità admin: disabilita utente + assegnazione gruppo (✅ 2026-08-03)
- **Fase 13b** — Sicurezza e robustezza (404/500 + error.html, ore 1-12, headers) (✅ 2026-08-03)
- **Fase 13c** — Fix stilistici e UX: S1 hamburger login, S3 menu utente, S5 highlight record, Issue J lookup (✅ 2026-08-03)
- **Suggestion 8** — Eliminazione definitiva utente dopo finestra temporale (✅ 2026-08-04)
- **Riassegnazione Issue J → S9** (2026-08-04): l'allineamento del pulsante AGGIUNGI è risolto in 13c; lo stile tabellare residua è un refine grafico → spostato in Future Features come S9.
- **Riorganizzazione /admin/users** — Tabella read-only + pagina modifica dedicata per singolo utente (✅ 2026-08-04, Issue M chiusa)
- **Fase 13d** — Hardening e sicurezza: XSS (Issue F), audit (da fare — penultima)
- **Fase 14** — Produzione e documentazione: test funzionali (Issue H), Issue C export (verificata risolta), systemd, README (da fare — SEMPRE ultima)

### Fase 12a — Infrastruttura ruoli e permessi
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: creare le basi tecniche dei ruoli senza modifica UI. Unica fonte di verità per i controlli di autorizzazione e scheletro del router `/admin`.
- **Cosa è stato fatto**:
  - **`app/core/permissions.py`** (NUOVO): costanti ruoli, helper `is_admin`/`is_manager`/`is_staff`, dependency `require_admin`/`require_manager`.
  - **`app/routers/admin.py`** (NUOVO): router `/admin` scheletro, pronto per la 12b.
  - **`app/routers/web.py`**: rimosso duplicato locale `_is_admin` → usa `is_admin` da permissions.
  - **`app/main.py`**: registra `admin_router`.
- **Verifiche**: 22/22 test OK; server avvia con il router `/admin` senza errori.
- **Versioning**: bump `VERSION` `0.14.0` → `0.15.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.15.0`. Niente `main`.
- **Commit**: `feat(auth): phase 12a roles and permissions infrastructure`.

### Fase 12b — Ruolo USER (consolidamento)
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: verificare e blindare il comportamento del ruolo USER e predispore la sidebar dinamica. Prima fase dell'approccio "dal basso verso l'alto": si consolidano i permessi minimi prima di aggiungere quelli di MANAGER e ADMIN.
- **Cosa è stato fatto**:
  - **`app/models/user.py`**: aggiunta colonna `last_login` (DateTime nullable) per tracciare l'ultimo accesso.
  - **`app/core/migrations.py`**: nuova migrazione `_migrate_users_last_login` (idempotente, `ALTER TABLE users ADD COLUMN last_login DATETIME`).
  - **`app/routers/auth.py`**: al login riuscito `user.last_login = utcnow()` + commit; `sidebar_items: []` nel context login (sidebar vuota in pagina di login).
  - **`app/routers/web.py`**: funzione `_sidebar_items(user)` che per ora restituisce il link "Registrazioni" per ogni ruolo autenticato; passata al context della route `index`.
  - **`app/templates/base.html`**: la sidebar popola le voci iterando `sidebar_items or []`, riusando le classi CSS esistenti (`.sidebar__menu li a`) senza duplicare stili.
  - **`tests/test_models.py`**: test per colonna `last_login` e per `_sidebar_items` (USER e ADMIN).
- **Verifiche**: 25/25 test OK; migrazione applicata al riavvio (log `Aggiunta colonna users.last_login`); login mario → `last_login` popolato; sidebar con "Registrazioni" per utente e admin, vuota in login; isolamento utente (22 record propri, colonna Utente nascosta), export segregato (0 voci altrui).
- **Versioning**: bump `VERSION` `0.15.0` → `0.16.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.16.0`. Niente `main`.
- **Commit**: `feat(roles): phase 12b user role consolidation and last_login`.

### Fase 12c — Ruolo MANAGER (vista gruppo)
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: `group_id` su `users`, migrazione + seed multi-gruppo, pagina gruppo read-only (`GET /group`) con filtro mese ed export, sidebar con link "Registrazioni" + "Gruppo". Il manager sulla pagina personale si comporta come USER (solo propri record); la vista gruppo mostra/esporta i record di tutto il suo gruppo (compresi i propri).
- **Cosa è stato fatto**:
  - **`app/models/user.py`**: aggiunta colonna `group_id` (FK verso `groups.id`, nullable) + relazione `group`.
  - **`app/core/migrations.py`**: migrazione `_migrate_users_group_id` (idempotente, `ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES groups(id)`).
  - **`app/core/seed.py`**: esteso dataset di test — 2 gruppi (SOC, NOC), 2 manager (giulia SOC, marco NOC) e 4 user (mario/paolo SOC, anna/elisa NOC) con `group_id`; `seed_test_records` ora usa il `group_id` del gruppo di appartenenza (120 record totali, ~20/utente). `seed_test_users` crea/aggiorna (upsert) ruolo e gruppo.
  - **`app/routers/web.py`**: helper `_is_manager_view`, `_records_in_group_statement`, `_records_in_group`, `_month_options_in_group`; route **`GET /group`** (read-only) e **`GET /group/export`** (CSV del gruppo); `_sidebar_items` estesa per MANAGER (link "Registrazioni" + "Gruppo").
  - **`app/templates/group.html`** (NUOVO): template dedicato alla vista gruppo, senza card form, colonna "Utente" sempre visibile, filtro mese/anno, bouton "Esporta CSV". Righe non cliccabili.
  - **`tests/test_models.py`**: test per colonna `group_id`, `_sidebar_items` manager, `_is_manager_view`, `_records_in_group`, `_month_options_in_group`, seed giulia manager, manager sulla propria pagina. Totale 33 test.
- **Verifiche**: 33/33 test OK; DB rigenerato (2 gruppi, 6 utenti, 120 record); giulia `/group` → GRUPPO SOC 60 record; marco `/group` → GRUPPO NOC 60 record; mario (user) `/group` → 303 (bloccato).
- **Versioning**: bump `VERSION` `0.16.0` → `0.17.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.17.0`. Niente `main`.
- **Commit**: `feat(role): phase 12c manager role with group view`.

### Fase 12d — Ruolo ADMIN (pannello amministrativo)
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: pannello admin completo. L'admin al login atterra sulla **dashboard `/admin`**; `GET /` redirige a `/admin` per l'admin. **Export mantenuto attivo per admin** (decisione utente). Sidebar admin con 4 voci.
- **Cosa è stato fatto**:
  - **`app/schemas/effort.py`**: nuovi modelli Pydantic `UserCreate`, `PasswordChange`, `RoleChange`, `LookupCreate`.
  - **`app/routers/admin.py`** (riscritto): dashboard `/admin`, records `/admin/records` (+ `/admin/records/export`), gestione utenti `/admin/users` (crea, cambia password, cambia ruolo, elimina) e gestione lookup `/admin/lookup` (create/edit/delete per clienti, gruppi, attività).
  - **`app/routers/web.py`**: `GET /` per admin → redirect `/admin`; `_sidebar_items` estesa per ADMIN (Dashboard, Registrazioni, Gestione Utenti, Gestione Lookup).
  - **`app/routers/auth.py`**: dopo il login, admin → `/admin` (redirect).
  - **Templates nuovi**: `admin_dashboard.html` (benvenuto), `admin_records.html` (tutti i record + export, no form), `admin_users.html` (CRUD utenti), `admin_lookup.html` (CRUD lookup con blocchi per elementi in uso).
  - **`app/static/style.css`**: stili admin/lookup/visually-hidden.
  - **`tests/test_models.py`**: test sidebar admin (4 voci) e mapping `_lookup_model`. Totale 35 test.
- **Protezioni**: no auto-declassamento, no auto-eliminazione, no eliminazione ultimo admin, no eliminazione lookup con record associati.
- **Verifiche**: 35/35 test OK; flusso curl: login admin → `/admin`, `/` → redirect `/admin`, dashboard 200, records (120 record), users 200, lookup 200, creazione utente/lookup ok, auto-declassamento bloccato, eliminazione lookup in uso bloccata; DB rigenerato a dataset standard (120 record).
- **Versioning**: bump `VERSION` `0.17.0` → `0.18.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.18.0`. Niente `main`.
- **Commit**: `feat(admin): phase 12d admin panel with user and lookup management`.

### Fase 13a — Funzionalità admin (disabilita utente + assegnazione gruppo)
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: gestire la dismissione di un lavoratore senza perdere i record. Invece di eliminare fisicamente un utente con record (creando orfani user_id=NULL), si introduce la **disabilitazione** (`disabled` flag): l'utente viene bloccato al login ma i suoi record restano intatti e visibili a manager e admin. Inoltre si completa la gestione del gruppo di appartenenza (Issue K).
- **Cosa è stato fatto**:
  - **`app/models/user.py`**: aggiunta colonna `disabled` (BOOLEAN, default False).
  - **`app/core/migrations.py`**: migrazione `_migrate_users_disabled` (idempotente, `ALTER TABLE users ADD COLUMN disabled BOOLEAN NOT NULL DEFAULT 0`).
  - **`app/routers/auth.py`**: al login, se `user.disabled` → blocco con messaggio "Account disabilitato. Contatta l'amministratore."
  - **`app/routers/admin.py`**:
    - `admin_users` passa anche `groups`, `disabled`, `group_id`, `group_name` alla tabella utenti.
    - Endpoint `POST /users/{id}/disable` — toggle disabilita/abilita (blocca auto-disabilitazione).
    - Endpoint `POST /users/{id}/group` — assegna/rimuove `group_id` a un utente (Issue K).
    - `POST /users/create` ora accetta `group_id` opzionale; **fix**: campi Form individuali (non `Annotated[UserCreate, Form()]`) perché FastAPI non supporta modelli Form misti ad altri Form (stesso fix Fase 5b).
  - **`app/templates/admin_users.html`**: form creazione con select Gruppo; tabella utenti con colonna Gruppo (select per assegnare), colonna Stato (badge Attivo/Disabilitato), toggle Disabilita/Abilita; pulsante Elimina visibile **solo** se l'utente è disabilitato (con avviso record) altrimenti "Disabilita prima" (Suggestion 8).
  - **`app/static/style.css`**: `.btn-sm`, `.badge`, `.badge-active`, `.badge-disabled`, riga `is-disabled`, stili compact per `.admin-actions` (input/select).
  - **`tests/test_models.py`**: test colonna `disabled` + `TestDisabledUser` (default False, persistito, toggle) + `TestUserGroupAssignment` (assegna gruppo, legge nome, svuota gruppo). Totale 41 test.
- **Protezioni**: admin non può disabilitare sé stesso; eliminazione consentita solo dopo disabilitazione.
- **Verifiche**: 41/41 test OK; migrazione applicata (`Colonna users.disabled aggiunta`); flusso curl: login admin → disabilita mario → mario.disabled=1 → login mario bloccato ("Account disabilitato") → mario ripristinato (disabled=0); creazione teseo con gruppo NOC ok; assegnazione gruppo a marco ok; disabilita+elimina teseo ok.
- **Versioning**: bump `VERSION` `0.18.0` → `0.19.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.19.0`. Niente `main`.
- **Commit**: `feat(admin): phase 13a user disable and group assignment`.

### S9 — Tab stile schedario per Gestione Lookup
- **Stato**: ✅ completata il 2026-08-04.
- **Obiettivo**: trasformare la pagina di Gestione Lookup da tre sezioni verticali a un'interfaccia a schede stile schedario con linguette colorate.
- **Cosa è stato fatto**:
  - **`app/templates/admin_lookup.html`**: introdotta barra `<nav class="lookup-tabs">` con 3 `<button>` (Clienti, Gruppi, Attività) con ruoli ARIA `tablist`/`tab`; pannelli `.lookup-tab-panel` con `role="tabpanel"` e `aria-labelledby`; JS vanilla inline per switch tab (click → attiva tab + pannello corrispondente). La macro `lookup_section` resta invariata.
  - **`app/static/style.css`**: ~80 righe di stili per tab stile schedario: linguette con bordo arrotondato solo in alto, effetto "fogli sovrapposti" (ombre/z-index), tab attivo in primo piano con accento colorato differenziato (blu navy per Clienti, verde #2e7d32 per Gruppi, arancione #e67e22 per Attività), pannelli con card e bordo che si fonde visivamente al tab attivo. Responsive su viewport stretti.
  - **`VERSION`**: `0.22.3` → `0.22.4` (PATCH: miglioramento UI senza nuove funzionalità).
- **Verifiche**: il tema dark/light funziona senza modifiche (tutti i nuovi stili usano variabili CSS esistenti); nessuna modifica al backend o alla logica applicativa.
- **Issue-Suggestion.md**: S9 rimossa dalle Future Features (risolta).

### Fase 13b — Sicurezza e robustezza (header HTTP, errori 404/500, ore 1-12)
- **Stato**: ✅ completata il 2026-08-03.
- **Obiettivo**: innalzare la sicurezza del servizio e migliorare la robustezza di fronte agli errori. Chiusura di Issue G (header di sicurezza HTTP), Issue A (pagine errore 404/500), Issue D + Suggestion 2 (validazione ore 1-12 step 0.50).
- **Area applicativa**:
  - **`app/core/security_headers.py`** (NUOVO): middleware `SecurityHeadersMiddleware` (Starlette `BaseHTTPMiddleware`) che aggiunge a ogni risposta: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` (default-src 'self', style/script 'unsafe-inline' per il tema, img data:, object 'none', base-uri self, form-action self), `Strict-Transport-Security`, `Referrer-Policy: no-referrer`, `Permissions-Policy`. Non sovrascrive header già presenti.
  - **`app/main.py`** (riscritto pulito): eliminati gli import duplicati residui; registrati `exception_handlers` per `StarletteHTTPException` (404→`404.html`, 500→`500.html`, altri codici (401/403/405/...)→`error.html` generico con codice+dettaglio) e `RequestValidationError` (→`500.html`); engine `templates` (Jinja2Templates) dal `TEMPLATES_DIR`; helper `_error_context(request)` **sincrono** e senza query DB (solo username da sessione). **Bug risolto durante e2e**: la funzione era `async def` ma chiamata senza `await` → errori 500 sul template 404. Resa sincrona (nessuna I/O). **Miglioramento su richiesta utente**: 401/403/405 ora templatizzati con `error.html` coerente col tema (prima erano HTML spoglio).
  - **`app/schemas/effort.py`**: `EffortEntryCreate.hours` → `Field(ge=1, le=12)` + validatore `hours_step_half` (multipli di 0.50, tolleranza floating point, arrotondamento a 2 decimali). Rimossa la Suggestion 2 (step 0.50).
  - **`tests/test_models.py`**: import di `EffortEntryCreate` e `ValidationError`; nuova classe `TestEffortEntryValidation` (6 test: range 1-12 valido, <1 rifiutato, >12 rifiutato, step 7.25 rifiutato, rounding floating, 12h per Supporto Specialistico consentito). Totale 47 test.
- **Area UI**:
  - **`app/templates/404.html`** (NUOVO): pagina errore 404 coerente con `500.html` (estende `base.html`, bottoni "Torna alla home" / "Vai alla dashboard").
  - **`app/templates/500.html`**: (già creato nel task precedente) pagina errore 500.
  - **`app/templates/index.html`**: input ore `min="1" max="12" step="0.50"`.
  - **`app/static/form.js`**: `isValidHours` ora 1..12 step 0.50; messaggio "Inserisci le Ore Spese (da 1 a 12, step 0.50)."
- **Verifiche**: 47/47 test OK (41 precedenti + 6 nuovi); e2e con server reale: header di sicurezza presenti su `/login` (tutti e 6), 404 → `404.html` con "404 — Pagina non trovata", login admin → 303 `/admin`, `/admin` 200 con sidebar. Bug `_error_context` async trovato e corretto.
- **Decisioni**: XSS (Issue F) **non** affrontato in questa fase → rinviato a Fase 14 (audit sicurezza). Suggestion 4 (filtro anno+mese) rinviata a Fase 13c/13d. `_error_context` volutamente **senza query DB** per pagine di errore robuste anche in caso di problemi di connettività.
- **Versioning**: bump `VERSION` `0.19.0` → `0.20.0` (MINOR).
- **Branch**: commit su `develop`, tag annotato `v0.20.0`. Niente `main`.
- **Commit**: `feat(security): phase 13b security headers and error pages`.

## Decisioni di versioning
- **Strategia**: SemVer. Versione tracciata solo nel file `VERSION` (unico servizio, niente repliche in `__init__.py`).
- **Bump ad ogni commit funzionale**, tag annotato `vX.Y.Z` sullo stesso commit.
- **MAJOR** = breaking changes architetturali.
- **MINOR** = nuove funzionalità retrocompatibili.
- **PATCH** = bug fix, refactoring interno, miglioramenti UI.

### Pagina Profilo Utente — Dati anagrafici e cambio password
- **Stato**: ✅ completata il 2026-08-04.
- **Obiettivo**: creare una pagina `/profile` per visualizzare e modificare nome, cognome, email e per cambiare la password. Predisporre il modello per future self-creation e cambio password obbligatorio.
- **Cosa è stato fatto**:
  - **`app/models/user.py`**: aggiunte colonne `first_name`, `last_name`, `email`, `password_change_required`.
  - **`app/core/migrations.py`**: nuova `_migrate_users_profile` (idempotente, 4 ALTER TABLE).
  - **`app/schemas/effort.py`**: nuovi `ProfileUpdate` e `SelfPasswordChange`.
  - **`app/routers/profile.py`** (NUOVO): GET `/profile`, POST `/profile`, POST `/profile/change-password`.
  - **`app/templates/profile.html`** (NUOVO): due card (Dati personali, Cambia password) con banner.
  - **`app/static/style.css`**: `.profile-page`, `.profile-card`, `.form-row--two`.
  - **`app/static/user-menu.js`**: link "Profilo" diretto, menu si chiude al click su link.
  - **`app/templates/base.html`**: href profilo = `/profile`.
  - **`app/main.py`**: registrato `profile_router`.
  - **`app/core/seed.py`**: popolati `first_name`, `last_name`, `email` per admin e utenti test.
  - **`app/routers/web.py`**: `_sidebar_items` aggiunge "Profilo" per USER e MANAGER.
  - **`memory-bank/Issue-Suggestion.md`**: aggiunte S10 (Self-creation utente) e S11 (Cambio password obbligatorio) in Future Features.
  - **`tests/test_models.py`**: 19 nuovi test (da 53 a 72). Totale 72 test OK.
- **Verifiche**: 72/72 test OK; migrazione 4 colonne applicata; profilo aggiornamento ok; cambio password con verifica vecchia/nuova ok.
- **Note futuro**: `password_change_required` predisposto ma non attivo; `email` non unique per ora; cambio password azzera il flag.

## Cose note / limitazioni accettate
- Auth attiva da Fase 10: route business protette da sessione, `/health` pubblico.
- `bcrypt` pinnato `<4.1` per compatibilità con passlib 1.7.4.
- Toggle dark/light funzionante dalla Fase 9b (due modalità, preferenza localStorage).
- `pydantic-core` pinnato a 2.46.4 per compatibilità con pydantic 2.13.4.
- Migrazioni schema con `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE` controllato; Alembic proposto se la complessità cresce.
- `user_id` con FK verso `users.id` (ON DELETE SET NULL) dalla Fase 11; nessuno modifica/elimina record altrui (regola aziendale).
- La cancellazione è **permanente** e senza soft-delete/audit (da valutare in Fase 14/hardening).
- I campi del form sono opzionali nella firma della route `POST /`: la validazione obbligatoria avviene comunque server-side via `EffortEntryCreate` per le azioni che creano/aggiornano record. Per `action=delete` bastano `record_id`.
- DB di sviluppo (Fase 12c): 2 gruppi (SOC, NOC), 6 utenti di test (giulia/marco manager, mario/paolo/anna/elisa user) con ~20 record ciascuno, password `test`, più admin. La colonna `user_text` è stata rimossa in Fase 11.
- Configurazione: il `.env` locale è per lo sviluppo; in produzione systemd legge `/etc/efftrack.env` (EnvironmentFile). Livello log controllato da `EFFORT_TRACKING_LOG_LEVEL`.

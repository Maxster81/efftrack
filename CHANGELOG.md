# Changelog

Tutte le modifiche rilevanti del progetto sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/) e il versioning [SemVer](https://semver.org/).

## [1.9.1] - 2026-08-26

### Fixed
- **Pagina 401 chiara per sessione scaduta**: quando la sessione scade (o manca) e l'utente
  compie un'azione su una route protetta (es. `/admin/*`), l'app mostrava la `error.html`
  generica con il messaggio fuorviante "Controlla i permessi dell'account o l'URL". Ora il
  codice 401 renderizza una pagina dedicata **"Sessione scaduta"** (`app/templates/401.html`)
  con il messaggio corretto e i pulsanti "Accedi" (`/login`) e "Torna alla home". La 403 resta
  sulla `error.html` (messaggio sui permessi, corretto). In `Issue-Suggestion.md` aperto il
  TODO **SESSION-TIMER** per un reminder di scadenza a 5 minuti (solo UX, non implementato).

## [1.9.0] - 2026-08-26

### Added
- **Export Excel (XLSX)**: gli export dei record possono ora essere generati in formato
  `.xlsx` oltre che in CSV. Nuovo servizio `app/services/export_xlsx.py` (`build_xlsx`, con
  `openpyxl`): stesse colonne del CSV, header in grassetto, larghezze calibrate, ore come
  numero, esclusione dei giorni "NON LAVORATO".
- **Parametro `format`**: gli endpoint `/export`, `/group/export`, `/admin/records/export`
  accettano `?format=xlsx` (default CSV, retrocompatibile). Nuova dipendenza `openpyxl>=3.1.0`.
- **UI**: nelle pagine index/group/admin_records il bottone "Esporta CSV" è stato sostituito
  da un **menu a tendina "Formato" (Excel di default / CSV)** + bottone "Esporta" (submit del
  form filtro verso l'endpoint export, mantiene i filtri anno/mese, nessun JS aggiuntivo).

## [1.8.9] - 2026-08-26

### Fixed
- **CSS/JS/favicon non caricati dietro reverse proxy HTTPS (NetScaler)**: i template usavano
  `url_for('static', path='...')` che in Starlette genera URL **assoluti** con lo scheme della
  richiesta in ingresso (HTTP dietro il proxy) → gli asset risultavano `http://...`, bloccati
  dalla CSP `'self'` (pagina su `https`) e da Mixed Content. Ora gli asset statici usano path
  relativi `/static/...` (in `base.html` e `index.html`), risolti dal browser rispetto alla
  pagina HTTPS. Non servono più `url_for('static', ...)`.

## [1.8.8] - 2026-08-26

### Added
- **`deploy.sh --update` ora fa il `git pull` dal repository** (pattern mutuato dal
  progetto paroleMutanti): prima di aggiornare, esegue `git pull --ff-only` nel clone
  (la directory da cui si lancia lo script, non `$DEPLOY_DIR`) e si ri-esegue con
  `exec` per caricare l'ultima versione di se stesso. Se la directory corrente non è
  un repo git, il pull viene saltato e l'update procede con i file già presenti.
  Conserva `--dir`/`--env-file` personalizzati attraverso il re-exec (env
  `EFFTRACK_DEPLOY_DIR`/`EFFTRACK_ENV_FILE`).

## [1.8.7] - 2026-08-23

### Fixed
- **Feedback del middleware cambio password**: quando un utente con `password_change_required`
  attivo tenta un'azione (es. cambio password di un altro utente da admin), il middleware ora
  reindirizza a `/profile?pwd_blocked=<path>` e la pagina profilo mostra un banner esplicito
  "Azione non eseguita" con il percorso bloccato. Prima il redirect era silenzioso e la modifica
  non veniva applicata senza alcun avviso.

## [1.4.1] - 2026-08-06

### Fixed
- **Voce sentinella "NON LAVORATO"** (S13): nella pagina `admin/lookup` non è più possibile
  rinominare né eliminare la voce sentinella usata per i giorni non lavorati (S6). Lato UI la
  riga è renderizzata come statica (con etichetta "sentinella"); lato server sono bloccate
  `create`/`edit`/`delete` sul nome "NON LAVORATO". Protegge il meccanismo dei giorni non
  lavorati da rinominazioni/eliminazioni accidentali da parte dell'admin.

## [1.4.0] - 2026-08-06

### Added
- **Deploy con DB pulito**: `deploy.sh` di default crea un database **vuoto** con il solo
  utente admin. La nuova variabile `EFFORT_TRACKING_DEMO_MODE` (default `false`) controlla il
  seed dei dati demo.
- **Opzione `--demo`** in `deploy.sh`: `sudo ./deploy.sh --demo` popola il DB con dati di
  esempio (gruppi "Gruppo 1"/"Gruppo 2", utenti e record di test). Da usare SOLO per ambienti
  demo/test, non in produzione.
- Rinominati i gruppi di demo da "GRUPPO SOC"/"GRUPPO NOC" a "Gruppo 1"/"Gruppo 2" e le
  attività da "SOC-Conduzione"/"SOC-Supporto Specialistico" a "Conduzione"/"Supporto Specialistico".

## [1.3.2] - 2026-08-06

### Fixed
- **Installazione pulita**: il servizio systemd non partiva su una prima installazione
  (`226/NAMESPACE`). Causa: `ReadWritePaths=/opt/efftrack/data` richiede che `data/`
  esista **prima** dell'avvio del servizio; su installazione pulita non esisteva.
  `deploy.sh --install` ora crea sempre `data/` (mkdir + chown) subito dopo la rsync.
- **Host/porta**: l'`ExecStart` di `systemd/efftrack.service` usa ora `uvicorn` **diretto**
  (niente wrapper `/bin/bash -c`, che rompeva il mount namespace di systemd, e niente
  `--host`/`--port` hardcodati). Host e porta sono letti da uvicorn tramite le variabili
  native `UVICORN_HOST` / `UVICORN_PORT` (default `127.0.0.1:8000`).
- `.env.example` aggiornato: `UVICORN_HOST`/`UVICORN_PORT` sostituiscono
  `EFFORT_TRACKING_HOST`/`EFFORT_TRACKING_PORT` come fonte per host/porta del server.

## [1.3.1] - 2026-08-06

### Changed (sostituito in 1.3.2)
- Tentativo di rendere host/porta configurabili nel servizio systemd avvolgendo
  `ExecStart` in `/bin/bash -c`. **Ritirato in 1.3.2** perché su installazione pulita
  rompeva il mount namespace di systemd (`226/NAMESPACE`). Vedi 1.3.2 per la soluzione.

## [1.3.0] - 2026-08-05

### Added
- **Dashboard admin** (`GET /admin`) con KPI e metriche di sistema: utenti
  totali/attivi/disabilitati, record totali, ore del mese, record di oggi,
  distribuzione per gruppo, utenti inattivi, attività recente, stato sistema.

## [1.2.1] - 2026-08-05

### Fixed
- Allineamento verticale del campo "Giorno non lavorato" nel form.

## [1.2.0] - 2026-08-05

### Added
- **Giorno non lavorato** (S6): checkbox nel form che crea un record con lookup
  sentinella "NON LAVORATO". Gli export CSV escludono i giorni non lavorati.

## [1.1.1] - 2026-08-05

### Fixed
- Firma robusta del listener di connettività SQLite per compatibilità con
  SQLAlchemy 2.0.x e future 3.x.

## [1.1.0] - 2026-08-04

### Added
- **Cambio password obbligatorio al primo login** (S11): seed admin e nuovi utenti
  con `password_change_required=True`, redirect a `/profile`, banner di primo accesso.

## [1.0.1] - 2026-08-04

### Fixed
- **Sessione con scadenza** (Issue N): il cookie di sessione ora scade dopo
  `EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS` (default 1800 s = 30 min).

## [1.0.0] - 2026-08-04

### Added
- Fase 14 completata: documentazione README completa, `deploy.sh`, suite di test
  funzionali (pytest + HTTPX).
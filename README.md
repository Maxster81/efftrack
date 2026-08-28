# Effort Tracking

Web server per la registrazione di **effort** (ore lavorate, attività giornaliere, note) con
gestionale CRUD. Sostituto moderno del vecchio tool aziendale, installabile su **Ubuntu** con
**Python `venv`** (no Docker).

> **Stato**: **v1.8.5** — versione stabile pronta per produzione.
> Autenticazione attiva (locale + login federato **SAML/MFA** con Microsoft Entra ID),
> multiutente con ruoli (USER/MANAGER/ADMIN), hardening di sicurezza, cambio password
> obbligatorio al primo login, suite di test completa (129 test + 5 subtests verdi).
> La documentazione di stato dettagliata è in [`memory-bank/`](./memory-bank/).

---

## Funzionalità

- **Registrazione effort**: form in alto + tabella elenco in basso, CRUD completo.
- **Copia su settimana**: inserimento bulk dei giorni feriali.
- **Filtro per mese** nell'elenco e negli export.
- **Export in CSV** (UTF-8 con BOM) **o XLSX** (Excel, via `openpyxl`) con segregazione dati per utente.
- **Autenticazione** locale con sessione firmata e password hashate (bcrypt).
- **Login federato SAML 2.0** con **Microsoft Entra ID** (MFA gestita da Microsoft), accanto al login locale.
- **Multiutente**: ogni utente vede/cambia/elimina solo i propri record.
- **Ruoli**: `USER`, `MANAGER` (vista gruppo), `ADMIN` (pannello di gestione).
- **Pannello admin**: dashboard, registrazioni globali, gestione utenti, gestione lookup.
- **Profilo utente**: dati anagrafici e cambio password.
- **Tema dark/light** con preferenza salvata nel browser.
- **Sicurezza**: header HTTP, body limit, cookie sessione SameSite/Secure, validazione server-side.

---

## Requisiti

- Ubuntu (testato su 22.04 LTS) o qualunque distribuzione con Python ≥ 3.10.
- `python3`, `python3-venv`, `python3-pip`.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Per l'**autenticazione SAML/Microsoft** (opzionale) serve anche la dipendenza di sistema `xmlsec1`:
```bash
sudo apt install -y xmlsec1 libxml2-dev libxmlsec1-dev
```
Vedi [`docs/saml-autenticazione.md`](docs/saml-autenticazione.md) per i dettagli.

---

## Installazione e avvio in sviluppo

```bash
cd /home/tuafolder/efftrack   # o la tua cartella del progetto
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Crea il file di configurazione locale (opzionale; se non esiste
# vengono usati i default di sviluppo, vedi .env.example)
cp .env.example .env

# Avvia il server in sviluppo
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoint disponibili:

- `http://localhost:8000/` — pagina di registrazione effort (richiede login).
- `http://localhost:8000/health` — health check pubblico (status app + check DB).
- `http://localhost:8000/docs` — documentazione OpenAPI generata da FastAPI.

> **Nota binding**: in sviluppo il server è bindato a `0.0.0.0` per accessibilità da rete
> locale/WSL/VM. In produzione si usa `127.0.0.1` dietro un reverse proxy (vedi sotto).

---

## Configurazione

Tutte le impostazioni sono sovrascrivibili via variabili d'ambiente. Vedi
[`.env.example`](./.env.example) per l'elenco completo.

```bash
cp .env.example .env
# modifica .env a piacere
```

Variabili principali:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `EFFORT_TRACKING_SECRET_KEY` | placeholder dev | Chiave per firmare le sessioni. **In produzione genera una chiave robusta.** |
| `EFFORT_TRACKING_DB_URL` | `sqlite:///./data/efftrack.db` | URL del database (SQLite oggi, PostgreSQL in futuro). |
| `UVICORN_HOST` / `UVICORN_PORT` | `0.0.0.0` / `8000` | Host e porta del web server. Li legge direttamente uvicorn (funzionano anche con systemd). Se il reverse proxy è **locale** (nginx/Caddy su localhost) usa `127.0.0.1`; se è **remoto** (es. NetScaler) o l'app è esposta direttamente usa `0.0.0.0`. |
| `EFFORT_TRACKING_LOG_LEVEL` | `INFO` | Livello dei log (DEBUG/INFO/WARNING/ERROR). |
| `EFFORT_TRACKING_AUTH_ENABLED` | `true` | `true` login obbligatorio, `false` server pubblico. |
| `EFFORT_TRACKING_DEMO_MODE` | `false` | `true` = seed dati di esempio (gruppi, utenti, record di test). In produzione resta `false` (DB pulito, solo admin). |
| `EFFORT_TRACKING_ADMIN_USERNAME` / `EFFORT_TRACKING_ADMIN_PASSWORD` | `admin` / `admin` | Credenziali **temporanee** del primo admin (lette solo al primo seed). **In produzione vanno sovrascritte.** Al primo login l'admin è obbligato a cambiarle. |
| `EFFORT_TRACKING_USER_DELETE_GRACE_DAYS` | `30` | Giorni di attesa prima che un utente disabilitato sia eliminabile. |
| `EFFORT_TRACKING_SESSION_SAMESITE` / `EFFORT_TRACKING_SESSION_SECURE` | `lax` / `false` | Sicurezza cookie di sessione. `SECURE=true` richiede HTTPS (il browser scarta il cookie di sessione su HTTP): su pre-prod/sviluppo senza TLS impostare `false`; in produzione dietro reverse proxy con TLS impostare `true`. |
| `EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS` | `1800` | Durata massima sessione in secondi (30 min). Se l'utente chiude il browser senza logout, alla scadenza serve rilogin. |
| `EFFORT_TRACKING_MAX_BODY_BYTES` | `1048576` (1 MiB) | Limite massimo del body delle richieste. |
| `EFFORT_TRACKING_SAML_ENABLED` | `false` | Abilita il login federato SAML/Microsoft. Disattivato di default. |
| `EFFORT_TRACKING_SAML_ENTITY_ID` | `https://efftrack.example.com/saml/metadata` | Entity ID SP (da far combaciare con l'Identifier in Azure). |
| `EFFORT_TRACKING_SAML_ACS_URL` | `https://efftrack.example.com/saml/acs` | Endpoint ACS pubblico (Reply URL in Azure). |
| `EFFORT_TRACKING_SAML_IDP_ENTITY_ID` | *(vuoto)* | Entity ID dell'IdP Microsoft (`https://sts.windows.net/<tenant>/`). |
| `EFFORT_TRACKING_SAML_IDP_METADATA_URL` | *(vuoto)* | URL/path del metadata XML dell'IdP. |
| `EFFORT_TRACKING_SAML_CERT_FILE` / `EFFORT_TRACKING_SAML_KEY_FILE` | *(vuoto)* | Certificato/chiave SP (firma AuthnRequest opzionale). |
| `HTTPS_PROXY` / `HTTP_PROXY` / `NO_PROXY` | *(vuoto)* | Proxy HTTP/HTTPS per il **traffico in uscita** (es. il fetch del metadata SAML verso Microsoft in reti aziendali). PySAML2 via `requests` le legge dall'ambiente (systemd `EnvironmentFile`). `NO_PROXY=127.0.0.1,localhost` evita di instradare il loopback nel proxy. |

Il file `.env` reale **non** va committato (è coperto da `.gitignore`).

---

## Deploy in produzione (Ubuntu + systemd)

Ci sono due strade: **script automatizzato** (consigliata) o **passi manuali**.

### Opzione A — Script automatizzato `deploy.sh`

Lo script `deploy.sh` (root del repo) automatizza: creazione utente/directory/venv, copia del
codice, generazione di `/etc/efftrack.env` e installazione del servizio systemd.

> ⚠️ **Wizard di configurazione**: durante l'installazione (`deploy.sh`, `--install`, `--env`
> o `--demo`) lo script pone una serie di **domande guidate** (directory di installazione,
> reverse proxy/host, porta, generazione password admin, attivazione SAML) e genera
> automaticamente `/etc/efftrack.env` con tutti i valori, evitando di dover modificare a
> mano i file successivamente. In ambienti non interattivi senza `/dev/tty` vengono usati
> i default sicuri.

```bash
sudo ./deploy.sh           # deploy completo (consigliato)
# oppure in step separati:
sudo ./deploy.sh --install # solo installazione (venv + dipendenze + copia)
sudo ./deploy.sh --env     # solo generazione /etc/efftrack.env
sudo ./deploy.sh --service # solo installazione/avvio del servizio systemd
sudo ./deploy.sh --update  # aggiornamento in-place di un'installazione esistente
# Directory di installazione e file env personalizzati (valgono per TUTTE le modalità):
sudo ./deploy.sh --install --dir /home/efftrack --env-file /home/efftrack/efftrack.env
sudo ./deploy.sh --help    # aiuto
```

Lo script genera una `SECRET_KEY` robusta e crea `/etc/efftrack.env` con valori sicuri.
**CAMBIA la password admin** (`EFFORT_TRACKING_ADMIN_PASSWORD`) prima di andare in produzione.

> **Nota sui path personalizzati (`--dir` / `--env-file`)**: il template
> `systemd/efftrack.service` usa i path **standard** `/opt/efftrack` e `/etc/efftrack.env`
> (in `WorkingDirectory`, `ExecStart`, `ReadWritePaths`, `EnvironmentFile`). Se installi in
> una directory diversa o con un file env personalizzato, `deploy.sh` copia il template così
> com'è: **devi adattare a mano** il tuo `/etc/systemd/system/efftrack.service` prima di
> avviare il servizio, altrimenti punterà a path inesistenti. In modalità `--update` il
> `.service` **non viene mai sovrascritto**: lo script lo segnala e mostri il diff.
>
> Con
> `--dir /home/efftrack` ed `EFFORT_TRACKING_DB_URL=sqlite:////home/efftrack/data/efftrack.db`
> nell'env custom, un esempio di `ReadWritePaths` corretto è `/home/efftrack/data`.

Con il flag `--demo` (es. `sudo ./deploy.sh --demo`) il DB viene popolato con dati di
esempio (gruppi "Gruppo 1"/"Gruppo 2", utenti e record di test): da usare SOLO per
ambiente demo/test. Di default (senza flag) il deploy crea un DB **pulito** con il solo
utente admin.
La password admin è **temporanea**: viene letta solo al primo seed (tabella `users` vuota) e
hashata nel DB. Al primo login l'admin è reindirizzato a `/profile` e **deve** cambiarla prima
di poter navigare (stessa regola vale per i nuovi utenti creati dall'admin: la password impostata
in fase di creazione è temporanea e va cambiata al primo accesso).

### Opzione A1 — Aggiornamento in-place (`--update`)

Per aggiornare un'installazione già esistente (senza perdere dati né configurazioni):

```bash
sudo ./deploy.sh --update                            # aggiorna in /opt/efftrack
sudo ./deploy.sh --update --dir /home/efftrack       # se hai installato altrove
sudo ./deploy.sh --update --env-file /etc/efftrack.env  # se hai un env personalizzato
```

> 💡 **`--update` esegue il `git pull` dal repository** (pattern mutuato dal progetto
> paroleMutanti). Prima di aggiornare, lo script esegue `git pull --ff-only` nel clone
> (la directory da cui lo lanci, ad es. la root del repo) e si **ri-esegue da solo**
> (`exec`) per caricare l'ultima versione di se stesso; poi prosegue con rsync +
> dipendenze + restart. Non serve più fare `git pull` a mano prima dell'update. Se la
> directory corrente non è un repo git, il pull viene saltato e l'update procede con i
> file già presenti.

Cosa fa `--update`:

0. (se il clone è un repo git) `git pull --ff-only` + ri-esecuzione automatica per caricare l'ultima versione dello script.
1. Verifica che esista un'installazione (directory + servizio systemd).
2. Controlla la versione installata (`DEPLOY_DIR/VERSION`): se è sotto la soglia minima
   (`1.6.0`, costante `MIN_UPDATE_VERSION` in `deploy.sh` — la prima versione con la
   dipendenza di sistema `xmlsec1`) blocca e stampa la procedura di
   **backup + reinstallazione**.
3. Crea un backup automatico in `DEPLOY_DIR/backups/YYYYMMDD-HHMMSS/` di:
   - il database (`data/efftrack.db`),
   - il file env (default `/etc/efftrack.env`, o il percorso passato con `--env-file`),
   - l'unità systemd (`/etc/systemd/system/efftrack.service`).
4. Ferma il servizio, copia il nuovo codice (escludendo `data/`, `.venv`, `backups/`, ecc.),
   aggiorna le dipendenze Python (`pip install -r requirements.txt`).
5. **Non sovrascrive** i file personalizzati:
   - Segnala le **nuove variabili d'ambiente** (presenti in `.env.example` ma assenti nel
     tuo file env). L'app usa già i default interni in `config.py`, quindi puoi ignorarle
     o aggiungerle a mano in base alla documentazione in `.env.example`.
   - Se l'unità systemd è cambiata nella nuova versione, mostra il **diff** e ti istruisce
     su come aggiornarla manualmente (importante se usi `--dir` o `--env-file` personalizzati:
     devi adattare `WorkingDirectory`, `ExecStart`, `EnvironmentFile` nel service).
6. Riavvia il servizio ed esegue l'health check.

> **Database**: il DB non viene mai toccato da `--update`. Le modifiche allo schema (nuove
> tabelle/colonne) vengono applicate a runtime alla prima accensione tramite le migrazioni
> idempotenti in `app/core/migrations.py`. La versione schema viene tracciata nella tabella
> `schema_version` (un solo record con la versione dell'app che ha eseguito l'ultima migrazione).
> Se hai impostato un percorso DB completamente fuori da `data/`, il backup automatico potrebbe
> non trovarlo: in quel caso fai un backup manuale prima dell'update.

### Soglia minima e reinstallazione

Se l'update non è consentito (versione installata < `MIN_UPDATE_VERSION`), esegui il **backup
manuale** e la **reinstallazione** seguendo le istruzioni stampate da `--update`, oppure:

1. `sudo systemctl stop efftrack`
2. Copia in un posto sicuro: `DEPLOY_DIR/data/efftrack.db`, l'env file, la unità systemd.
3. `sudo rm -rf DEPLOY_DIR`
4. Clona il nuovo repo ed esegui `sudo ./deploy.sh --install --dir ... --env-file ...`.
5. Ferma il servizio, ripristina DB ed env dai backup, riavvia.
6. Al primo avvio le migrazioni portano il DB alla versione corrente.

### Opzione B — Passi manuali

Il template dell'unità systemd è in [`systemd/efftrack.service`](./systemd/efftrack.service).
Viene documentato in testa al file; in sintesi:

```bash
sudo cp systemd/efftrack.service /etc/systemd/system/efftrack.service
sudo useradd --system --home /opt/efftrack --shell /usr/sbin/nologin efftrack
sudo mkdir -p /opt/efftrack
# IMPORTANTE: crea anche data/ (richiesta da ReadWritePaths del service PRIMA
# dell'avvio, altrimenti error 226/NAMESPACE) e dai i permessi:
sudo mkdir -p /opt/efftrack/data
sudo chown -R efftrack:efftrack /opt/efftrack
# copia il codice in /opt/efftrack (es. rsync), crea il venv e installa le dipendenze
sudo cp .env.example /etc/efftrack.env   # poi personalizza (vedi config)
sudo systemctl daemon-reload
sudo systemctl enable --now efftrack.service
sudo systemctl status efftrack.service
sudo journalctl -u efftrack -f            # log
```

> **Nota**: il template NON hardcoda host/porta: uvicorn li legge dalle variabili native
> `UVICORN_HOST` / `UVICORN_PORT` definite in `/etc/efftrack.env` (default interni
> `127.0.0.1:8000`). In produzione si usa un **reverse proxy** davanti a Uvicorn. Se il reverse
> proxy è **locale** (nginx/Caddy su localhost) usa `127.0.0.1`; se è **remoto** (es. NetScaler)
> o l'app è esposta direttamente, imposta `UVICORN_HOST=0.0.0.0`.
> Per ascoltare su un'altra interfaccia/porta (es. pre-prod su `0.0.0.0:8010`) basta impostare
> quelle variabili in `/etc/efftrack.env` e riavviare: `sudo systemctl restart efftrack`.
> I log escono su **journald**.

---

## Migrazione futura a PostgreSQL

Il progetto è predisposto al passaggio da SQLite a PostgreSQL: è sufficiente modificare
`EFFORT_TRACKING_DB_URL` (config) senza refactoring di repository/service. Il prefisso mostra
l'esempio: `postgresql://efftrack:PASSWORD@localhost:5432/efftrack`.

---

## Test

La suite di test usa `pytest` + `httpx` (dipendenze DEV in `requirements-dev.txt`).

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

- **Test**: `tests/test_models.py` (modelli, seed, validazione, segregazione),
  `tests/test_functional.py` (test end-to-end HTTP su route, auth, permessi, CRUD, export)
  e `tests/test_saml.py` (flusso SAML con client mockato: creazione/associazione utente,
  errori di validazione, messaggi leggibili).
- I test usano un database SQLite **dedicato e isolato** (non toccano `data/efftrack.db`).

---

## Documentazione

- [**Guida all'installazione e gestione del server**](docs/installazione.md) — per chi
  installa e amministra EffTrack su Ubuntu (deploy, configurazione, aggiornamento, backup,
  troubleshooting).
- [**Autenticazione SAML con Microsoft Entra ID**](docs/saml-autenticazione.md) — guida
  per amministratori di sistema alla configurazione del login federato SAML (Azure ed
  EffTrack, firme, testing).
- [**Guida utente**](docs/guida-utente.md) — manuale d'uso del prodotto per gli utenti
  finali (registrazione effort, filtro, export, ruoli e permessi).

---

## Struttura del progetto

```
efftrack/
├── app/                # codice applicativo (FastAPI)
│   ├── main.py         # entry point, lifespan, middleware, errori
│   ├── config.py       # configurazione centralizzata (env vars)
│   ├── db.py           # engine, sessione, dependency
│   ├── dependencies.py # dependency di autenticazione
│   ├── core/           # body_limit, logging, migrazioni, password_change, permissions, seed, security_headers
│   ├── routers/        # web, auth, admin, profile, api
│   ├── schemas/        # modelli Pydantic (validazione)
│   ├── models/         # modelli ORM (SQLAlchemy)
│   ├── repositories/   # accesso dati dedicato
│   ├── services/       # logica di servizio
│   ├── templates/      # template Jinja2
│   └── static/         # CSS e JS
├── systemd/            # template unit systemd (NON attivato)
├── data/               # SQLite (gitignored)
├── tests/              # pytest (unit + funzionali)
├── memory-bank/        # documentazione persistente di progetto
├── deploy.sh           # script di deploy opzionale
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── VERSION             # versione del progetto (SemVer)
```

---

## Workflow del progetto

Il progetto segue una roadmap a fasi documentata in [`memory-bank/`](./memory-bank/). Ogni fase
si considera completata solo dopo conferma esplicita dell'utente. Lo stato corrente è riflesso in
[`memory-bank/activeContext.md`](./memory-bank/activeContext.md) e
[`memory-bank/progress.md`](./memory-bank/progress.md).

---

## Licenza

Da definire.
# Effort Tracking

Web server per la registrazione di **effort** (ore lavorate, attività giornaliere, note) con
gestionale CRUD. Sostituto moderno del vecchio tool aziendale, installabile su **Ubuntu** con
**Python `venv`** (no Docker).

> **Stato**: **v1.1.1** — versione stabile pronta per produzione.
> Autenticazione attiva, multiutente con ruoli (USER/MANAGER/ADMIN), hardening di sicurezza,
> cambio password obbligatorio al primo login, suite di test completa (107 test verdi). La documentazione di stato dettagliata è in
> [`memory-bank/`](./memory-bank/).

---

## Funzionalità

- **Registrazione effort**: form in alto + tabella elenco in basso, CRUD completo.
- **Copia su settimana**: inserimento bulk dei giorni feriali.
- **Filtro per mese** nell'elenco e negli export.
- **Export CSV** (UTF-8 con BOM) con segregazione dati per utente.
- **Autenticazione** locale con sessione firmata e password hashate (bcrypt).
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
| `EFFORT_TRACKING_HOST` / `EFFORT_TRACKING_PORT` | `0.0.0.0` / `8000` | Host e porta del web server. |
| `EFFORT_TRACKING_LOG_LEVEL` | `INFO` | Livello dei log (DEBUG/INFO/WARNING/ERROR). |
| `EFFORT_TRACKING_AUTH_ENABLED` | `true` | `true` login obbligatorio, `false` server pubblico. |
| `EFFORT_TRACKING_ADMIN_USERNAME` / `EFFORT_TRACKING_ADMIN_PASSWORD` | `admin` / `admin` | Credenziali **temporanee** del primo admin (lette solo al primo seed). **In produzione vanno sovrascritte.** Al primo login l'admin è obbligato a cambiarle. |
| `EFFORT_TRACKING_USER_DELETE_GRACE_DAYS` | `30` | Giorni di attesa prima che un utente disabilitato sia eliminabile. |
| `EFFORT_TRACKING_SESSION_SAMESITE` / `EFFORT_TRACKING_SESSION_SECURE` | `lax` / `false` | Sicurezza cookie di sessione (in produzione dietro TLS: `true`). |
| `EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS` | `1800` | Durata massima sessione in secondi (30 min). Se l'utente chiude il browser senza logout, alla scadenza serve rilogin. |
| `EFFORT_TRACKING_MAX_BODY_BYTES` | `1048576` (1 MiB) | Limite massimo del body delle richieste. |

Il file `.env` reale **non** va committato (è coperto da `.gitignore`).

---

## Deploy in produzione (Ubuntu + systemd)

Ci sono due strade: **script automatizzato** (consigliata) o **passi manuali**.

### Opzione A — Script automatizzato `deploy.sh`

Lo script `deploy.sh` (root del repo) automatizza: creazione utente/directory/venv, copia del
codice, generazione di `/etc/efftrack.env` e installazione del servizio systemd.

```bash
sudo ./deploy.sh           # deploy completo (consigliato)
# oppure in step separati:
sudo ./deploy.sh --install # solo installazione (venv + dipendenze + copia)
sudo ./deploy.sh --env     # solo generazione /etc/efftrack.env
sudo ./deploy.sh --service # solo installazione/avvio del servizio systemd
sudo ./deploy.sh --help    # aiuto
```

Lo script genera una `SECRET_KEY` robusta e crea `/etc/efftrack.env` con valori sicuri.
**CAMBIA la password admin** (`EFFORT_TRACKING_ADMIN_PASSWORD`) prima di andare in produzione.
La password admin è **temporanea**: viene letta solo al primo seed (tabella `users` vuota) e
hashata nel DB. Al primo login l'admin è reindirizzato a `/profile` e **deve** cambiarla prima
di poter navigare (stessa regola vale per i nuovi utenti creati dall'admin: la password impostata
in fase di creazione è temporanea e va cambiata al primo accesso).

### Opzione B — Passi manuali

Il template dell'unità systemd è in [`systemd/efftrack.service`](./systemd/efftrack.service).
Viene documentato in testa al file; in sintesi:

```bash
sudo cp systemd/efftrack.service /etc/systemd/system/efftrack.service
sudo useradd --system --home /opt/efftrack --shell /usr/sbin/nologin efftrack
sudo mkdir -p /opt/efftrack
sudo chown -R efftrack:efftrack /opt/efftrack
# copia il codice in /opt/efftrack (es. rsync), crea il venv e installa le dipendenze
sudo cp .env.example /etc/efftrack.env   # poi personalizza (vedi config)
sudo systemctl daemon-reload
sudo systemctl enable --now efftrack.service
sudo systemctl status efftrack.service
sudo journalctl -u efftrack -f            # log
```

> **Nota**: il template usa `--host 127.0.0.1` perché in produzione si usa un **reverse proxy**
> (nginx/Caddy) davanti a Uvicorn. I log escono su **journald**.

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

- **107 test**: `tests/test_models.py` (modelli, seed, validazione, segregazione) +
  `tests/test_functional.py` (test end-to-end HTTP su route, auth, permessi, CRUD, export).
- I test usano un database SQLite **dedicato e isolato** (non toccano `data/efftrack.db`).

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
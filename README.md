# Effort Tracking

Web server per la registrazione di **effort** (ore lavorate, attività giornaliere, note) con
piccolo gestionale CRUD. Sostituto moderno del vecchio tool aziendale, pensato per essere
installato su **Ubuntu** con **Python `venv`** (no Docker).

> Stato corrente: **Fase 0 — Bootstrap**. Server di test raggiungibile, health check attivo.
> La documentazione di stato è in [`memory-bank/`](./memory-bank/).

---

## Requisiti

- Ubuntu (testato su 22.04 LTS) o qualunque distribuzione con Python ≥ 3.10.
- `python3`, `python3-venv`, `python3-pip`.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

---

## Installazione

```bash
cd /home/mbocchini/efftrack
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Avvio in sviluppo

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoint disponibili:

- `http://localhost:8000/` — pagina di benvenuto.
- `http://localhost:8000/health` — health check (status app + check DB).
- `http://localhost:8000/docs` — documentazione OpenAPI generata da FastAPI.

## Configurazione

Tutte le impostazioni sono sovrascrivibili via variabili d'ambiente. Vedi
[`.env.example`](./.env.example) per l'elenco completo.

```bash
cp .env.example .env
# modifica .env a piacere
```

Il file `.env` reale **non** va committato (è coperto da `.gitignore`).

## Deploy in produzione (Ubuntu + systemd)

Un template di unit file è fornito in [`systemd/efftrack.service`](./systemd/efftrack.service).
**Non viene attivato automaticamente**: è solo un documento pronto all'uso.

I passi consigliati sono descritti in testa al file stesso; in sintesi:

```bash
sudo cp systemd/efftrack.service /etc/systemd/system/efftrack.service
sudo useradd --system --home /opt/efftrack --shell /usr/sbin/nologin efftrack
sudo mkdir -p /opt/efftrack
sudo chown -R efftrack:efftrack /opt/efftrack
sudo cp .env.example /etc/efftrack.env   # poi personalizza
sudo systemctl daemon-reload
sudo systemctl enable --now efftrack.service
sudo systemctl status efftrack.service
```

⚠️ **Nota di binding**: il template `ExecStart` usa `--host 127.0.0.1` perché in
produzione ci si attende un reverse proxy davanti (nginx/Caddy). Per test locali
su Ubuntu puoi modificare temporaneamente a `0.0.0.0`.

## Struttura del progetto

```
efftrack/
├── app/                # codice applicativo (FastAPI)
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── routers/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── models/
│   ├── core/
│   ├── templates/
│   └── static/
├── systemd/            # template service (NON attivato)
├── data/               # SQLite (gitignored)
├── tests/
├── memory-bank/        # documentazione persistente
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── VERSION
```

## Workflow del progetto

Il progetto segue una roadmap in 12 fasi. **Ogni fase si considera completata solo
dopo conferma esplicita dell'utente**: niente commit funzionale, niente bump di
versione, niente tag finché non arriva il "ok". Lo stato è sempre riflesso in
[`memory-bank/activeContext.md`](./memory-bank/activeContext.md) e
[`memory-bank/progress.md`](./memory-bank/progress.md).

## Licenza

Da definire.

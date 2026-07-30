# Service Architecture Rules

## Struttura dei Servizi
- **Servizio iniziale:** un singolo servizio web dedicato all'effort tracking.
- **Architettura consigliata:** pacchetto Python separato con `main.py`, `routes.py`, `config.py`, `database.py`, `schemas.py`, `services.py`.
- **Router:** usare `APIRouter(prefix="")` per la root app e prefissi espliciti per eventuali moduli futuri (`/auth`, `/exports`, `/admin`, `/api`).
- **Endpoint:** mantenere distinzione chiara tra pagine HTML e API/azioni di backend.

## Host e Binding
- **Sviluppo:** bindare `0.0.0.0` per accessibilità da rete locale, WSL o VM.
- **Produzione:** bindare sull'IP della VM o su localhost dietro reverse proxy, secondo il contesto.
  - Trovarlo con: `ip a | grep inet`
  - Modificare `--host` nel comando uvicorn o nel servizio systemd
- **Porta dedicata:** usare una porta esplicita configurabile via env var, ad esempio `EFFORT_TRACKING_PORT`.
- I docstring o README di esecuzione devono mostrare una sintassi shell chiara con env var configurabili.
- Quando viene creato il servizio, **annotare nella chat** che in produzione va rivisto il binding, indicando file e riga precisi.

## Static Files (CSS/JS condivisi)
- File statici dell'app vanno in `static/` del progetto oppure in un path condiviso già presente nell'infrastruttura.
- I template devono preferire file CSS/JS condivisi e riusabili.
- **Non duplicare CSS inline** se la stessa regola esiste già nello shared CSS.

## Reverse Proxy
- Se si prevede uso di Caddy o Nginx, separare chiaramente applicazione e proxy.
- Il file del reverse proxy può anche non far parte del repository, ma ogni modifica necessaria deve:
1. Essere **segnalata esplicitamente in chat** all'utente.
2. Essere **annotata in `memory-bank/activeContext.md`** con la modifica precisa.
3. Essere documentata con istruzioni replicabili a mano in produzione.

## Health Check
- Raccomandato il path `/health` (GET).
- Deve restituire almeno stato applicazione e controllo base della connettività al database.

# Python Style Rules

## Stile di Codice
- **Docstring:** stile descrittivo semplice, prima riga breve, poi eventuali dettagli operativi.
- **Type hints:** sempre presenti sulle firme delle funzioni. Usare `X | None` (Python 3.10+) o `Optional[X]` dove più chiaro.
- **Pattern FastAPI:** preferire `lifespan` pattern (`asynccontextmanager`) per init/shutdown.
- **Router:** usare `APIRouter(prefix="...")` per organizzare le routes.
- **Configurazione:** centralizzare env vars e costanti applicative in moduli dedicati (`config.py`, `settings.py` o equivalente).
- **Validazioni:** usare modelli Pydantic per input/output quando si espongono API o form model strutturati.

## Regola di Progetto — Effort Tracking
- **Scelta preferita:** FastAPI come framework principale, salvo controindicazioni motivate.
- **Template engine:** Jinja2 server-side come default per la UI.
- **Interattività:** vanilla JavaScript per comportamento form/tabella; evitare SPA nelle prime fasi.
- **Business logic:** separare logica di persistenza, logica di validazione e logica di rendering.

## Architettura Servizi
- **Servizio iniziale:** un singolo servizio web dedicato all'effort tracking.
- **Router root:** `APIRouter(prefix="")` per la root; prefissi espliciti per moduli futuri (`/auth`, `/exports`, `/admin`, `/api`).
- **Endpoint:** distinzione chiara tra pagine HTML e API/azioni di backend.

## Host e Binding
- **Sviluppo:** bindare `0.0.0.0` per accessibilità da rete locale, WSL o VM.
- Quando viene creato il servizio, **annotare nella chat** che in produzione va rivisto il binding, indicando file e riga precisi.

## Health Check
- Raccomandato il path `/health` (GET).
- Deve restituire almeno stato applicazione e controllo base della connettività al database.

## Sovrascrivibilità
Se per una funzionalità specifica un altro stile è più adatto (es. classi invece di funzioni, SQLAlchemy invece di SQLite diretto), proporre con analisi pro/contro. Non c'è una regola fissa che impone uno stile unico per tutto.

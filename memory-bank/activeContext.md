# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 1 ✅ (2026-07-31).
- **Fase in corso**: nessuna. In attesa di task per la Fase 2.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.1.1` (tag `v0.1.1` annotato su `develop`).
- **Riepilogo chiusura Fase 1**: refactor routing completato e verificato su `127.0.0.1:8000`. Bump `VERSION` `0.1.0` → `0.1.1`, commit `refactor(routing): phase 1 web router extraction` su `develop`, tag `v0.1.1`. Convenzione di porta operativa (verifiche su 8000, kill di chi occupa) annotata qui sotto e rispettata da qui in avanti.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: struttura CSS variabili presente da Fase 2; toggle dark/light rimandato a Fase 9.
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro futuro va su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Niente replica in `__init__.py` (regola rimossa a fine Fase 0 su decisione utente). Bump confermato a `0.1.1` per la Fase 1.
- **Memory bank**: aggiornato a ogni cambio di stato di fase.

## Modifiche di Fase 1 (refactor)
- **Refactor routing**: le route `GET /` e `GET /health` sono state spostate da `app/main.py` a `app/routers/web.py` come `APIRouter(tags=["web"])`. Le route mantengono `name="index"` e `name="health"` per non rompere reverse proxy e link futuri.
- **Nuovo router API**: `app/routers/api.py` creato come `APIRouter(prefix="/api", tags=["api"])` (vuoto, predisposizione per future API JSON).
- **`app/main.py` snellito**: contiene solo creazione app, lifespan, mount static, `include_router` per i due router. Niente più route inline.
- **`app/config.py` esteso**: aggiunti `TEMPLATES_DIR` e `STATIC_DIR` calcolati da `BASE_DIR`, eliminando i path "magic" sparsi in `main.py`.
- **Comportamento osservabile invariato**: stessi URL, stesse risposte, stessi content-type. Il refactor è puramente strutturale.

## Verifiche tecniche di Fase 1 (curl)
Eseguito Uvicorn locale su `127.0.0.1:8001` e curl sui 4 endpoint chiave:
- `GET /` → **HTTP 200**, `text/html; charset=utf-8`, 1424 byte. Pagina renderizzata correttamente con titolo `Effort Tracking — Fase 1 — Pagina HTML statica raggiungibile`, link a `/health` e `/docs` presenti.
- `GET /health` → **HTTP 200**, JSON `{"app":"Effort Tracking","version":"0.1.0","status":"ok","db":"ok"}`.
- `GET /docs` → **HTTP 200**, `text/html; charset=utf-8` (OpenAPI UI).
- `GET /static/style.css` → **HTTP 200**, `text/css; charset=utf-8`.

Tutti i codici e i content-type sono quelli attesi. Niente regressioni rispetto alla Fase 0.

## Separazione backend / frontend (Fase 1)
- **Area applicativa**: refactor di `app/main.py`, nuovi `app/routers/web.py` e `app/routers/api.py`, estensione di `app/config.py`.
- **Area UI**: nessuna modifica (nessun file template/CSS/JS toccato, la pagina di benvenuto resta invariata).
- **Area documentale**: aggiornamento `activeContext.md` e `progress.md`.

## Verifiche Fase 1 (rivalidazione su porta canonica 8000)
Su richiesta dell'utente, la verifica è stata rifatta sulla porta canonica `127.0.0.1:8000` invece della `8001` usata per la prima tornata. Esito:
- `GET /` → **HTTP 200**, `text/html; charset=utf-8`, content-length 1424.
- `GET /health` → **HTTP 200**, `{"app":"Effort Tracking","version":"0.1.0","status":"ok","db":"ok"}`.
- `GET /docs` → **HTTP 200**, `text/html; charset=utf-8`.
- `GET /static/style.css` → **HTTP 200**, `text/css`.
- `pgrep -af uvicorn` mostra il processo `24737` in ascolto su `127.0.0.1:8000`.

## Convenzione operativa: porta di sviluppo (decisa in Fase 1)
- **Porta canonica del progetto**: `8000` (default in `app/config.py`).
- **Verifiche automatiche di Cline**: sempre su `127.0.0.1:8000` (o `0.0.0.0:8000` se serve accesso da rete). Niente porte alte usa-e-getta.
- **Se la 8000 è occupata** (anche da un mio processo precedente rimasto appeso, da un browser ancora aperto, o da un'istanza di test), Cline **uccide il processo** e riavvia. In sviluppo non si tengono in piedi istanze fantasma.
- **La regola vale da qui in avanti** per tutte le fasi successive. Decisione utente 2026-07-31.

## Regola operativa attiva (workflow)
1. Implemento la fase corrente.
2. Eseguo verifiche tecniche interne (curl, lettura file, struttura).
3. **Mi fermo** e non marco la fase come completata.
4. L'utente fa le sue verifiche.
5. **Solo dopo conferma esplicita** dell'utente: aggiorno `progress.md` e `activeContext.md`, eseguo bump `VERSION` + commit su `develop` + tag annotato.

## Decisione speciale di Fase 0 (eccezione una tantum)
- L'utente ha autorizzato esplicitamente un commit iniziale su `main` per depositare la base funzionante del progetto. Subito dopo è stato creato il branch `develop`. Da qui in avanti `main` non viene più toccato senza autorizzazione esplicita nel messaggio corrente.

## Prossima fase (Fase 1)
- In pratica la pagina HTML di benvenuto è già in piedi dalla Fase 0 (`/` → 200 OK, `/health` → JSON con status/db ok, `/docs` → OpenAPI).
- In Fase 1 consolidiamo la raggiungibilità e documentiamo nel memory bank i risultati. Non si introducono nuove funzionalità: serve da "spartitraffico" prima della Fase 2 (layout statico stile effort tracking).

## Rischi / punti aperti
- Tema dark/light rimandato a Fase 9 (accettato come debito temporaneo).
- Migrazioni schema: `ALTER TABLE` a startup invece di Alembic fino a Fase 9 (se la complessità cresce, si introduce Alembic).
- Nessun test automatico in Fase 0.
- `user_id` presente come colonna nullable dal momento dell'introduzione della tabella `effort_entries` (Fase 4), ma non valorizzato fino a Fase 11.

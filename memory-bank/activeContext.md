# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 2 ✅ (2026-07-31).
- **Fase in corso**: nessuna. In attesa di task per la Fase 3.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.2.0` (tag `v0.2.0` annotato su `develop`).
- **Nota ambiente**: in questa sessione è stato ricreato il `.venv` su un nuovo OS (Python 3.12.3, pip 24.0). Dipendenze installate: fastapi 0.141.1, uvicorn 0.52.0, sqlalchemy 2.0.51, pydantic 2.13.4, jinja2 3.1.6, python-multipart 0.0.32.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: struttura CSS variabili presente; toggle dark/light rimandato a Fase 9.
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Bump confermato a `0.2.0` per la Fase 2 (MINOR: nuova funzionalità UI).
- **Import di `Engine`**: notato `from sqlalchemy.engine import Engine` in `app/routers/web.py` non usato (potrebbe essere legacy). Da verificare/ripulire in un refactor futuro.

## Modifiche di Fase 2 (layout statico stile effort tracking)
- **`app/templates/base.html`**: aggiunta icona utente decorativa (SVG sagoma persona) nell'header in alto a destra, come placeholder per il futuro login (Fase 10). Wrapper `.app-header__actions` con fase + icona.
- **`app/templates/index.html`**: sostituita la welcome card con il layout reale a due sezioni:
  - Form di inserimento (card `.form-card`) con campi User, Data, Cliente, Gruppo, Attività, Ore Spese, Note, Descrizione + pulsante Salva centrale.
  - Tabella elenco (card `.records-card`) con header a 7 colonne (Data, Cliente, Gruppo, Attività, Ore, Note, Descrizione), contatore `({{ records|length }} record)` e stato vuoto "Nessuna registrazione presente."
  - Il campo **Descrizione** è sempre visibile in Fase 2; lo show/hide condizionale per "Supporto Specialistico" arriva in Fase 3.
- **`app/static/style.css`**: rimosse le regole della welcome card (Fasi 0/1), aggiunte regole per form card, form grid a 2 colonne responsive (breakpoint 720px), input/select/textarea con focus ring blu navy, pulsante Salva primario (.btn-primary), tabella con header blu navy, righe alternate e hover, messaggio vuoto. Tutto basato sulle variabili CSS esistenti.
- **`app/routers/web.py`**: aggiornata label di fase a "Fase 2 — Layout statico stile effort tracking", aggiunto `records: []` nel context (predisposizione Fase 6).
- **`app/config.py`**: `APP_VERSION` aggiornata da `0.1.0` a `0.2.0` — corretta una discrepanza rimasta dalla Fase 1 (il file VERSION era già a `0.1.1` mentre config restava `0.1.0`).

## Verifiche tecniche di Fase 2 (curl su 127.0.0.1:8000)
- `GET /` → **HTTP 200**, `text/html; charset=utf-8`, 4949 byte. Struttura verificata: titolo "Fase 2 — Layout statico stile effort tracking", 7 `<th scope="col">` corretti, messaggio "Nessuna registrazione presente", conteggio `(0 record)`, icona utente `.app-header__user-icon`, placeholder Descrizione "Obbligatoria per l'attività Supporto Specialistico".
- `GET /health` → **HTTP 200**, `{"app":"Effort Tracking","version":"0.2.0","status":"ok","db":"ok"}`.
- `GET /static/style.css` → **HTTP 200**, `text/css; charset=utf-8`.
- `GET /docs` → **HTTP 200**, `text/html; charset=utf-8`.

Tutti i codici e i content-type sono quelli attesi. Niente regressioni.

## Separazione backend / frontend (Fase 2)
- **Area UI**: `base.html` (icona utente), `index.html` (form + tabella), `style.css` (nuove regole).
- **Area applicativa**: `web.py` (label fase + context records), `config.py` (APP_VERSION).
- **Area documentale**: aggiornamento `activeContext.md` e `progress.md`.

## Convenzione operativa: porta di sviluppo (decisa in Fase 1)
- **Porta canonica del progetto**: `8000` (default in `app/config.py`).
- **Verifiche automatiche di Cline**: sempre su `127.0.0.1:8000` (o `0.0.0.0:8000` se serve accesso da rete).
- **Se la 8000 è occupata**, Cline uccide il processo e riavvia.
- Regola valida per tutte le fasi successive. Decisione utente 2026-07-31.

## Regola operativa attiva (workflow)
1. Implemento la fase corrente.
2. Eseguo verifiche tecniche interne (curl, lettura file, struttura).
3. **Mi fermo** e non marco la fase come completata.
4. L'utente fa le sue verifiche.
5. **Solo dopo conferma esplicita** dell'utente: aggiorno `progress.md` e `activeContext.md`, eseguo bump `VERSION` + commit su `develop` + tag annotato.

## Decisione speciale di Fase 0 (eccezione una tantum)
- L'utente ha autorizzato esplicitamente un commit iniziale su `main` per depositare la base funzionante. Subito dopo è stato creato il branch `develop`. Da qui in avanti `main` non viene più toccato senza autorizzazione esplicita nel messaggio corrente.

## Prossima fase (Fase 3)
- **Form interattivo con lookup hardcoded**:
  - Dropdown reali (già presenti come hardcoded in Fase 2).
  - Show/hide condizionale del campo **Descrizione** quando l'attività selezionata è "SOC-Supporto Specialistico".
  - Validazioni base client-side.
  - Primo JavaScript vanilla (`static/*.js`).

## Rischi / punti aperti
- Tema dark/light rimandato a Fase 9 (accettato come debito temporaneo).
- Migrazioni schema: `ALTER TABLE` a startup invece di Alembic fino a Fase 9.
- Nessun test automatico fino a Fase 4.
- `user_id` presente come colonna nullable dal momento dell'introduzione della tabella `effort_entries` (Fase 4), non valorizzato fino a Fase 11.
- Import `Engine` non usato in `app/routers/web.py` (da ripulire in refactor futuro).
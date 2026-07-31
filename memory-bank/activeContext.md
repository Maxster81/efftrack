# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 3 ✅ (2026-07-31).
- **Fase in corso**: nessuna. In attesa di task per la Fase 4.
- **Stato**: idle, pronto per nuovo task.
- **Versione corrente**: `0.3.0` (tag `v0.3.0` annotato su `develop`).
- **Nota ambiente**: sviluppo su **Ubuntu in WSL** (Python 3.12.3, pip 24.0). Venv ricreato in questa macchina. Dipendenze: fastapi 0.141.1, uvicorn 0.52.0, sqlalchemy 2.0.51, pydantic 2.13.4, jinja2 3.1.6, python-multipart 0.0.32.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: struttura CSS variabili presente; toggle dark/light rimandato a Fase 9.
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Bump confermato a `0.3.0` per la Fase 3 (MINOR: nuova funzionalità).
- **Campo User**: scrivibile nelle fasi pre-auth (intenzionale, per "firmare" i record senza login). In Fase 10 diventerà read-only derivato dalla sessione. Nota in `productContext.md`.
- **Etichetta descrizione**: rinominata in **"Descrizione attività"** per coerenza col vecchio tool.
- **Note**: campo **opzionale** (mai obbligatorio). **Descrizione attività**: obbligatoria **solo** quando l'attività è "SOC-Supporto Specialistico" (campo visibile). Chiarimento utente in Fase 3.
- **Bind server**: in sviluppo bind su `0.0.0.0` (accessibile da browser Windows via rete WSL). Verificato efficace in Fase 3 (richieste ricevute da IP host 172.20.144.1).
- **Import di `Engine`**: notato `from sqlalchemy.engine import Engine` in `app/routers/web.py` non usato (potrebbe essere legacy). Da verificare/ripulire in un refactor futuro.

## Modifiche di Fase 3 (form interattivo con lookup hardcoded)
- **`app/static/form.js`** (NUOVO): JavaScript vanilla con:
  - **Show/hide** del campo "Descrizione attività": visibile solo se Attività = "SOC-Supporto Specialistico"; all'avvio nascosto.
  - **Validazione client-side** al submit: User, Data, Cliente, Gruppo, Attività, Ore Spese obbligatori; Ore 0.25..24 step 0.25 (gestisce virgola). Descrizione attività obbligatoria solo se visibile. Note mai obbligatoria.
  - Errori: classe `.is-invalid` sui campi, banner `#form-error role="alert"`, focus sul primo campo non valido; reset errore su input/change.
- **`app/static/style.css`**: aggiunte `.is-hidden`, `.form-group.is-invalid *`, `.form-error`. Nessuna modifica alle regole esistenti.
- **`app/templates/index.html`**: area errore `#form-error` (hidden); label form e `<th>` tabella rinominati "Descrizione attività"; gruppo Descrizione inizialmente `is-hidden`; `novalidate` sul form (validazione gestita da JS); incluso `form.js` con `defer`.
- **`app/templates/base.html`**: aggiunto blocco `{% block scripts %}` prima di `</body>`.

## Verifiche Fase 3 (curl su 0.0.0.0:8000 e browser)
- Riavvio server su `0.0.0.0:8000` (corretto binding da 127.0.0.1 → 0.0.0.0).
- `GET /` → 200 `text/html` (5155 byte); `GET /health` → 200 `version:0.3.0`; `GET /static/form.js` → 200 `text/javascript`; `GET /static/style.css` → 200 `text/css`.
- Log server: richieste da IP host Windows (172.20.144.1) con 200 — raggiungibilità da browser confermata.
- **Verifica utente (browser)**: (1) submit a vuoto → warning e campi evidenziati; (2) "Supporto Specialistico" → compare "Descrizione attività"; (3) compilato completo + Salva → "method not allowed" (atteso, nessun POST reale fino a Fase 5).

## Separazione backend / frontend (Fase 3)
- **Area UI**: `form.js` (nuovo), `style.css`, `index.html`, `base.html`.
- **Area applicativa**: nessuna modifica (nessun POST reale).
- **Area documentale**: aggiornamento `activeContext.md`, `progress.md`.

## Convenzione operativa: porta e binding (aggiornata in Fase 3)
- **Porta canonica**: `8000`.
- **Binding in sviluppo**: `0.0.0.0` (per raggiungibilità da rete/WSL/browser Windows). Niente binding su 127.0.0.1 in dev.
- **Se la 8000 è occupata**: uccidere il processo e riavviare.
- **Ambiente**: Ubuntu in WSL, niente display grafico; niente `xdg-open`/`open`. Per verifiche visive l'utente apre `http://localhost:8000/` nel browser Windows. Tool CLI standard solo (`curl`, `pgrep`, `pkill`, `git`). Dettagli in `techContext.md`.

## Regola operativa attiva (workflow)
1. Implemento la fase corrente.
2. Eseguo verifiche tecniche interne (curl, lettura file, struttura).
3. **Mi fermo** e non marco la fase come completata.
4. L'utente fa le sue verifiche.
5. **Solo dopo conferma esplicita** dell'utente: aggiorno `progress.md` e `activeContext.md`, eseguo bump `VERSION` + commit su `develop` + tag annotato.

## Decisione speciale di Fase 0 (eccezione una tantum)
- L'utente ha autorizzato esplicitamente un commit iniziale su `main` per depositare la base funzionante. Subito dopo è stato creato il branch `develop`. Da qui in avanti `main` non viene più toccato senza autorizzazione esplicita nel messaggio corrente.

## Prossima fase (Fase 4)
- **Database e seed lookup**:
  - SQLAlchemy + SQLite (WAL + foreign keys già configurati in `app/db.py`).
  - Tabelle lookup: `clients`, `groups`, `activities` (con `requires_description BOOL`).
  - Tabella `effort_entries` (con `user_id` nullable FK, ready per Fase 11).
  - Seed iniziale: INAIL, MDS; GRUPPO SOC; SOC-Conduzione (no desc via), SOC-Supporto Specialistico (sì desc via).
  - Predisposizione per i test automatici (da Fase 4 in poi).
  - I dropdown hardcoded della Fase 3 verranno sostituiti dal contenuto del DB.

## Rischi / punti aperti
- Tema dark/light rimandato a Fase 9 (accettato come debito temporaneo).
- Migrazioni schema: `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE` controllato a startup fino a Fase 9; Alembic proposto se cresce la complessità.
- Nessun test automatico finora (previsti da Fase 4).
- `user_id` nullable in `effort_entries` dal suo inserimento, valorizzato in Fase 11.
- Import `Engine` non usato in `app/routers/web.py` (da ripulire in refactor futuro).
- POST "method not allowed" al submit del form: atteso, sarà implementato in Fase 5.
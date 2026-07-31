# Active Context — Effort Tracking

## Stato corrente
- **Ultima fase completata**: Fase 0 ✅ (2026-07-31).
- **Fase in corso**: **Fase 1** — Pagina HTML statica raggiungibile. Non ancora avviata, in attesa di task.
- **Stato**: idle. Pronto per Fase 1 o per un nuovo task.

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite.
- **Palette UI**: blu navy + grigi neutri (variabili CSS in `:root`, predisposte per dark/light futuri).
- **Tema**: struttura CSS variabili presente da Fase 2; toggle dark/light rimandato a Fase 9.
- **Struttura**: repo unico con layout modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Systemd**: template `efftrack.service` creato in Fase 0 ma non attivato.
- **Branching**: `main` intoccato salvo autorizzazione esplicita. Tutto il lavoro futuro va su `develop`.
- **Versioning**: SemVer, file `VERSION` (unico). Niente replica in `__init__.py` (regola rimossa a fine Fase 0 su decisione utente).
- **Memory bank**: aggiornato a ogni cambio di stato di fase.

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

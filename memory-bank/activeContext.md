# Active Context — Effort Tracking

## Stato corrente
- **Fase in corso**: nessuna. **Progetto completo alla v1.0.0** (versione stabile pronta per produzione).
- **Stato**: idle, pronto per eventuali evoluzioni future.
- **Versione corrente**: `1.0.0` (bump MAJOR per rilascio finale, Fase 14 chiusa).
- **Fasi complete**: 0–13d e 14 tutte completate. Hardening (13d) e audit di documentazione sono ora su richiesta (vedi `.clinerules/09-post-change.md`).
- **Issue chiuse in Fase 14**: I (systemd già corretto), J (health pubblico), K (timeout — nessuna azione), L (middleware body limit), M (deploy.sh), H (test funzionali pytest+HTTPX).
- **DB di sviluppo**: dataset multi-gruppo (2 gruppi SOC/NOC, 6 utenti di test, ~20 record ciascuno, password `test`). Admin utente di sola gestione (group_id NULL).
- **Merge su `main`**: autorizzato solo in Fasi 9 e 9b (v0.12.0). Tutte le fasi 10+ sono solo su `develop`.
- **Ambiente**: Ubuntu in WSL, Python 3.12.3, venv ricreato. Dipendenze: fastapi 0.141.1, uvicorn 0.52.1, sqlalchemy 2.0.51, pydantic 2.13.4 (pydantic-core 2.46.4), jinja2 3.1.6, python-multipart 0.0.32, python-dotenv 1.2.2, pytest 9.1.1 (dev), httpx 0.28.1 (dev). `pydantic-core` 2.47.0 NON adottato (incompatibile).

## Cronologia fasi completate (riepilogo)
| Fase | Versione | Commit (riassunto) |
|------|----------|---------------------|
| 0 Bootstrap | v0.1.0 | chore(bootstrap): scaffolding |
| 1 Pagina statica | v0.1.1 | refactor(routing): web router |
| 2 Layout statico | v0.2.0 | feat(ui): static layout |
| 3 Form interattivo | v0.3.0 | feat(ui): interactive form |
| 4 DB e seed | v0.4.0 | feat(db): schema + seed |
| 4b Sidebar hamburger | v0.5.0 | feat(ui): sidebar |
| 5 Salvataggio | v0.6.0 | feat(db): save entry |
| 5b Copia settimana | v0.7.0 | feat(db): bulk week |
| 6 Elenco record | v0.8.0 | feat(ui): records list |
| 7 Select/update/delete | v0.9.0 | feat(db): record CRUD |
| 8 Export CSV | v0.10.0 | feat(db): csv export |
| 9 Refactor/logging/env | v0.11.0 | feat(core): logging dotenv |
| 9b Toggle dark/light | v0.12.0 | feat(ui): theme toggle |
| 10 Autenticazione | v0.13.0 | feat(auth): local auth |
| 11 Multiutente | v0.14.0 | feat(multiuser): segregation |
| 12a Ruoli/permessi | v0.15.0 | feat(auth): roles infra |
| 12b Ruolo USER | v0.16.0 | feat(roles): user role |
| 12c Ruolo MANAGER | v0.17.0 | feat(role): manager |
| 12d Ruolo ADMIN | v0.18.0 | feat(admin): panel |
| 13a Admin extra | v0.19.0 | feat(admin): disable+group |
| 13b Sicurezza | v0.20.0 | feat(security): headers |
| 13c Fix stile/UX | v0.21.0 | feat(ui): style/ux fixes |
| S8 Eliminazione utente | v0.22.x | feat(admin): delete grace |
| S9 Tab lookup | v0.22.4 | style(ui): lookup tabs |
| Profilo utente | v0.23.0 | feat(profile): user data |
| Restyle header | v0.23.2 | style(ui): header grid |
| 13d Hardening | v0.23.3 | fix(security): hardening |
| 14 Issue L+M | v0.24.0 | feat(security): body limit + deploy.sh |
| Fase 14 Issue H | v0.24.2 | test(functional): e2e pytest+HTTPX |
| Fase 14 chiusura | v1.0.0 | chore(release): bump to v1.0.0 — Fase 14 completata |

## Decisioni recenti
- **Stack**: FastAPI + Jinja2 + SQLAlchemy 2.x + SQLite (WAL + FK).
- **Tema**: toggle dark/light (Fase 9b), preferenza `theme-preference` in localStorage.
- **Struttura**: repo unico modulare (`app/{routers,services,repositories,schemas,models,core}`).
- **Branching**: tutto su `develop`; `main` intoccato senza autorizzazione esplicita nel messaggio corrente.
- **Versioning**: SemVer, file `VERSION` unico, tag annotato `vX.Y.Z` a ogni commit funzionale.
- **Modello dati**: lookup solo `name` UNIQUE; `effort_entries` senza `user_text` (FK su users); mese mai persistito (derivato da data); campo User forzato lato server dopo Fase 10.
- **Regola aziendale**: nessuno (nemmeno admin) modifica/elimina record altrui.
- **Sessione**: HTTP firmata (SessionMiddleware) con `SameSite`/`https_only` configurabili (Fase 13d).
- **Logging**: `setup_logging()` nel lifespan, livello da env, formato console/journald.
- **Config**: `config.py` + `load_dotenv()`; in produzione systemd `EnvironmentFile`.
- **Test funzionali (Issue H)**: `tests/conftest.py` configura un DB SQLite su file (isolato da `data/efftrack.db`) impostando `EFFORT_TRACKING_DB_URL` PRIMA dell'import dei moduli app.*; `tests/test_functional.py` usa TestClient (HTTPX). Nota: con `expire_on_commit=False` va chiamato `db_session.expire_all()` prima di rileggere oggetti modificati dal thread del TestClient.

## Fasi successive
- **Progetto completo**: tutte le fasi (0–13d, 14) concluse. Eventuali evoluzioni future (vedi `Issue-Suggestion.md`: S10, S11, S4, S6, S9) restano backlog opzionale, non assegnate a fasi correnti.

## Fase 14 — Attività chiuse (2026-08-04)
- **Issue I**: service systemd già corretto (EnvironmentFile=/etc/efftrack.env, nessuna variabile hardcodata). Verificato.
- **Issue J**: `/health` già pubblico (nessuna dependency auth in `web.py:602`). Verificato.
- **Issue K**: timeout export valutato — Uvicorn senza timeout request, export CSV è StreamingResponse. Nessuna azione necessaria.
- **Issue L**: nuovo `RequestBodyLimitMiddleware` (`app/core/body_limit.py`), registrato in `main.py`. Soglia `EFFORT_TRACKING_MAX_BODY_BYTES` (default 1 MiB) in `config.py` + `.env.example`.
- **Issue M**: nuovo `deploy.sh` opzionale (venv, copia codice, `/etc/efftrack.env`, servizio systemd). Allineato al path `.venv`.
- **Issue H**: nuova suite `tests/test_functional.py` (26 test) + `tests/conftest.py`; dipendenza dev `httpx` in `requirements-dev.txt`. Copertura: `/health` pubblico, auth (login/logout/account disabilitato/redirect anonimi), CRUD record via form, regola aziendale (niente update/delete su record altrui), export CSV segregato per utente + filtro mese, permessi di ruolo (USER/MANAGER/ADMIN), vista gruppo manager e relativo export, profilo e cambio password. **104 test totali verdi.**
- **Chiusura Fase 14 (v1.0.0)**: README riscritto per intero (stato v1.0.0, funzionalità, config, deploy `deploy.sh` e manuale, note PostgreSQL, test). Bump MAJOR a `1.0.0` (VERSION + `config.py`). Memory bank allineato.

## Rischi / punti aperti
- `Issue-Suggestion.md`: non restano issue aperte in Fase 14. Future Features (backlog): S10 (self-creation), S11 (password obbligatoria al primo login), S4 (filtro anno+mese), S6 (giorno ferie), S9 (refine lookup tabellare).
- Password admin `admin/admin`: da cambiare in produzione via env var (Sicurezza Fase 14).
- `SECRET_KEY` placeholder di sviluppo: obbligatoria robusta in produzione.
- `pydantic-core` pinnato a 2.46.4 (compatibilità pydantic 2.13.4).
- Migrazioni schema: `run_schema_migrations` gestisce modifiche note; per cambi non gestiti va rigenerato il DB. Alembic da valutare.
- Cancellazione record **permanente** senza soft-delete/audit (da valutare in futuro).
- Il `.env` reale in produzione è sostituito da `/etc/efftrack.env` (systemd).
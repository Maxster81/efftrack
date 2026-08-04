# Progress — Effort Tracking

## Stato globale
- **Fase in corso**: nessuna. **Progetto completo alla v1.1.0** (versione stabile pronta per produzione).
- **Stato**: idle, pronto per eventuali evoluzioni future.
- **Versione corrente**: `1.1.0` (bump MINOR — cambio password obbligatorio al primo login, S11).
- **Fasi complete**: 0–13d e 14 tutte completate. Vedi `activeContext.md` per la cronologia compatta versione/commit.
- **Fase 14 chiusa** (2026-08-04): produzione e documentazione conclusa. Vedi sotto e Issue-Suggestion.md.

> **⚠️ NOTA OPERATIVA — Issue e Suggerimenti:** le issue/suggestion sono tracciate **esclusivamente** in `memory-bank/Issue-Suggestion.md`. Consultarlo a inizio ogni fase; le voci risolte vanno **rimosse** lì nello stesso commit che le risolve.

## Roadmap completa (stato)
| Fase | Stato |
|------|-------|
| 0 Bootstrap | ✅ |
| 1 Pagina statica | ✅ |
| 2 Layout statico | ✅ |
| 3 Form interattivo | ✅ |
| 4 Database e seed lookup | ✅ |
| 4b Sidebar hamburger | ✅ |
| 5 Salvataggio record | ✅ |
| 5b Copia su settimana | ✅ |
| 6 Elenco record + filtro mese | ✅ |
| 7 Select/update/delete | ✅ |
| 8 Export CSV | ✅ |
| 9 Refactor, logging, env, systemd | ✅ |
| 9b Toggle dark/light + deps | ✅ |
| 10 Autenticazione locale | ✅ |
| 11 Multiutente e segregazione | ✅ |
| 12a Ruoli e permessi | ✅ |
| 12b Ruolo USER | ✅ |
| 12c Ruolo MANAGER | ✅ |
| 12d Ruolo ADMIN | ✅ |
| 13a Admin (disable+gruppo) | ✅ |
| 13b Sicurezza (headers, errori) | ✅ |
| 13c Fix stilistici e UX | ✅ |
| 13d Hardening (audit su richiesta) | ✅ 2026-08-04 |
| 14 Produzione e documentazione | ✅ 2026-08-04 (chiusura v1.0.0) |

## Dettagli di fasi chiave
Jinja2 autoescape attivo (nessun `|safe`); `hours` 1-12 step 0.50; header sicurezza HTTP; `error.html` generico 401/403/405; `_error_context` sincrono senza DB.

- **Fase 13d (2026-08-04)**: XSS da `onsubmit` in `admin_user_edit.html` corretto (data-attributes + script sicuro), sanificazione caratteri di controllo negli schemi Pydantic, cookie sessione SameSite/Secure configurabili, log password prudente. 78 test OK + 5 subtests. **Issue F chiusa.**
- **Fase 14 (2026-08-04)**: chiuse le issue della lista (vedi sotto).
  - **Issue I**: service systemd già corretto (EnvironmentFile=/etc/efftrack.env, nessuna variabile hardcodata). Verificato.
  - **Issue J**: `/health` già pubblico (nessuna dependency auth in `web.py:602`). Verificato.
  - **Issue K**: timeout export valutato — l'app usa Uvicorn (nessun timeout request) e l'export CSV è uno `StreamingResponse`: nessuna azione necessaria. Documentazione in `techContext.md`.
  - **Issue L**: nuovo middleware `RequestBodyLimitMiddleware` (`app/core/body_limit.py`) registrato in `main.py`, soglia `EFFORT_TRACKING_MAX_BODY_BYTES` (default 1 MiB) in `config.py`/`.env.example`.
  - **Issue M**: nuovo script opzionale `deploy.sh` (crea utente/dir/venv, copia codice, genera `/etc/efftrack.env`, installa servizio systemd). Allineato al path `.venv` del service.
  - **Issue H** (v0.24.2, 2026-08-04): nuova suite `tests/test_functional.py` (26 test) + `tests/conftest.py` con DB SQLite su file dedicato ai test (isolato da `data/efftrack.db`). Dipendenza dev `httpx` aggiunta a `requirements-dev.txt`. Copertura: `/health` pubblico, auth login/logout/account disabilitato, redirect anonimi, CRUD record via form (crea/aggiorna/elimina), regola aziendale (niente update/delete su record altrui), export CSV segregato per utente e filtro mese, permessi di ruolo (USER/MANAGER/ADMIN sull'area admin), vista gruppo manager e relativo export, profilo e cambio password. **104 test totali verdi.** **Issue H chiusa.**
  - **Chiusura (2026-08-04, v1.0.0)**: README riscritto per intero (stato v1.0.0, funzionalità, config, deploy con `deploy.sh` e manuale, note PostgreSQL, test). Memory bank allineato. Bump MAJOR a `1.0.0` (VERSION + `config.py`). **Fase 14 completata.**
  - **Issue N (2026-08-04, v1.0.1)**: bug di sicurezza — sessione senza scadenza (SessionMiddleware default 14 giorni) manteneva il login oltre riavvii/chiusura browser. Aggiunto `max_age` a `SessionMiddleware` con env var `EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS` (default 1800 s = 30 min). Aggiornati `config.py`, `main.py`, `.env.example`. **Issue N chiusa.**
- **S11 (2026-08-04, v1.1.0)**: cambio password obbligatorio al primo login.
  - Seed admin con `password_change_required=True`; nuovo middleware `PasswordChangeRequiredMiddleware` (`app/core/password_change.py`) registrato in `main.py` dopo `SessionMiddleware` con whitelist (profile, logout, login, static, health, docs) che redirige a `/profile` gli utenti con flag attivo.
  - `admin_users_create` imposta il flag per i nuovi utenti (password temporanea).
  - Redirect post-login a `/profile` quando il flag è attivo (`app/routers/auth.py`).
  - Banner di primo accesso in `profile.html` + CSS, context `password_change_required`.
  - `profile.py:change-password` azzera già il flag dopo il successo (verificato).
  - Documentazione: `.env.example`, `README.md`, `deploy.sh` (commento password temporanea), `.clinerules/09-post-change.md` (checklist Deploy).
  - **107 test totali verdi** (3 nuovi test in `tests/test_functional.py`). **S11 chiusa.**

## Cose note / limitazioni accettate
- Auth attiva (route business protette, `/health` pubblico).
- `bcrypt` pinnato `<4.1` per compatibilità passlib 1.7.4.
- Toggle dark/light (Fase 9b), preferenza localStorage.
- `pydantic-core` pinnato 2.46.4 per compatibilità pydantic 2.13.4.
- Migrazioni schema con `run_schema_migrations` (idempotente); Alembic da valutare.
- `user_id` FK verso users (ON DELETE SET NULL); regola aziendale: nessuno modifica/elimina record altrui.
- Cancellazione **permanente** senza soft-delete/audit (da valutare in futuro).
- DB sviluppo: 2 gruppi SOC/NOC, 6 utenti test (~20 record ciascuno, password `test`), admin gestore.
- Config: `.env` locale dev; in produzione `/etc/efftrack.env` (systemd EnvironmentFile).
- Campi form opzionali nella firma `POST /` per supportare `action=delete`; validazione obbligatoria server-side via `EffortEntryCreate`.
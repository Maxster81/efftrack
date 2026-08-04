# Post-Change Rules — Controlli dopo ogni modifica

## Principio

Il progetto ha due livelli di verifica qualità/security:

1. **Controllo rapido post-modifica** — eseguito **sempre**, prima di ogni commit funzionale.
2. **Audit approfondito** (ex Fasi 13d/14) — eseguito **solo su richiesta esplicita dell'utente**, perché impegnativo e di norma necessario solo a livelli di modifica elevati.

---

## Sezione 1 — Controllo rapido post-modifica (obbligatorio ad ogni commit funzionale)

Prima di committare qualsiasi modifica funzionale (backend o UI), verificare **in modo rapido** questa checklist (~30 secondi):

- [ ] **Input:** i nuovi campi utente hanno validazione server-side e sanitizzazione?
- [ ] **Route:** le nuove route sono protette da autenticazione/autorizzazione?
- [ ] **Template:** nessun dato utente in `onsubmit`/`onclick`/attributi `on*`? Nessun `|safe` abusato?
- [ ] **Verifica browser (se UI):** se il task ha toccato CSS/template/JS, usare Playwright MCP (`browser_navigate` + `browser_snapshot`/`browser_take_screenshot`) per verificare resa, accessibilità e assenza di errori JS/console (pattern in `10-mcp.md`)
- [ ] **Logging:** nessuna password o dato sensibile nei log?
- [ ] **Config:** i nuovi parametri sono in `.env.example` con default sicuro?
- [ ] **Test:** `pytest` eseguibili e tutti verdi?

Se una verifica non è soddisfatta, correggere prima del commit. Non serve rifare gli audit completi per ogni micro-modifica.

---

## Sezione 2 — Audit approfondito su richiesta (ex Fasi 13d + 14)

Da eseguire **solo quando l'utente lo richiede esplicitamente** (es. "fai l'audit", "fai l'hardening", "prepariamo per la produzione", "fai solo i test funzionali").

Ogni punto è **indipendente**: l'utente può chiederne uno solo, senza dover rifare tutto. Nessun automatismo: attendere sempre il comando dell'utente.

### 14P-A — XSS e sanitizzazione
- [ ] Verificare che non siano comparse nuove superfici XSS (attributi `on*`, `|safe`, `innerHTML`, interpolazine JS con dati utente).
- [ ] Verificare che la CSP (`SecurityHeadersMiddleware`) sia ancora coerente con le pagine e gli script attuali.
- [ ] Verificare che i campi testo in persistenza abbiano validazione robusta (max_length, whitelist, sanitizzazione caratteri di controllo).

### 14P-B — CSRF e sessione
- [ ] Cookie di sessione con `SameSite` corretto (default `lax`) e `Secure` attivo/attivabile in produzione.
- [ ] `SessionMiddleware` configurato correttamente (`same_site`, `https_only`).
- [ ] Form POST protetti da CSRF cross-site (SameSite è sufficiente per l'app server-rendered).

### 14P-C — Error handling e logging
- [ ] Nessuno stack trace esposto all'utente in produzione (pagine di errore templatizzate).
- [ ] Nessuna password, token o dato sensibile nei log.
- [ ] `_error_context` (o equivalente) senza query DB e robusto in caso di problemi di connettività.

### 14P-D — Test funzionali completi (Issue H)
- [ ] Test end-to-end con `pytest` + `HTTPX` sulle route: GET `/`, POST `/` (insert/update/delete), export, auth, permessi.
- [ ] Copertura dei ruoli (admin/manager/user) sulle route sensibili.
- [ ] Verifica che l'export restituisca solo i dati autorizzati.

### 14P-E — Documentazione deploy
- [ ] `README.md` aggiornato con istruzioni di deploy complete (venv, dipendenze, `.env`, systemd, reverse proxy).
- [ ] `systemd/efftrack.service` verificato e aggiornato (variabili env, log su journald).
- [ ] Note PostgreSQL (o altro) aggiornate se lo stack/DB è cambiato.

### 14P-F — Memory bank completo
- [ ] Tutti i file del memory bank (`activeContext.md`, `progress.md`, `systemPatterns.md`, `techContext.md`, ecc.) coerenti con lo stato attuale del progetto.

---

## Relazione con le altre regole

Questa regola è **procedurale** (dice quando eseguire quali controlli):
- La **Sezione 1** si integra con `08-workflow.md` (verifiche per-area a ogni task).
- La **Sezione 2** riprende le attività delle Fasi 13d (hardening) e 14 (documentazione/tests) come audit ciclici su richiesta.
- Complementare a `06-security.md` (normativo su auth, secrets, validazione).
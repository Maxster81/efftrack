# Issue e Suggerimenti (test utente)

> **Nota operativa:** contiene SOLO le issue/suggestion ancora **aperte**. Quando una voce viene risolta, va **rimossa** nello stesso commit che la risolve.
> Lo storico delle voci risolte è compattato in fondo (una riga ciascuna).

## Issue aperte

## Future Features (non assegnate alle fasi correnti)

### S10 — Self-creation utente
Pagina di login: consentire l'auto-registrazione di un nuovo utente. Il modello `users` ha già `first_name`, `last_name`, `email`, `password_change_required`. La self-creation imposta `password_change_required=True` e `role="user"`.

### S11 — Cambio password obbligatorio al primo login
Se `password_change_required=True`, dopo il login l'utente viene rediretto a `/profile` finché non cambia la password. Flag e router `profile.py` già predisposti.

### S4 — Filtro per anno e mese separati
Separare il filtro mensile in due dropdown distinti (Anno + Mese), così la lista dei mesi resta "bloccata" ai 12 valori.

### S6 — Giorno di ferie
Checkbox/radio che rende i campi non obbligatori e non compilabili (solo data). Al SALVA crea un record con campi vuoti e "FERIE" nelle NOTE.

### S9 — Refine grafico Gestione Lookup
Affinare lo stile tabellare della pagina Lookup (ex Issue J).

## Storico voci risolte (compattato)
- **Issue A** (pagine errore 404/500) → Fase 13b.
- **Issue B, C, M** → risolte (banner, export, riorganizzazione /admin/users).
- **Issue D** (validazione ore 1-12, step 0.50) → Fase 13b.
- **Issue E** (campo last_login) → Fase 12b.
- **Issue F** (XSS/sanificazione input) → Fase 13d.
- **Issue G** (header sicurezza HTTP) → Fase 13b.
- **Issue I** (stile admin utenti ok) → Fase 13c.
- **Issue K** (assegnazione gruppo utenti) → Fase 13a.
- **Issue L** (disabilita utente) → Fase 13a.
- **S1** (hamburger nascosto in login) → Fase 13c.
- **S2** (ore step 0.50) → Fase 13b.
- **S3** (menu utente a discesa) → Fase 13c.
- **S5** (evidenzia record modificato) → Fase 13c.
- **Issue H** (test funzionali pytest+HTTPX) → Fase 14, v0.24.2 (2026-08-04).
- **S7** (gruppo autopopolato, campo readonly) → 2026-08-04.
- **S8** (finestra eliminazione utente) → 2026-08-04.

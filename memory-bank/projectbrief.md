# Project Brief — Effort Tracking

## Scopo
Web server per la registrazione di **effort** (ore lavorate, attività giornaliere, note) replicando il comportamento di un vecchio tool gestionale usato in azienda, ma come applicazione web moderna, manutenibile e installabile su Ubuntu.

## Target
- **Deployment**: Ubuntu con Python `venv`. **No Docker** come prerequisito.
- **Utente iniziale**: single-user.
- **Evoluzione**: multi-user con segregazione dei dati.
- **Auth**: rimandata alle fasi finali (Fase 10–11). Login e segregazione non vanno implementati prima.

## Vincoli non negoziabili
- Stack Python con venv, niente Docker.
- Server-side rendering (Jinja2) + JS vanilla. Niente SPA pesante nelle prime fasi.
- Validazione server-side obbligatoria su tutti gli input che entrano in persistenza.
- Accessibilità di base (label, ARIA, semantic HTML).
- Ogni fase deve lasciare un risultato verificabile.
- Niente merge su `main` senza istruzione esplicita dell'utente **nel messaggio corrente**.

## Regole di workflow non negoziabili
- Le **fasi** della roadmap (Fase 0 → Fase 12) si considerano completate **solo quando l'utente lo dichiara esplicitamente** ("fase X completata", "ok", "procedi", ecc.).
- Il memory bank va aggiornato a ogni cambio di stato di fase e ad ogni decisione tecnica rilevante.
- Il memory bank è la **fonte di verità** dello stato del progetto. In qualunque sessione futura, leggendo `activeContext.md` e `progress.md` si sa esattamente dove si è arrivati.
- La fase in corso è sospesa: nessun commit funzionale, nessun bump di versione, nessun tag finché l'utente non conferma la chiusura della fase.

## Esclusioni esplicite (derivate dal master-prompt)
- **Niente internazionalizzazione Ita→Eng**: i riferimenti i18n presenti nelle cline rules sono adattati da un altro progetto e vanno ignorati.
- **Niente `09-web-design` rule**: il web design non è prioritario in questo momento. Si replica la struttura del mock ma con palette neutra (blu navy + grigi), non i colori dell'azienda precedente.
- **Auth rimandata**: SECRET_KEY placeholder presente in config ma l'autenticazione non si attiva.

## Stack
- **Backend**: Python 3.10+ con FastAPI.
- **Template**: Jinja2 server-side.
- **ORM**: SQLAlchemy 2.x (per favorire la futura migrazione a PostgreSQL).
- **DB**: SQLite3 con WAL + foreign keys abilitati a ogni connessione.
- **Static files**: CSS vanilla + JS vanilla, in `app/static/`.

## Palette UI
- Primario: **blu navy** (header, header tabelle, pulsante Salva).
- Secondario: grigi neutri per sfondo, bordi, testi secondari.
- Accento: per riga selezionata in tabella.
- Variabili CSS definite in `:root` per consentire un futuro tema dark/light senza refactoring.

## Roadmap (estesa il 2026-07-31)
```text
Fase 0   — Bootstrap progetto
Fase 1   — Pagina HTML statica raggiungibile
Fase 2   — Layout statico stile effort tracking
Fase 3   — Form interattivo con lookup hardcoded
Fase 4   — Database e seed lookup
Fase 4b  — Sidebar navigazione con hamburger menu        🆕
Fase 5   — Salvataggio record (singolo)
Fase 5b  — Inserimento bulk "copia su settimana"         🆕
Fase 6   — Elenco record
Fase 7   — Selezione record e update
Fase 8   — Export CSV/XLSX
Fase 9   — Refactoring, logging, env, systemd
Fase 10  — Autenticazione locale
Fase 11  — Multiutente e segregazione dati
Fase 12  — Gestione ruoli e amministrazione (Admin)      🆕
Fase 13  — Export manager e gestione gruppo (Manager)    🆕
Fase 14  — Hardening e produzione
```

Le **Fasi 4b e 5b** sono sotto-fasi della 4 e 5: dipendono rispettivamente dal DB e dal salvataggio singolo, ma hanno scope UI/produttività propri. La **sidebar** è un contenitore vuoto in 4b e verrà popolata in base al ruolo nelle fasi 12–13.

Vedi `progress.md` per lo stato corrente e `techContext.md` per i dettagli tecnici di ciascuna fase.

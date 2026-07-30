# Git & Version Control Rules

## Branching — Regola ASSOLUTA

Tutto il lavoro va su `develop`. `main` è off-limits **finché l'utente non dice espressamente "fai merge su main"**.

Questa regola si applica a **qualunque** operazione su `main`:
- merge
- checkout
- push
- rebase
- commit diretto (vietato sempre)

### Cosa fare — passo obbligatorio

Prima di eseguire qualsiasi comando Git che coinvolga `main`:
1. **Leggi questa regola.** (always)
2. **Controlla** se l'utente ti ha dato un'istruzione esplicita per operare su `main` nel messaggio corrente.
3. **Se non c'è** → non toccare `main`. Fine.
4. **Se c'è** → esegui solo quella singola operazione richiesta, poi torna immediatamente su `develop` con `git checkout develop`.

### Esempi

| Utente dice | Cosa fare |
|-------------|-----------|
| *"fai un commit e merge su main"* | ✅ Un merge, poi checkout develop |
| *"pusherò io"* o *"fai il commit"* | ❌ Mai toccare main |
| *"porta in produzione"* | ❌ Chiedere: "vuoi che faccia merge su main?" |
| *"fai il merge di activeContext.md su main"* | ✅ Un merge (se già autorizzato nel msg), poi checkout develop |
| *nessun messaggio su main* | ❌ Mai toccare main, anche se poco prima era stato autorizzato |

### Eccezioni

**Nessuna.** Anche se:
- l'utente ha detto "fai merge" poche righe fa e ora chiede altro
- il merge è piccolo (fast-forward)
- è solo un aggiornamento di activeContext.md
- sembra "ovvio" che l'utente lo vorrebbe

Se l'utente non dice esplicitamente "fai merge su main" **in quel messaggio**, non si tocca main.

### Conseguenze

Violare questa regola = corrompere il workflow del progetto. Non si tratta di una preferenza, ma di una barriera di sicurezza.

Non c'è spazio per interpretazione: **nessuna operazione su main senza autorizzazione esplicita nel messaggio corrente**.

## Commit Convention (Conventional Commits)
Usare il formato `type(scope): description`:
- `feat:` — Nuova funzionalità
- `fix:` — Bug fix
- `refactor:` — Refactoring senza cambi funzionali
- `chore:` — Manutenzione, dipendenze, build
- `docs:` — Documentazione
- `style:` — Formattazione, spazi, virgolette

## Messaggi
- Solo in inglese.
- Descrizione breve ma chiara (max ~72 caratteri).
- Il corpo del commit è opzionale, usarlo per dettagli aggiuntivi se necessario.

## Versioning (SemVer)

Il progetto segue il **Semantic Versioning** (MAJOR.MINOR.PATCH).

- **MAJOR** — breaking changes: ristrutturazioni architetturali, rimozione di endpoint, modifiche incompatibili con versioni precedenti.
- **MINOR** — nuove funzionalità retrocompatibili: nuova feature, nuovo modulo, nuova area della UI.
- **PATCH** — bug fix, refactoring interno, miglioramenti UI/CSS, aggiornamento dipendenze.

### File VERSION
La versione corrente del progetto è tracciata nel file `VERSION` nella root del repository.
Ogni servizio o package principale può inoltre avere la propria versione in `__init__.py`.

### Regola: bump obbligatorio ad ogni commit funzionale
Ogni volta che Cline fa un commit che modifica codice applicativo, UI/CSS o file di configurazione (esclusa la sola documentazione), **deve**:
1. Valutare se il cambiamento è MAJOR, MINOR o PATCH secondo SemVer.
2. Aggiornare `VERSION` e tutti i `__init__.py` dei servizi toccati **prima** di creare il commit.
3. Includere `VERSION` e tutti i `__init__.py` aggiornati **nello stesso commit** delle modifiche funzionali.
4. Creare un tag git annotato sullo stesso commit del bump.

### Convenzione tag
- Usare il prefisso `v` seguito dal numero di versione: `v1.0.0`, `v1.1.0`, `v2.0.0`, ecc.
- Il tag va creato **dopo** il commit di aggiornamento del `VERSION`, sullo stesso commit.
- I tag sono annotati (`-a`), non leggeri.

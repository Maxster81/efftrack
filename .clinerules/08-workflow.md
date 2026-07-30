# Workflow Rules — Separazione Backend / Frontend nei Task Misti

## Principio Fondamentale

Ogni task che coinvolge **sia logica applicativa sia interfaccia web** deve essere affrontato separando esplicitamente i due ambiti, sia in fase di analisi che di implementazione.

Non trattare mai un task misto come "un'unica modifica indistinta".

In questo progetto effort tracking è inoltre **obbligatorio procedere per fasi incrementali**, con stop esplicito tra una fase e la successiva quando richiesto dall'utente.

---

## Flusso di Lavoro Obbligatorio

### Fase 0 — Lettura Contesto Persistente

Prima di qualunque analisi o modifica:
1. Leggere **tutti** i file in `memory-bank/`.
2. Estrarre:
   - stato corrente del progetto
   - decisioni tecniche attive
   - fase corrente
   - rischi aperti
   - prossimi passi già concordati
3. Se il memory bank non esiste o è incompleto, segnalarlo e proporre/creare la baseline documentale.

### Fase 1 — Analisi e Separazione

Prima di scrivere codice, analizza il task e classifica gli impatti in due aree distinte:

**Area Applicativa (Backend / Servizi / API / Logica / Stato)**
- Routes e endpoint
- Validazione dati
- Autenticazione / autorizzazione
- Database e query
- Configurazione e variabili d'ambiente
- Logica di business
- Export dati
- Side-effect su altri servizi

**Area UI (Frontend / HTML / CSS / Componenti / Accessibilità / Resa Visiva)**
- Template Jinja2
- CSS condiviso (`static/style.css`)
- JavaScript client-side (`static/*.js`)
- Visualizzazione form effort tracking
- Griglia/tabella dei record
- Accessibilità base (label, ARIA, semantic HTML)
- Responsive behavior
- Coerenza grafica con componenti esistenti

### Fase 2 — Pianificazione di Fase

Per questo progetto, prima di implementare, mappare sempre il task contro la roadmap:
- **Fase 0:** bootstrap progetto, venv, struttura, pagina test server
- **Fase 1:** pagina HTML statica raggiungibile
- **Fase 2:** layout statico stile effort tracking
- **Fase 3:** form interattivo con valori hardcoded e show/hide descrizione
- **Fase 4:** database e seed lookup
- **Fase 5:** salvataggio record
- **Fase 6:** elenco record
- **Fase 7:** selezione record e update
- **Fase 8:** export CSV/XLSX
- **Fase 9:** refactoring, logging, .env, systemd
- **Fase 10:** autenticazione locale
- **Fase 11:** multiutente e segregazione dati
- **Fase 12:** hardening e produzione

Ogni task deve dichiarare esplicitamente:
- in quale fase ricade
- se anticipa dipendenze di fasi successive
- se introduce debito tecnico accettato temporaneamente

### Fase 3 — Ricerca Parallela (per task ampi o poco chiari)

Se il task è **ampio** (coinvolge ≥3 file di ciascuna area) o **poco chiaro** (requisiti aperti, da esplorare):

1. Lanciare subagents distinti:
   - Subagent #1 — focalizzato su codice applicativo e architettura
   - Subagent #2 — focalizzato su UI, markup, componenti e coerenza grafica
2. Sintetizzare i risultati in un piano unico prima di modificare qualsiasi file.
3. Presentare il piano in checklist o task progress.

Per task **piccoli** (1-2 file per area, modifiche localizzate), i subagents non sono necessari. Ma la separazione concettuale resta obbligatoria.

### Fase 4 — Implementazione

Mantieni **separazione delle responsabilità** nelle modifiche:

- **La logica applicativa** non deve introdurre dipendenze inutili nella UI.
- **La UI** non deve rompere contratti, dati o flussi applicativi.
- Ogni fase deve lasciare il progetto in stato eseguibile o almeno verificabile.
- Non introdurre autenticazione nelle fasi iniziali solo “per portarsi avanti”.

### Fase 5 — Verifiche Specifiche per Area

#### Ogni volta che tocchi il frontend, verifica:
- [ ] **HTML semantico:** Tag appropriati (`<nav>`, `<main>`, `<section>`, `<label>`, `<fieldset>`)
- [ ] **Accessibilità base:** `for` su label, `alt` su immagini, `aria-label` su bottoni icona, contrasto colore
- [ ] **Coerenza con componenti e stili esistenti:** Non duplicare CSS già esistente in `static/style.css`
- [ ] **Responsive behavior:** Il layout regge su viewport stretti
- [ ] **Tema (dark/light):** Le nuove aggiunte rispettano le variabili CSS del tema
- [ ] **i18n:** Nessuna stringa UI hardcodata in italiano, tranne fallback controllati
- [ ] **Verifica browser:** raccomandata per modifiche a CSS, template o JS

#### Ogni volta che tocchi la logica applicativa, verifica:
- [ ] **Impatto su servizi, API, validazioni e stato:** La modifica è retrocompatibile?
- [ ] **Possibili regressioni:** Il task tocca dati, export o futuro multiutente?
- [ ] **Configurazione:** I nuovi parametri hanno default di sviluppo sicuri?
- [ ] **Security:** Le nuove routes espongono dati sensibili? Hanno auth quando necessario?
- [ ] **Persistenza:** Le modifiche sono compatibili con l'evoluzione da single-user a multi-user?
- [ ] **Punti in cui servono test o controlli manuali**

### Fase 6 — Aggiornamento Memory Bank

Prima di chiudere il task:
- aggiornare `activeContext.md`
- aggiornare `progress.md`
- aggiornare `systemPatterns.md` se cambia architettura o pattern
- aggiornare `techContext.md` se cambiano stack, dipendenze o setup

### Fase 7 — Riepilogo Finale

Prima del commit, produrre un riepilogo strutturato con tre sezioni:

```text
## Modifiche Applicative
- [file] : cosa è cambiato (1-2 righe per file)

## Modifiche UI/Grafiche
- [file] : cosa è cambiato (1-2 righe per file)

## Rischi o Punti da Verificare
- [x] Verifica superata / [ ] Da testare manualmente
```

Questo riepilogo va annotato in `memory-bank/activeContext.md`.

---

## Soglie per l'Uso dei Subagents

| Complessità | Subagents? | Esempio |
|---|---|---|
| **Piccolo** (1-2 file per area) | No | Fix CSS puntuale, etichette form, seed lookup |
| **Medio** (2-4 file per area) | Opzionale | Nuova pagina con form + route + persistenza |
| **Grande** (≥5 file per area, o task ambiguo) | **Sì, obbligatorio** | Nuovo modulo auth, export avanzato, refactoring architetturale |

---

## Eccezioni

Task puramente **applicativi** o puramente **UI** non richiedono la separazione in due aree, ma devono comunque dichiarare esplicitamente che l'impatto è su una sola area.

---

## Relazione con le Altre Regole

Questa regola è **procedurale** (dice come lavorare), complementare alle regole **normative**:
- `01-python-2.md` → stile Python, type hints, pattern FastAPI
- `02-services-3.md` → architettura del servizio, binding, reverse proxy
- `03-database-4.md` → SQLite, WAL, migrazioni, lookup
- `04-frontend-5.md` → Jinja2, vanilla JS, tema, CSS condiviso
- `09-web-design-10.md` → HTML semantico, accessibilità, colori, tipografia, coerenza grafica
- `05-git-6.md` → branching, commit convention, versioning
- `06-security-7.md` → autenticazione futura, secrets, validazione
- `07-memory-bank-8.md` → documentazione persistente del progetto
- **`08-workflow-9.md` (questa)** → processo strutturato per task misti BE/FE e gestione a fasi

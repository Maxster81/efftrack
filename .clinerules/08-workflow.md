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

Per questo progetto, prima di implementare, mappare sempre il task contro la roadmap attuale (stato completo in `memory-bank/progress.md`):
- **Fasi 0–8:** bootstrap, pagine, form, DB, salvataggio, elenco, CRUD, export.
- **Fasi 4b/5b/9b:** sidebar, copia su settimana, toggle tema.
- **Fasi 9–11:** refactor/logging, auth, multiutente e segregazione.
- **Fasi 12a–13d:** ruoli/permessi, ADMIN, hardening.
- **Fase 14:** produzione e documentazione (sempre ultima; audit su richiesta via `.clinerules/09-post-change.md`).

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
- `01-python.md` → stile Python, type hints, pattern FastAPI, architettura servizi
- `03-database.md` → SQLite, WAL, migrazioni, lookup
- `04-frontend.md` → Jinja2, vanilla JS, tema, CSS condiviso
- `05-git.md` → branching, commit convention, versioning
- `06-security.md` → autenticazione futura, secrets, validazione
- `07-memory-bank.md` → documentazione persistente del progetto
- `09-post-change.md` → controlli rapidi post-modifica (sempre) + audit approfondito su richiesta
- **`08-workflow.md` (questa)** → processo strutturato per task misti BE/FE e gestione a fasi
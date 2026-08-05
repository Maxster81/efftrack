# MCP Rules — Server Disponibili e Pattern d'Uso

## Principio Generale

In questo workspace sono installati quattro server MCP: **Filesystem**, **Memory**, **Playwright** e **Context7**.

Usali quando apportano un **beneficio reale** rispetto agli strumenti built-in (read_file, search_files, execute_command). Non usarli per operazioni banali o quando uno strumento nativo è più semplice e altrettanto efficace: l'overhead di un MCP deve essere giustificato.

Prima di usare un MCP, chiedersi:
- Questo tool fa qualcosa che uno strumento built-in non può fare (o fa in modo molto più efficiente)?
- L'uso del MCP aggiunge valore al task (accuratezza, velocità, tracciabilità)?

---

## Filesystem MCP

### Capacità
- Lettura/scrittura/ricerca file su più percorsi.
- Operazioni batch (`read_multiple_files`, `directory_tree`, `search_files`).
- Gestione directory e metadati file (dimensioni, date, permessi).

### Quando usarlo
- **Lettura multipla simultanea**: analizzare più file correlati in un'unica chiamata (`read_multiple_files`).
- **Ricerca avanzata** su pattern glob o percorsi annidati (`search_files`, `directory_tree`).
- **Operazioni batch o strutturali** (spostare/rinominare, verificare struttura completa di una directory).
- Quando occorre il **tree JSON** dell'intero progetto o di una sotto-gerarchia per una visione d'insieme.

### Quando NON usarlo
- Lettura di un singolo file noto → preferire `read_file` built-in.
- Ricerca regex trasversale a molti file con contesto → preferire `search_files` built-in (ritorna righe di contesto).
- Creazione/overwrite di un file singolo → preferire `write_to_file` / `replace_in_file`.

---

## Memory MCP (Knowledge Graph)

### Capacità
- Knowledge graph persistente di **entità** (con osservazioni) e **relazioni** tra esse.
- Ricerca semantica (`search_nodes`), lettura dell'intero grafo (`read_graph`).

### Pattern d'uso consigliato per efftrack
- **Entità = modelli di dominio**: `Client`, `Group`, `Activity`, `User`, `EffortEntry`.
- **Entità = componenti architetturali**: `FastAPI`, `SQLite`, `Jinja2`, `static/*.js`.
- **Relazioni = dipendenze o flussi**: es. `WebRouter → EffortEntry`, `Form.js → POST /`, `AuthRouter → User`.
- **Osservazioni = decisioni o note tecniche** associate a un'entità (es. "WAL mode attivo su SQLite", "campi Descrizione opzionale mostrato solo per Supporto Specialistico").

### Rapporto con il memory-bank su file
- Il **memory-bank su file** (`memory-bank/*.md`) resta la **fonte di verità** principale: è la memoria che persiste tra le sessioni e va sempre aggiornata (regole `07-memory-bank.md` e `08-workflow.md`).
- Il **Memory MCP** è complementare: utile per tracciare **relazioni tra concetti** e interrogazioni rapide del tipo "cosa dipende da cosa", senza dover rileggere interi file.
- Quando si usa il Memory MCP per registrare decisioni, **salvarle comunque anche nel memory-bank su file** (mai duplicazione che diverge: il file è il riferimento).
- Il Memory MCP non sostituisce i file: se si svuota il grafo MCP, il progetto non deve perdere nulla di rilevante.

### Quando NON usarlo
- Per appunti temporanei o per cose già ben documentate nei file del memory-bank.
- Quando il beneficio di tracciare una relazione nel grafo è marginale rispetto al costo di mantenerlo allineato al memory-bank.

---

## Playwright MCP

### Capacità
- Browser headless (Chromium) con navigazione, click, snapshot di **accessibilità**, screenshot, console/network monitoring, fill di form.

### Pattern d'uso consigliato per efftrack
- **Verifica frontend post-modifica** (integrazione con la checklist Fase 5 di `08-workflow.md`): dopo modifiche a CSS, template o JS, usare Playwright per:
  - `browser_navigate` sulla route interessata (es. `/`).
  - `browser_snapshot` per verificare la struttura accessibile e il comportamento degli elementi.
  - `browser_take_screenshot` per un controllo visuale (tema dark/light, responsive, coerenza).
  - `browser_fill_form` / `browser_click` per testare flussi (es. salvataggio record, toggle tema, selezione riga).
- **Verifica console/errori**: `browser_console_messages` e `browser_network_requests` per intercettare errori JS o richieste fallite dopo i cambiamenti.
- **Accessibilità**: lo snapshot accessibile aiuta a verificare label, ARIA e struttura semantica pronti all'uso.

### Quando NON usarlo
- Task che toccano **solo backend/livello applicativo** (routes di logica, DB, configurazione senza UI).
- Quando è sufficiente l'analisi statica del markup/template senza esecuzione reale del browser.

---

## Context7 MCP

### Capacità
- Documentazione aggiornata e version-specifica di librerie/framework, con esempi di codice estratti direttamente dalle fonti ufficiali.
- Due tool: `resolve-library-id` (risolve un nome di libreria in un ID Context7) e `query-docs` (recupera documentazione per un ID libreria).
- Eseguito localmente via `npx @upstash/context7-mcp` (server stdio), configurato in `cline_mcp_settings.json` come `github.com/upstash/context7-mcp`.

### Pattern d'uso consigliato per efftrack
- **Documentazione aggiornata dei framework in uso**: FastAPI, Starlette, Jinja2, vanilla JS, SQLite, ecc. quando serve una API/pattern recente e non ci si affida alla memoria di training.
- **Scelta dello stack o escalation di decisioni tecniche** (regole `01-python.md`/`03-database.md`): recuperare documentazione ufficiale aggiornata prima di proporre una soluzione.
- **Esempio di flusso**: `resolve-library-id` (query: "documentazione FastAPI", libraryName: "FastAPI") → ID `/websites/fastapi_tiangolo` → `query-docs` con quella library id e una domanda specifica.
- **Specificare versione quando rilevante** (es. "Next.js 14") per documentazione esatta di quella versione.
- **ID libreria noto**: se si conosce già l'ID (es. `/websites/fastapi_tiangolo`), passarlo direttamente a `query-docs` senza passare da `resolve-library-id`.

### Quando NON usarlo
- Quando la documentazione è già nota/stabile e la query non aggiunge valore rispetto alle conoscenze consolidate.
- Per ricerche generiche sullo stack locale già ben documentato nel memory-bank (`techContext.md`, `systemPatterns.md`).
- Non sostituisce la lettura dei sorgenti locali: per capire com'è fatto il codice di efftrack usare `read_file`/`search_files`.

---

## Riepilogo: quale MCP per quale scenario

| Scenario | MCP consigliato | Strumento alternativa |
|---|---|---|
| Analisi di più file correlati in blocco | Filesystem (`read_multiple_files`) | read_file ripetuto |
| Visione d'insieme della struttura progetto | Filesystem (`directory_tree`) | list_files |
| Tracciare relazioni tra entità di dominio / architettura | Memory (create_entities/relations) | (memory-bank su file) |
| Verifica visuale/accessibilità di una pagina | Playwright (snapshot, screenshot) | analisi statica del template |
| Test di un flusso UI (form, toggle, selezione) | Playwright (navigate, fill_form, click) | (nessuna — serve il browser) |
| Documentazione aggiornata di librerie/framework | Context7 (`resolve-library-id`, `query-docs`) | memoria di training (obsoleta) |
| Lettura/modifica di un singolo file | — (usare tool built-in) | read_file / write_to_file |

---

## Relazione con le Altre Regole

Questa regola è **normativa sugli strumenti** (quando usare i MCP) e si integra con:
- `04-frontend.md` → la verifica browser di Playwright rispetta gli stessi criteri di accessibilità/tema/coerenza.
- `08-workflow.md` → Playwright si inserisce nella checklist di verifica frontend (Fase 5), come mezzo per la "Verifica browser raccomandata".
- `09-post-change.md` → la verifica frontend del controllo rapido post-modifica può usare Playwright.
- `07-memory-bank.md` → il Memory MCP è complementare ma non sostituisce il memory-bank su file, che resta la fonte di verità.
- `01-python.md` e `03-database.md` → prima di proporre un sotto-stack o una scelta di libreria, Context7 può fornire documentazione ufficiale aggiornata a supporto dell'analisi pro/contro.

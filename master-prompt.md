# Master Prompt — Effort Tracking Web Server

Agisci come senior software architect, senior Python backend developer e senior frontend engineer con forte attenzione a manutenibilità, UX gestionale e deployment reale su Ubuntu.

Devi progettare e sviluppare un'applicazione web chiamata **Effort Tracking** da eseguire su Ubuntu, preferibilmente senza Docker. Lo stack preferito è Python in virtual environment (`venv`).

## Regola assoluta di esecuzione
Prima di ogni task devi leggere **tutti** i file in `memory-bank/` e usare il loro contenuto come base di contesto persistente. Se il memory bank non esiste, devi crearlo come primo deliverable insieme alla baseline documentale minima.

## Obiettivo del prodotto
L'app deve permettere di tracciare attività giornaliere e ore lavorate per cliente, replicando il comportamento di un vecchio tool di effort tracking usato in azienda, ma tramite piccolo web server con database locale e futura evoluzione multiutente.

## Vincoli iniziali
- Fase iniziale **single-user**.
- Evoluzione successiva a **multi-user**.
- L'autenticazione user/password va introdotta **solo nelle ultime fasi**.
- **Non usare Docker come prerequisito**.
- Il target di deploy è **Ubuntu con Python venv**.
- Ogni scelta deve privilegiare semplicità operativa, leggibilità e facilità di manutenzione.

## Stack desiderato
Proponi uno stack concreto e motivato tra:
- FastAPI + Jinja2 + SQLite
- FastAPI + Jinja2 + SQLAlchemy + SQLite
- Flask + Jinja2 + SQLite

Se non emergono controindicazioni forti, preferisci **FastAPI**.

## Requisiti UI
L'interfaccia deve ricordare un piccolo gestionale CRUD:
- area superiore con form di inserimento/modifica
- area inferiore con elenco/tabella delle attività salvate
- alla selezione di una riga, i campi del form si popolano con i dati del record selezionato
- pulsante Salva
- esportazione dati prevista in fasi successive

## Campi richiesti
- **User:** mostra nome e cognome della persona
- **Mese:** inutile, non persistito
- **Data:**
  - se è selezionato un record, mostra la data dell'evento
  - se si crea un nuovo record, permette di scegliere una nuova data
- **Cliente:** 
  - se è selezionato un record, mostra il valore del record
  - se si crea un nuovo record, dropdown, valori iniziali `INAIL`, `MDS`, default `INAIL`
- **Gruppo:** 
 - se è selezionato un record, mostra il valore del record
 - se si crea un nuovo record, dropdown, valore iniziale `GRUPPO SOC`, default `GRUPPO SOC`
- **Attività:** 
  - se è selezionato un record, mostra il valore del record
  - se si crea un nuovo record, dropdown, valori iniziali:
   - `SOC - Conduzione apparati di sicurezza`
   - `SOC - Supporto Specialistico`
     default `SOC - Conduzione apparati di sicurezza`
- **Ore spese:** 
 - se è selezionato un record, mostra il valore del record
 - se si crea un nuovo record, campo numerico, valori da 1 a 24, default 8
- **Note:** testo libero
 - se è selezionato un record, mostra il valore del record
 - se si crea un nuovo record, campo vuoto compilabile
- **Descrizione:** testo libero, nascosto di default, visibile solo se Attività = `SOC - Supporto Specialistico`
 - se è selezionato un record, mostra il valore del record
 - se si crea un nuovo record, campo vuoto compilabile

## Requisiti dati
- I dati devono essere persistiti in database.
- Prima fase: **SQLite**.
- Progettare in modo da semplificare futura migrazione a PostgreSQL.
- Il campo **mese** deve essere derivato dalla data, non memorizzato.
- Prevedere almeno create, read e update.
- Prevedere export CSV e, se opportuno, XLSX in fase successiva.

## Requisiti architetturali
Proporre una struttura semplice e scalabile, ad esempio:
- `app/`
- `templates/`
- `static/`
- `routers/`
- `services/`
- `repositories/`
- `schemas/`
- `memory-bank/`
- `tests/`

Puoi proporre una struttura migliore, ma mantienila comprensibile e coerente col progetto.

## Regole di lavoro obbligatorie
Per ogni task devi:
1. leggere il memory bank
2. classificare gli impatti in backend e frontend
3. mappare il task a una fase della roadmap
4. spiegare obiettivo, file toccati, comandi Ubuntu, verifiche
5. aggiornare il memory bank a fine fase/task significativo
6. non saltare direttamente alle fasi finali

## Roadmap obbligatoria
### Fase 0
- inizializzazione progetto
- creazione venv
- requirements
- struttura directory
- README tecnico minimale
- pagina/server di test
- creazione memory bank iniziale

### Fase 1
- pagina HTML statica raggiungibile via browser
- verifica raggiungibilità web server

### Fase 2
- layout HTML/CSS ispirato al vecchio effort tracking
- nessuna logica reale
- nessun salvataggio
- nessun dropdown realmente collegato

### Fase 3
- trasformazione del layout in form reale
- dropdown hardcoded
- validazioni client-base
- show/hide campo Descrizione

### Fase 4
- progettazione modello dati
- introduzione SQLite
- tabella effort_entries
- eventuali lookup tables o seed

### Fase 5
- salvataggio record nel database
- validazioni server-side
- messaggi di esito

### Fase 6
- elenco record nella parte inferiore
- ordinamento per data decrescente
- colonne utili per rendicontazione

### Fase 7
- selezione record dalla tabella
- popolamento form
- update record

### Fase 8
- export CSV
- opzionale export XLSX
- filtri base per data/cliente/attività

### Fase 9
- refactoring codice
- logging
- `.env.example`
- predisposizione systemd
- note reverse proxy se servono

### Fase 10
- autenticazione locale user/password
- password hashate
- login page
- sessione utente

### Fase 11
- multiutente
- segregazione dati per utente
- predisposizione ruoli futuri

### Fase 12
- hardening produzione
- controllo validazioni
- gestione errori
- backup SQLite
- note migrazione futura PostgreSQL

## Deliverable iniziale richiesto
Per cominciare non scrivere subito tutto il codice finale.
Prima devi produrre:
1. proposta architetturale
2. motivazione dello stack
3. struttura directory
4. data model iniziale
5. rischi e miglioramenti futuri
6. piano operativo dettagliato per fasi
7. solo dopo iniziare la Fase 0

## Regole di output quando generi codice
- Fornisci file completi
- Indica path precisi
- Indica comandi shell esatti
- Non fare assunzioni nascoste
- Se una decisione è dubbia, esplicitala prima

## Regole di qualità
- Codice chiaro e senza overengineering
- Preferire server-side rendering e JS leggero nelle prime fasi
- Validazione lato server obbligatoria quando entrano i dati
- Accessibilità di base obbligatoria
- UI professionale e semplice da usare
- Ogni fase deve lasciare un risultato verificabile

## Imprecisioni da parte utente
- le cline rules sono state adattate da altro progetto, per cui se trovi qualcosa relativo i18n, per cui relativo a traduzioni da Ita a ENG, non devi prenderle in considerazione.
- se trovi riferimenti a una cline rule chiamata 09-web-design (o simile), non prenderla in considerazione. Il web design in questo momento è l'ultimo problema. Provvederemo successivamente alle migliorie grafiche.
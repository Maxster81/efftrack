# Database Rules

## Tecnologia
- **Default:** SQLite3 per la prima implementazione del servizio effort tracking, salvo che sia dimostrato inadeguato.
- **WAL mode + foreign keys:** abilitare sempre su ogni connessione SQLite:
  ```python
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA foreign_keys=ON")
  ```
- **Target evolutivo:** predisporre il codice a una futura migrazione a PostgreSQL senza stravolgimenti architetturali.

## ORM vs SQLite diretto
- Per la prima fase, se il modello resta semplice, è ammesso SQLite3 diretto con query chiare e repository dedicato.
- Se il servizio cresce in complessità (più tabelle lookup, utenti, ruoli, esportazioni avanzate, audit), proporre SQLAlchemy/Alembic con analisi pro/contro.
- Se si sceglie SQLAlchemy fin dall'inizio, mantenere comunque l'implementazione semplice e leggibile.

## Modello Dati Minimo
- Prevedere almeno una tabella per le registrazioni di effort (`effort_entries`).
- Prevedere lookup separati o facilmente separabili per:
  - clienti
  - gruppi
  - attività
- Il campo **mese** non va persistito: deve essere derivato dalla data.
- Il campo **descrizione** deve essere opzionale e semanticamente collegato al caso “Supporto Specialistico”.
- Predisporre il modello per futura aggiunta di `user_id` senza refactoring distruttivo.

## Migrazioni
- Per servizi con poche tabelle, il pattern `ALTER TABLE` a startup o bootstrap SQL controllato è sufficiente.
- Se il numero di tabelle o versioni cresce, proporre strumenti strutturati (Alembic o equivalenti).
- Ogni modifica schema deve essere documentata in `memory-bank/systemPatterns.md` e `memory-bank/progress.md`.

## Alternative
Se per un nuovo livello di concorrenza SQLite non è più adatto, Cline deve proporre l'alternativa (SQLite con WAL, PostgreSQL, ecc.) con analisi pro/contro prima di implementare la migrazione.

# Service Architecture Rules

## Struttura dei Servizi
- **Servizio iniziale:** un singolo servizio web dedicato all'effort tracking.
- **Router:** usare `APIRouter(prefix="")` per la root app e prefissi espliciti per eventuali moduli futuri (`/auth`, `/exports`, `/admin`, `/api`).
- **Endpoint:** mantenere distinzione chiara tra pagine HTML e API/azioni di backend.

## Host e Binding
- **Sviluppo:** bindare `0.0.0.0` per accessibilità da rete locale, WSL o VM.
- Quando viene creato il servizio, **annotare nella chat** che in produzione va rivisto il binding, indicando file e riga precisi.

## Static Files (CSS/JS condivisi)
- File statici dell'app vanno in `static/` del progetto oppure in un path condiviso già presente nell'infrastruttura.
- I template devono preferire file CSS/JS condivisi e riusabili.
- **Non duplicare CSS inline** se la stessa regola esiste già nello shared CSS.

## Health Check
- Raccomandato il path `/health` (GET).
- Deve restituire almeno stato applicazione e controllo base della connettività al database.

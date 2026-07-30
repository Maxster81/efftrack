# Security Rules

## Autenticazione
- Per il servizio effort tracking, includere configurazione per autenticazione futura anche se inizialmente disattiva:
  ```python
  SECRET_KEY = os.environ.get("EFFORT_TRACKING_SECRET_KEY", "default-placeholder")
  ALGORITHM = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES = 60
  ```
- L'autenticazione parte **disattiva** per default nelle prime fasi.
- Login user/password e segregazione utenti arrivano **solo nelle fasi finali**.
- MFA **non richiesta** nella prima implementazione.

## Secrets
- Tutti i secrets (SECRET_KEY, password DB, API key) vanno letti da **environment variables**, non hardcodati.
- Fornire un default di sviluppo con placeholder (es. `"cambia-questa-chiave-prima-di-attivare"`).
- Creare `.env.example` quando il progetto arriva a una fase abbastanza stabile.

## Password e Sessioni
- Quando viene introdotta l'autenticazione:
  - password hashate, mai in chiaro
  - sessione sicura o JWT solo se davvero giustificato
  - segregazione dei dati per utente obbligatoria
- Se il progetto resta server-rendered classico, preferire sessioni sicure e semplici rispetto a complessità inutile.

## Sicurezza Applicativa
- Validazione server-side obbligatoria anche se esiste validazione client-side.
- Limitare i campi numerici (`ore_spese`) ai valori consentiti.
- Non fidarsi mai dei valori dei dropdown inviati dal browser: validarli lato server.
- Gli export devono restituire solo i dati autorizzati per l'utente corrente, quando il progetto diventa multiutente.

## JWT (solo se adottato)
- Se si attiva JWT, seguire un pattern coerente e documentato.
- Se si usa `passlib`, pin di `bcrypt` compatibile per evitare incompatibilità note.

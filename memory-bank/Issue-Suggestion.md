# Issue e Suggerimenti (test utente)

> **Nota operativa:** questo file contiene SOLO le issue/suggestion ancora **aperte**.
> Quando una voce viene risolta, va **rimossa** nello stesso commit che la risolve,
> così che il file resti sempre aggiornato e non si accumulino voci già chiuse.

## Suggestion 1 - Visibilità del menu hamburger nella login
**Contesto:** Pagina di login.

**Comportamento attuale:** il menu hamburger è visibile anche nella pagina di login.

**Suggerimento:** nascondere il menu hamburger nella login, poiché potrebbe contenere sezioni riservate a specifiche tipologie di utenti o gruppi di appartenenza.

## Suggestion 2 - Incrementale delle ore
**Contesto:** Nuova registrazione o modifica.

**Comportamento attuale:** Le ore vengono ingramentate di un quarto di ora alla volta

**Suggerimento:** incrementare di mezz'ora alla volta

## Suggestion 3 - Menu a discesa sull'immagine utente
**Contesto:** tutte le pagine, ad eccezione della pagina di login.

**Comportamento attuale:** non è presente alcun menu associato all'immagine o al nome utente.

**Suggerimento:** ripristinare l'immagine utente accanto al nome utente e prevedere, al click sul nome e/o sull'immagine, un menu a discesa con le opzioni disponibili. In questo modo, la voce **ESCI** non dovrebbe più essere mostrata accanto al nome profilo.

**Voci previste del menu:**  
- Profilo  
- ESCI
Aggiornare il suggerimento 3 senza rimuoverlo completamente, seguiranno ulteriori azioni

## Suggestione 4: Prevedere filtro per anni e mesi
**Contesto:** vista Registrazioni, filtro

**Comportamento attuale:** il filtro è su base mensile che inlcude l'anno.

**Suggerimento:** per evitare una colonna di filtro che nel corso del tempo potrebbe diventare enorme, prevedere il filtro sia per anno che per mese, così da avere una colonna mese "bloccata" ai 12 elementi/mesi

## Suggestione 5: Illuminare il record modificato
**Contesto:** vista Registrazioni, filtro

**Comportamento attuale:** alla pressione del pulsante Salva, compare regsitrazione effettuata

**Suggerimento:** oltre a quanto già accade, si può far risaltare nel filtro il record modificato? E' solo una scelta stilistica, di comodità visiva

## Suggestion 6 - Prevedere una checkbox o un radio button per il giorno di ferie
**Contesto:** vista Registrazioni, sezione filtro.

**Comportamento attuale:** non è presente alcuna opzione dedicata ai giorni di ferie.

**Suggerimento:** prevedere una checkbox o un radio button che, se selezionato, renda tutti i campi non obbligatori e non compilabili, ad eccezione della data. Alla pressione di **SALVA**, per quella data verrà creato un record con i campi vuoti e con la dicitura **FERIE** nel campo **NOTE**.

## Suggestion 7 - Verificare la reale necessità di scegliere il gruppo nella registrazione
**Contesto:** vista Registrazioni, sezione filtro.

**Comportamento attuale:** l'utente deve scegliere il gruppo di appartenenza

**Suggerimento:** ma se un utente fa già parte di un gruppo, che necessità c'è di sceglierlo di nuovo durante la registrazione dell'evento? Un po' come il campo User

## Suggestion 6 - Prevedere una checkbox o un radio button per il giorno di ferie
**Contesto:** vista Registrazioni, sezione filtro.

**Comportamento attuale:** non è presente alcuna opzione dedicata ai giorni di ferie.

**Suggerimento:** prevedere una checkbox o un radio button che, se selezionato, renda tutti i campi non obbligatori e non compilabili, ad eccezione della data. Alla pressione di **SALVA**, per quella data verrà creato un record con i campi vuoti e con la dicitura **FERIE** nel campo **NOTE**.

## Suggestion 7 - Verificare la reale utilità del campo Gruppo modificabile
**Contesto:** vista Registrazioni, sezione filtro.

**Comportamento attuale:** Il campo gruppo si può scegliere

**Suggerimento:** quanto è utile scegliere il gruppo durante la registrazione di un evento se tanto un utente può far parte solo di un determinato gruppo? Un po' come il campo User, autopopolato

---

## Issue da verificare (ereditate da progress.md disallineato)

> Le seguenti voci provengono dalla vecchia sezione "Cosa Manca / Da Fare" di `progress.md`
> (numerazione precedente allo sdoppiamento della Fase 12). NON è confermato se siano già
> state risolte: vanno verificate prima di essere considerate chiuse o da fare.
> Quando una voce viene verificata e risolta, va **rimossa** da qui.

### Issue A — Gestione errori 404/500 con pagine HTML dedicate
- **Stato**: 🔴 da verificare
- **Descrizione**: Attualmente gli errori restituiscono JSON o pagine vuote. Servono pagine HTML dedicate per 404 e 500, coerenti con il tema.

### Issue B — Navbar: link "Esporta" non funzionante
- **Stato**: 🔴 da verificare
- **Descrizione**: Il link "Esporta" nella navbar non è funzionante. Va rimosso o reso operativo.

### Issue C — Bottone "Esporta" nella pagina principale è fuori contesto
- **Stato**: 🔴 da verificare
- **Descrizione**: Il pulsante "Esporta CSV" è posizionato nella barra filtri ma non è chiaramente un'azione di export. Valutare se spostarlo in un menu contestuale o in una toolbar dedicata.

### Issue D — Validazione avanzata ore spese (range 1-12, vincoli per Supporto Specialistico)
- **Stato**: 🔴 da verificare
- **Descrizione**: Il campo Ore Spese deve essere validato con range 1-12 (non 0.25-24 come attuale). Per Supporto Specialistico potrebbe esserci un vincolo diverso (es. max 4 ore).

### Issue E — Registrazione automatica data/ora ultimo login
- **Stato**: 🔴 da verificare
- **Descrizione**: Al momento non viene tracciato l'ultimo accesso degli utenti. Aggiungere campo `last_login` alla tabella `users` e popolarlo al login.

### Issue F — Sanificazione input e protezione XSS base
- **Stato**: 🔴 da verificare
- **Descrizione**: Verificare che tutti gli input utente siano sanificati contro XSS. Jinja2 auto-escape è attivo di default, ma verificare note, descrizione e campi testuali.

### Issue G — Verifica sicurezza headers HTTP
- **Stato**: 🔴 da verificare
- **Descrizione**: Aggiungere header di sicurezza HTTP (Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, ecc.) tramite middleware Starlette.

### Issue H — Test funzionali base con pytest
- **Stato**: 🔴 da verificare
- **Descrizione**: I test attuali coprono solo i modelli. Mancano test per:
  - Route web (GET /, POST /, redirect)
  - Route API
  - Autenticazione e permessi
  - Export CSV

### Issue I - Verifica stilistica pagina ADMIN aggiunta utenti- **Stato**: 🔴 da verificare
- **Descrizione**: lo stile della pagina è completamente sballato
 - pulsanti **ruolo, pwd ed elimina** sono enormi rispetto al resto del testo (a che servono 2 pulsanti per lostesso concetto?)
 - **dropdown** ruolo e campo testo **nuova password** piccoli rispetto ai pulsanti (uno dei due va rivisto)
 - **Devo darti uno screenshot per questo issue**

### Issue J - Verifica stilistica pagina ADMIN aggiunta lookup- **Stato**: 🔴 da verificare
- **Descrizione**: lo stile della pagina è completamente sballato
 - pulsante **AGGIUNGI** disallineato rispetto al campo **NOME**
 - vorrei uno stile più tabellare (creare vari mokup)

### Issue K - assegnazione gruppo di appartenenza - **Stato**: 🔴 da verificare
- **Descrizione**: non è possibile assegnare i gruppi a nessun utente
 - durante l'aggiunta di un nuovo utente non è possibile assegnare il gruppo 
- durante la modifica di un  utente esistente non è possibile assegnare il gruppo 

### Issue L - Record orfani dopo eliminazione utente non mostrano il proprietario originale
- **Stato**: 🔴 da verificare
- **Descrizione**: Quando un admin elimina un utente che ha record, i record diventano orfani (user_id=NULL) e restano visibili all'admin ma con colonna "Utente" vuota. Non si sa più a chi appartenessero. Possibili soluzioni:
 - (a) bloccare l'eliminazione di utenti con record associati
 - (b) mantenere lo username originale in una colonna separata (es. `original_username`)
 - (c) soft-delete dell'utente invece di cancellazione fisica
- **Suggerimento** In gestione Lookup si possono creare i gruppi, nella pagina degli utenti sarà possibile associare l'utente ad uno dei gruppi presi dal lookup
# Issue e Suggerimenti (test utente)

> **Nota operativa:** questo file contiene SOLO le issue/suggestion ancora **aperte**.
> Quando una voce viene risolta, va **rimossa** nello stesso commit che la risolve,
> così che il file resti sempre aggiornato e non si accumulino voci già chiuse.

## Suggestion 1 - Visibilità del menu hamburger nella login
**Contesto:** Pagina di login.

**Comportamento attuale:** il menu hamburger è visibile anche nella pagina di login.

**Suggerimento:** nascondere il menu hamburger nella login, poiché potrebbe contenere sezioni riservate a specifiche tipologie di utenti o gruppi di appartenenza.

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

## Suggestion 8 - Eliminazione definitiva utente dopo finestra temporale
**Contesto:** pagina ADMIN Gestione Utenti.

**Comportamento attuale:** l'utente può essere eliminato fisicamente in qualsiasi momento, anche subito dopo la disabilitazione.

**Suggerimento:** prevedere una finestra temporale (es. 30-60 giorni) dopo la **disabilitazione**, trascorsa la quale l'admin potrà eliminare l'utente definitivamente insieme ai suoi record. Durante l'eliminazione mostrare messaggi/warning chiari, es:
 - "L'utente è stato disabilitato il {data}. Sono trascorsi {n} giorni."
 - "L'utente ha {X} record associati che verranno eliminati definitivamente. Sei sicuro?"
 - "Eliminazione consentita dopo almeno 30 giorni dalla disabilitazione."

---

## Issue da verificare (ereditate da progress.md disallineato)

> Le seguenti voci provengono dalla vecchia sezione "Cosa Manca / Da Fare" di `progress.md`
> (numerazione precedente allo sdoppiamento della Fase 12). NON è confermato se siano già
> state risolte: vanno verificate prima di essere considerate chiuse o da fare.
> Quando una voce viene verificata e risolta, va **rimossa** da qui.

### Issue B — Navbar: link "Esporta" non funzionante
- **Stato**: 🔴 da verificare
- **Descrizione**: Il link "Esporta" nella navbar non è funzionante. Va rimosso o reso operativo.

### Issue C — Bottone "Esporta" nella pagina principale è fuori contesto
- **Stato**: 🔴 da verificare
- **Descrizione**: Il pulsante "Esporta CSV" è posizionato nella barra filtri ma non è chiaramente un'azione di export. Valutare se spostarlo in un menu contestuale o in una toolbar dedicata.

### Issue E — Registrazione automatica data/ora ultimo login
- **Stato**: 🔴 da verificare
- **Descrizione**: Al momento non viene tracciato l'ultimo accesso degli utenti. Aggiungere campo `last_login` alla tabella `users` e popolarlo al login.

### Issue F — Sanificazione input e protezione XSS base
- **Stato**: 🔴 da verificare
- **Descrizione**: Verificare che tutti gli input utente siano sanificati contro XSS. Jinja2 auto-escape è attivo di default, ma verificare note, descrizione e campi testuali.

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

<!-- Suggestion 2 risolta in Fase 13b (ore step 0.50). -->
<!-- Issue A risolta in Fase 13b (pagine errore 404/500). -->
<!-- Issue D risolta in Fase 13b (validazione ore 1-12, step 0.50). -->
<!-- Issue G risolta in Fase 13b (header di sicurezza HTTP). -->
<!-- Issue K risolta in Fase 13a (assegnazione gruppo utenti). -->
<!-- Issue L risolta in Fase 13a (disabilita utente con flag disabled). -->

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

## Suggestione 5: Illuminare il record modificato
**Contesto:** vista Registrazioni, filtro

**Comportamento attuale:** alla pressione del pulsante Salva, compare regsitrazione effettuata

**Suggerimento:** oltre a quanto già accade, si può far risaltare nel filtro il record modificato? E' solo una scelta stilistica, di comodità visiva

## Issue da verificare (ereditate da progress.md disallineato)

> Le seguenti voci provengono dalla vecchia sezione "Cosa Manca / Da Fare" di `progress.md`
> (numerazione precedente allo sdoppiamento della Fase 12). NON è confermato se siano già
> state risolte: vanno verificate prima di essere considerate chiuse o da fare.
> Quando una voce viene verificata e risolta, va **rimossa** da qui.

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

### Issue J - Verifica stilistica pagina ADMIN aggiunta lookup- **Stato**: 🔴 da verificare
- **Descrizione**: lo stile della pagina è completamente sballato
 - pulsante **AGGIUNGI** disallineato rispetto al campo **NOME**
 - vorrei uno stile più tabellare (creare vari mokup)

---

## Future Features

> Voci di sviluppo futuro, non assegnate alle fasi correnti. Vengono riportate
> qui quando si decide di non gestirle nella roadmap attiva.

### S4 — Filtro per anno e mese separati
**Contesto:** vista Registrazioni, filtro.

**Descrizione:** separare il filtro mensile (che include l'anno) in due dropdown distinti (Anno + Mese), così la lista dei mesi resta "bloccata" ai 12 valori e non cresce nel tempo.

### S6 — Giorno di ferie
**Contesto:** vista Registrazioni, sezione filtro.

**Descrizione:** prevedere una checkbox o un radio button che, se selezionato, renda tutti i campi non obbligatori e non compilabili, ad eccezione della data. Alla pressione di **SALVA**, per quella data verrà creato un record con i campi vuoti e con la dicitura **FERIE** nel campo **NOTE**.

### S7 — Campo Gruppo autopopolato
**Contesto:** vista Registrazioni, sezione filtro.

**Descrizione:** valutare l'utilità del campo Gruppo modificabile nella registrazione, dato che un utente appartiene già a un gruppo: considerare di renderlo autopopolato come il campo User.

---

<!-- Suggestion 1 risolta in Fase 13c (hamburger nascosto in login). -->
<!-- Suggestion 2 risolta in Fase 13b (ore step 0.50). -->
<!-- Suggestion 5 risolta in Fase 13c (evidenzia record modificato). -->
<!-- Suggestion 3 risolta in Fase 13c (menu utente a discesa). -->
<!-- Suggestion 8 risolta il 2026-08-04 (finestra temporale eliminazione utente). -->
<!-- Issue A risolta in Fase 13b (pagine errore 404/500). -->
<!-- Issue D risolta in Fase 13b (validazione ore 1-12, step 0.50). -->
<!-- Issue E risolta in Fase 12b (campo last_login). -->
<!-- Issue G risolta in Fase 13b (header di sicurezza HTTP). -->
<!-- Issue I risolta in Fase 13c (stile admin utenti ok). -->
<!-- Issue K risolta in Fase 13a (assegnazione gruppo utenti). -->
<!-- Issue L risolta in Fase 13a (disabilita utente con flag disabled). -->

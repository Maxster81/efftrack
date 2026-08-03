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

## Suggesrtion 4: Prevedere filtro per anni e mesi
**Contesto:** vista Registrazioni, filtro

**Comportamento attuale:** il filtro è su base mensile che inlcude l'anno.

**Suggerimento:** per evitare una colonna di filtro che nel corso del tempo potrebbe diventare enorme, prevedere il filtro sia per anno che per mese, così da avere una colonna mese "bloccata" ai 12 elementi/mesi

## Suggesrtion 5: Illuminare il record modificato
**Contesto:** vista Registrazioni, filtro

**Comportamento attuale:** alla pressione del pulsante Salva, compare regsitrazione effettuata

**Suggerimento:** oltre a quanto già accade, si può far risaltare nel filtro il record modificato? E' solo una scelta stilistica, di comodità visiva

## Suggestion 6 - Prevedere una checkbox o un radio button per il giorno di ferie
**Contesto:** vista Registrazioni, sezione filtro.

**Comportamento attuale:** non è presente alcuna opzione dedicata ai giorni di ferie.

**Suggerimento:** prevedere una checkbox o un radio button che, se selezionato, renda tutti i campi non obbligatori e non compilabili, ad eccezione della data. Alla pressione di **SALVA**, per quella data verrà creato un record con i campi vuoti e con la dicitura **FERIE** nel campo **NOTE**.
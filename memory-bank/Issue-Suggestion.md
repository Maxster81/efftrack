# Issue e Suggerimenti (test utente)

> **Nota operativa:** questo file contiene SOLO le issue/suggestion ancora **aperte**.
> Quando una voce viene risolta, va **rimossa** nello stesso commit che la risolve,
> così che il file resti sempre aggiornato e non si accumulino voci già chiuse.

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

## Future Features

> Voci di sviluppo futuro, non assegnate alle fasi correnti. Vengono riportate
> qui quando si decide di non gestirle nella roadmap attiva.

### S9 — Stile tabellare per la pagina ADMIN lookup
**Contesto:** pagina ADMIN Gestione Lookup.

**Descrizione:** refine grafico (non applicativo): la parte di allineamento del pulsante AGGIUNGI al campo NOME è già risolta in Fase 13c, ma restano da migliorare lo stile 'tabellare' della pagina (creare vari mockup). Riassegnata come Suggestion in quanto intervento esclusivamente grafico.

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
<!-- Issue M risolta il 2026-08-04 (riorganizzazione /admin/users: tabella read-only + pagina modifica dedicata). -->
<!-- Issue J riassegnata il 2026-08-04 come S9 (refine grafico stile tabellare lookup, in Future Features). -->

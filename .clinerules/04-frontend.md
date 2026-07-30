# Frontend Rules

## Tecnologia
- **Template engine:** Jinja2 (server-side) — default per il servizio effort tracking.
- **JavaScript:** vanilla JS. Se in futuro l'interattività diventa complessa, proporre HTMX, Alpine o React con analisi pro/contro.
- **CSS:** tutto lo stile condiviso va in `static/`. Non duplicare regole CSS identiche tra template diversi.

## Tema (Dark/Light/System)
Ogni servizio con UI deve implementare il sistema di tema esistente o un suo equivalente coerente:
- Chiave `theme-preference` in localStorage, se il contesto del progetto lo consente.
- Tre modalità: `dark`, `light`, `system`.
- Rilevamento automatico del tema di sistema via `matchMedia`.
- Pulsante toggle nell'header della pagina.
- Variabili CSS in blocco `:root {}` e `[data-theme="light"] {}`.

## Regola di Progetto — Effort Tracking UI
- La UI iniziale deve replicare il paradigma del vecchio tool:
  - form in alto
  - tabella elenco in basso
  - selezione record con popolamento del form
- **Fase iniziale:** prima versione statica del layout, senza logica reale.
- **Fase successiva:** campi realmente interattivi, dropdown hardcoded, validazioni base, show/hide del campo Descrizione.
- **Niente SPA pesante** nelle prime fasi.
- Mantenere UX “single-page feeling” pur con rendering server-side.

## Regole Normative di Accessibilità e Design
Per le regole **normative** su HTML semantico, accessibilità, colori, tipografia, contrasto e coerenza grafica, vedi `09-web-design-10.md`.

## Back-Button Blocker
Se un servizio necessita di bloccare il tasto Back del browser, usare il pattern a **2 pushState**:
```javascript
(function() {
    history.pushState(null, '', window.location.href);
    history.pushState(null, '', window.location.href);
    window.addEventListener('popstate', function() {
        history.pushState(null, '', window.location.href);
    });
})();
```
Ma **non introdurlo per default** nell'effort tracking se non c'è un requisito esplicito.

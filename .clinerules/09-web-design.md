# Web Design & Accessibility Rules

Regole **normative** per HTML semantico, accessibilità, leggibilità, colori, tipografia e coerenza grafica.
Complementare a `04-frontend-5.md` (regole tecnologiche) e `08-workflow-9.md` (regole procedurali con checklist).

---

## 1. HTML Semantico — OBBLIGATORIO

- **Un solo `<h1>` per pagina.** La gerarchia titoli deve essere ordinata (h1→h2→h3), senza salti.
- **`lang` su `<html>`:** sempre presente. Valore dinamico se il template è multilingua (es. `lang="{{ lang }}"`).
- **Tag strutturali:** `<nav>` per navigazione, `<main>` per contenuto principale, `<section>` per sezioni logiche, `<fieldset>`/`<legend>` per gruppi di campi form.
- **Skip-link:** link nascosto all'inizio della pagina che punta a `<main id="main-content">`.

## 2. Form e Input — OBBLIGATORIO

- Ogni `<input>`, `<select>`, `<textarea>` deve avere un `<label>` associato tramite attributo `for` che corrisponde all'`id` dell'input.
- Messaggi di errore: spiegare **cosa è sbagliato** e **come correggere**.
- Campi obbligatori: indicare visivamente (es. asterisco `*` con `aria-required="true"`).
- Placeholder non sostituisce la label.
- Nei form di effort tracking usare raggruppamenti chiari dei campi e nomi coerenti tra UI, schema e database.

## 3. Immagini e Media — OBBLIGATORIO

- **Immagini informative:** attributo `alt` descrittivo.
- **Immagini decorative:** `alt=""`.
- Icone decorative devono essere nascoste agli screen reader con `aria-hidden="true"` se necessario.

## 4. Accessibilità Tastiera — OBBLIGATORIO

- **`:focus-visible` sempre visibile.**
- Ordine di tabulazione logico.
- Tutti i componenti interattivi devono essere raggiungibili e azionabili da tastiera.
- La selezione record in tabella deve essere accessibile anche via tastiera, non solo con click mouse.

## 5. Colori e Contrasto — OBBLIGATORIO

- **Testo normale:** rapporto di contrasto ≥ **4.5:1**.
- **Testo grande** (≥18px bold o ≥24px): ≥ **3:1**.
- **Verificare il contrasto in entrambi i temi** (dark e light).
- Palette definita in `:root` e `[data-theme="light"]` con ruoli chiari.
- **Stati interattivi:** hover, focus, disabled devono avere contrasto adeguato.
- Il layout ispirato alla schermata originale può mantenere una dominante viola, ma senza sacrificare leggibilità e contrasto.

## 6. Tipografia — RACCOMANDAZIONE FORTE

- **Font:** fallback system native stack sempre presente.
- **Scala titoli**:
  - `h1`: ≥ 2rem
  - `h2`: ≥ 1.5rem
  - `h3`: ≥ 1.25rem
- **Line-height:** corpo testo ≥ **1.5**, titoli ≥ **1.2**.
- **Larghezza massima paragrafi:** ~**65–75 caratteri** per testo lungo.
- **Font-weight:** evitare pesi < 400 per testo normale.
- Nei form e nelle tabelle privilegiare leggibilità e densità informativa equilibrata.

## 7. Responsive e Zoom — OBBLIGATORIO

- **Nessun contenuto perso o troncato a zoom 200%.**
- **Nessuno scroll orizzontale non intenzionale** su viewport comuni, salvo tabelle dati dove sia strettamente necessario e gestito visivamente.
- **Breakpoint minimi:**
  - Mobile: < 768px
  - Tablet: 768–1024px
  - Desktop: > 1024px
- **Viewport meta tag** sempre presente.
- Se la tabella non entra su mobile, prevedere strategia esplicita: scroll orizzontale guidato, card view o riduzione colonne.

## 8. Coerenza Grafica — RACCOMANDAZIONE FORTE

- **Riutilizzare classi CSS esistenti** da `static/style.css`.
- Mantenere coerenza tra area form, area elenco e stato selezionato del record.
- **Nuove variabili CSS:** aggiungere sempre per entrambi i temi.
- **Nuovo colore?** Verificare il contrasto in entrambi i temi prima di aggiungerlo.
- Evitare UI troppo “enterprise grigia”: il tool deve restare chiaro, professionale e piacevole da usare.

## 9. Condizioni di Fallimento (BLOCCO DEPLOY)

Queste condizioni impediscono il deploy se non soddisfatte:
1. `<html>` senza attributo `lang`.
2. Input senza `<label>` associata.
3. Immagine informativa senza `alt` corretto.
4. `outline: none` su elemento interattivo senza `:focus-visible` custom.
5. Rapporto di contrasto testo normale < **3:1** in uno dei due temi.
6. `<h1>` multiplo nella stessa pagina.
7. Perdita di contenuto a zoom 200% o scroll orizzontale forzato su viewport ≥ 320px senza gestione esplicita.

## 10. Checklist Pre-Pubblicazione

Checklist da spuntare prima di ogni deploy/release che tocca il frontend:
- [ ] **Tastiera:** focus visibile ovunque.
- [ ] **Zoom 200%:** nessun contenuto perso o troncato.
- [ ] **Contrasto:** verificato in entrambi i temi.
- [ ] **Titoli:** un solo `<h1>`, gerarchia ordinata.
- [ ] **Label:** tutti gli input hanno `<label for="...">`.
- [ ] **`alt`:** tutte le immagini informative hanno `alt` descrittivo.
- [ ] **`lang`:** `<html lang="...">` presente.
- [ ] **Skip-link:** presente e funzionante.
- [ ] **Coerenza CSS:** nessuna regola duplicata rispetto a `static/style.css`.
- [ ] **Responsive:** test mentale su mobile, tablet, desktop.
- [ ] **i18n:** nessuna stringa UI hardcodata in italiano, salvo fallback controllati.

---

## Relazioni con Altre Regole

- `04-frontend-5.md` — regole tecnologiche.
- `08-workflow-9.md` — processo strutturato per task misti BE/FE.
- `00-core.md` — i18n bilingue IT+EN per tutte le UI.

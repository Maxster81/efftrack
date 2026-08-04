/* ------------------------------------------------------------
 * Effort Tracking — logica form.
 *
 * Show/hide condizionale del campo "Descrizione attività" e
 * validazione client-side del form. JavaScript vanilla, niente
 * dipendenze esterne. Il show/hide usa `data-requires-description`
 * dell'attività selezionata (popolata dal DB).
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  // --- Selettori ---
  var form = document.querySelector(".effort-form");
  var errorContainer = document.getElementById("form-error");
  var activitySelect = document.getElementById("effort-activity");
  var descriptionGroup = document.getElementById("description-group");
  var descriptionInput = document.getElementById("effort-description");

  // --- Utility: messaggio + gestione classe errore ---
  function showError(message) {
    if (!errorContainer) { return; }
    errorContainer.textContent = message;
    errorContainer.hidden = false;
  }

  function clearError() {
    if (!errorContainer) { return; }
    errorContainer.textContent = "";
    errorContainer.hidden = true;
  }

  function setInvalid(field, invalid) {
    if (!field) { return; }
    var group = field.closest(".form-group");
    if (group) {
      group.classList.toggle("is-invalid", invalid);
    }
  }

  function validateRequired(field, message) {
    var value = field.value.trim();
    var valid = value.length > 0;
    setInvalid(field, !valid);
    if (!valid) {
      showError(message);
    }
    return valid;
  }

  // --- Show/hide campo Descrizione ---
  // L'attività selezionata espone `data-requires-description` (true/false):
  // se true, la descrizione attività è obbligatoria e il campo va mostrato.
  function activityRequiresDescription() {
    if (!activitySelect || !activitySelect.selectedOptions.length) { return false; }
    var option = activitySelect.selectedOptions[0];
    return option.getAttribute("data-requires-description") === "true";
  }

  function syncDescriptionVisibility() {
    var visible = activityRequiresDescription();
    if (descriptionGroup) {
      descriptionGroup.classList.toggle("is-hidden", !visible);
    }
    // Se la descrizione non è richiesta, pulisce eventuali errori.
    if (!visible && descriptionInput) {
      setInvalid(descriptionInput, false);
    }
  }

  // --- Validazione ore (1 .. 12, multipli di 0.50) ---
  function isValidHours(raw) {
    if (raw.trim() === "") { return false; }
    var value = parseFloat(raw.replace(",", "."));
    if (isNaN(value) || value < 1 || value > 12) { return false; }
    // Multiplo di 0.50: tolleranza floating point.
    return Math.abs(value * 2 - Math.round(value * 2)) < 1e-6;
  }

  // --- Validazione submit ---
  function validateForm() {
    clearError();
    var fields = form.querySelectorAll(".is-invalid");
    Array.prototype.forEach.call(fields, function (field) {
      setInvalid(field, false);
    });

    var valid = true;
    var firstInvalid = null;

    function mark(field, ok) {
      setInvalid(field, !ok);
      if (!ok && !firstInvalid) { firstInvalid = field; }
    }

    // User: obbligatorio solo se NON è readonly (quando loggato è precompilato
    // dal server dalla sessione).
    var user = document.getElementById("effort-user");
    var ok = true;
    if (user && !user.readOnly) {
      ok = validateRequired(user, "Il campo User è obbligatorio.");
      mark(user, ok);
    }
    valid = valid && ok;

    // Data
    var date = document.getElementById("effort-date");
    ok = validateRequired(date, "Il campo Data è obbligatorio.");
    mark(date, ok);
    valid = valid && ok;

    // Cliente
    var client = document.getElementById("effort-client");
    ok = validateSelect(client, "Seleziona un Cliente.");
    mark(client, ok);
    valid = valid && ok;

    // Gruppo: readonly dal DB, non serve validazione client.
    // Il server forza il group_id della sessione.

    // Attività
    ok = validateSelect(activitySelect, "Seleziona un Attività.");
    mark(activitySelect, ok);
    valid = valid && ok;

    // Ore Spese
    var hours = document.getElementById("effort-hours");
    ok = isValidHours(hours.value);
    setInvalid(hours, !ok);
    if (!ok) {
      if (!firstInvalid) { firstInvalid = hours; }
      showError("Inserisci le Ore Spese (da 1 a 12, step 0.50).");
    }
    valid = valid && ok;

    // Descrizione: obbligatoria solo se l'attività la richiede.
    var descRequired = activityRequiresDescription();
    if (descRequired) {
      ok = validateRequired(descriptionInput, "La Descrizione attività è obbligatoria per il Supporto Specialistico.");
      mark(descriptionInput, ok);
      valid = valid && ok;
    }

    // Focus sul primo campo non valido + messaggio d'errore.
    if (!valid && firstInvalid) {
      firstInvalid.focus();
    }

    return valid;
  }

  // Wrapper per le select (valore non vuoto).
  function validateSelect(field, message) {
    var valid = Boolean(field && field.value);
    setInvalid(field, !valid);
    if (!valid) {
      showError(message);
    }
    return valid;
  }

  // --- Event listeners ---
  if (form) {
    form.addEventListener("submit", function (event) {
      // La cancellazione non richiede la validazione dei campi del form:
      // serve solo `record_id` (già valorizzato da row-select.js).
      var submitter = event.submitter;
      if (submitter && submitter.id === "edit-delete") {
        return;
      }
      if (!validateForm()) {
        event.preventDefault();
      }
    });

    // Rimuove l'errore dal campo al change/input.
    form.addEventListener("change", function (event) {
      var field = event.target;
      if (field.id === "effort-activity") {
        syncDescriptionVisibility();
      }
      if (field.classList && !field.classList.contains("is-invalid")) {
        setInvalid(field, false);
      }
    });
    form.addEventListener("input", function (event) {
      setInvalid(event.target, false);
    });
  }

  // Espone helper riusabili da row-select.js.
  window.EffortTrack = window.EffortTrack || {};
  window.EffortTrack.syncDescriptionVisibility = syncDescriptionVisibility;

  // --- Inizializzazione ---
  syncDescriptionVisibility();
})();

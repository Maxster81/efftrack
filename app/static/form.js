/* ------------------------------------------------------------
 * Effort Tracking — logica form (Fase 3).
 *
 * Show/hide condizionale del campo "Descrizione attività" e
 * validazione client-side del form. JavaScript vanilla, niente
 * dipendenze esterne. La validazione server-side arriverà in Fase 5.
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  // --- Selettori ---
  var form = document.querySelector(".effort-form");
  var errorContainer = document.getElementById("form-error");
  var activitySelect = document.getElementById("effort-activity");
  var descriptionGroup = document.getElementById("description-group");
  var descriptionInput = document.getElementById("effort-description");

  // Valore che rende visibile (e obbligatoria) la descrizione.
  var SUPPORT_ACTIVITY = "SOC-Supporto Specialistico";

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
  function syncDescriptionVisibility() {
    var visible = activitySelect && activitySelect.value === SUPPORT_ACTIVITY;
    if (descriptionGroup) {
      descriptionGroup.classList.toggle("is-hidden", !visible);
    }
    // Se la descrizione non è richiesta, pulisce eventuali errori.
    if (!visible && descriptionInput) {
      setInvalid(descriptionInput, false);
    }
  }

  // --- Validazione ore (0.25 .. 24, multipli di 0.25) ---
  function isValidHours(raw) {
    if (raw.trim() === "") { return false; }
    var value = parseFloat(raw.replace(",", "."));
    if (isNaN(value) || value < 0.25 || value > 24) { return false; }
    // Multiplo di 0.25: tolleranza floating point.
    return Math.abs(value * 4 - Math.round(value * 4)) < 1e-6;
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

    // User
    var user = document.getElementById("effort-user");
    var ok = validateRequired(user, "Il campo User è obbligatorio.");
    mark(user, ok);
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

    // Gruppo
    var group = document.getElementById("effort-group");
    ok = validateSelect(group, "Seleziona un Gruppo.");
    mark(group, ok);
    valid = valid && ok;

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
      showError("Inserisci le Ore Spese (da 0.25 a 24, step 0.25).");
    }
    valid = valid && ok;

    // Descrizione: obbligatoria solo se l'attività la richiede.
    var descRequired = activitySelect && activitySelect.value === SUPPORT_ACTIVITY;
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

  // --- Inizializzazione ---
  syncDescriptionVisibility();
})();
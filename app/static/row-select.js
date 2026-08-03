/* ------------------------------------------------------------
 * Effort Tracking — selezione record dalla tabella (Fase 7).
 *
 * Click su una riga della tabella popola il form con i dati del
 * record e attiva la "modalità modifica": il campo hidden `record_id`
 * viene valorizzato, il pulsante "Copia su settimana" viene nascosto
 * (la copia bulk ha senso solo in inserimento), appaiono i pulsanti
 * "Annulla modifica" e "Elimina registrazione". Al submit il POST
 * invia `record_id` e la route aggiorna il record esistente; con
 * `action=delete` la route elimina definitivamente il record.
 *
 * Comportamento accessibile: le righe hanno `role="button"` e
 * `tabindex="0"`, quindi rispondono anche a Enter/Spazio.
 * JavaScript vanilla, nessuna dipendenza esterna.
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  // --- Selettori ---
  var rows = document.querySelectorAll(".records-table__row[data-record-id]");
  var recordIdInput = document.getElementById("record-id");
  var form = document.querySelector(".effort-form");
  var weekAction = document.getElementById("week-action");
  var editCancel = document.getElementById("edit-cancel");
  var editDelete = document.getElementById("edit-delete");
  var titleText = document.getElementById("form-title-text");
  var titleEdit = document.getElementById("form-title-edit");

  // Campo del form popolati al click.
  var userInput = document.getElementById("effort-user");
  var dateInput = document.getElementById("effort-date");
  var clientSelect = document.getElementById("effort-client");
  var groupSelect = document.getElementById("effort-group");
  var activitySelect = document.getElementById("effort-activity");
  var hoursInput = document.getElementById("effort-hours");
  var notesInput = document.getElementById("effort-notes");
  var descriptionInput = document.getElementById("effort-description");

  var selectedRow = null;

  function isEditMode() {
    return !!(recordIdInput && recordIdInput.value);
  }

  function setSelectedRow(row) {
    if (selectedRow) {
      selectedRow.classList.remove("is-selected");
      selectedRow.setAttribute("aria-selected", "false");
    }
    selectedRow = row;
    if (selectedRow) {
      selectedRow.classList.add("is-selected");
      selectedRow.setAttribute("aria-selected", "true");
    }
  }

  // Popola il form con i data-* del record cliccato.
  function populateForm(row) {
    if (!row) { return; }

    if (userInput) { userInput.value = row.getAttribute("data-user") || ""; }
    if (dateInput) { dateInput.value = row.getAttribute("data-date") || ""; }
    if (clientSelect) {
      clientSelect.value = row.getAttribute("data-client-id") || "";
    }
    if (groupSelect) {
      groupSelect.value = row.getAttribute("data-group-id") || "";
    }
    if (activitySelect) {
      activitySelect.value = row.getAttribute("data-activity-id") || "";
    }
    if (hoursInput) {
      hoursInput.value = row.getAttribute("data-hours") || "";
    }
    if (notesInput) { notesInput.value = row.getAttribute("data-notes") || ""; }
    if (descriptionInput) {
      descriptionInput.value = row.getAttribute("data-description") || "";
    }

    // Ricalcola la visibilità della descrizione in base all'attività.
    if (window.EffortTrack && typeof window.EffortTrack.syncDescriptionVisibility === "function") {
      window.EffortTrack.syncDescriptionVisibility();
    }
  }

  // Attiva la modalità modifica per una riga.
  function editRecord(row) {
    if (!row || !recordIdInput || !editCancel || !weekAction) { return; }

    recordIdInput.value = row.getAttribute("data-record-id") || "";
    populateForm(row);
    setSelectedRow(row);

    // L'inserimento bulk non è consentito in modifica; compaiono i
    // pulsanti "Annulla modifica" ed "Elimina registrazione".
    weekAction.classList.add("is-hidden");
    editCancel.classList.remove("is-hidden");
    if (editDelete) { editDelete.classList.remove("is-hidden"); }
    if (titleText) { titleText.hidden = true; }
    if (titleEdit) { titleEdit.hidden = false; }
  }

  // Esce dalla modalità modifica e resetta il form al default.
  function clearEdit() {
    if (recordIdInput) { recordIdInput.value = ""; }
    if (form) { form.reset(); }
    if (dateInput) { dateInput.value = new Date().toISOString().slice(0, 10); }

    setSelectedRow(null);

    if (weekAction) { weekAction.classList.remove("is-hidden"); }
    if (editCancel) { editCancel.classList.add("is-hidden"); }
    if (editDelete) { editDelete.classList.add("is-hidden"); }
    if (titleText) { titleText.hidden = false; }
    if (titleEdit) { titleEdit.hidden = true; }

    // Ricalcola la visibilità della descrizione sullo stato iniziale.
    if (window.EffortTrack && typeof window.EffortTrack.syncDescriptionVisibility === "function") {
      window.EffortTrack.syncDescriptionVisibility();
    }
  }

  // --- Event listeners sulle righe ---
  Array.prototype.forEach.call(rows, function (row) {
    // Click del mouse.
    row.addEventListener("click", function () {
      editRecord(row);
    });

    // Tastiera: invio/spazio replicano il click (accessibilità).
    row.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        editRecord(row);
      }
    });
  });

  // Annulla la modalità modifica.
  if (editCancel) {
    editCancel.addEventListener("click", clearEdit);
  }

  // Conferma prima della cancellazione definitiva: se l'utente clicca
  // "Elimina registrazione" e annulla, il submit viene bloccato.
  if (form) {
    form.addEventListener("submit", function (event) {
      var submitter = event.submitter;
      if (submitter && submitter.id === "edit-delete") {
        if (!window.confirm("Eliminare definitivamente questa registrazione?")) {
          event.preventDefault();
        }
      }
    });
  }

  // Espone helper riusabili da form.js.
  window.EffortTrack = window.EffortTrack || {};
  window.EffortTrack.clearEdit = clearEdit;
  window.EffortTrack.isEditMode = isEditMode;
})();
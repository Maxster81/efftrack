/* ------------------------------------------------------------
 * Effort Tracking — logica sidebar navigazione (Fase 4b).
 *
 * Gestisce l'apertura/chiusura del menu hamburger: click sul
 * pulsante hamburger, click sulla X di chiusura, click sull'overlay
 * e tasto ESC. JavaScript vanilla, nessuna dipendenza esterna.
 * Le voci del menu verranno popolate in base al ruolo nelle Fasi 12-13.
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  var toggleBtn = document.getElementById("nav-toggle");
  var sidebar = document.getElementById("app-sidebar");
  var overlay = document.getElementById("sidebar-overlay");
  var closeBtn = document.getElementById("sidebar-close");

  function openSidebar() {
    if (!sidebar || !overlay) { return; }
    sidebar.classList.add("is-open");
    overlay.hidden = false;
    if (toggleBtn) {
      toggleBtn.setAttribute("aria-expanded", "true");
      toggleBtn.setAttribute("aria-label", "Chiudi menu di navigazione");
    }
  }

  function closeSidebar() {
    if (!sidebar || !overlay) { return; }
    sidebar.classList.remove("is-open");
    overlay.hidden = true;
    if (toggleBtn) {
      toggleBtn.setAttribute("aria-expanded", "false");
      toggleBtn.setAttribute("aria-label", "Apri menu di navigazione");
    }
  }

  function isOpen() {
    return Boolean(sidebar && sidebar.classList.contains("is-open"));
  }

  // Apertura/chiusura via hamburger.
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      if (isOpen()) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  // Chiusura via X.
  if (closeBtn) {
    closeBtn.addEventListener("click", closeSidebar);
  }

  // Chiusura via click sull'overlay.
  if (overlay) {
    overlay.addEventListener("click", closeSidebar);
  }

  // Chiusura con tasto ESC.
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && isOpen()) {
      closeSidebar();
    }
  });
})();
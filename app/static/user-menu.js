/* Menu a discesa utente (Fase 13c, Suggestion 3).
 *
 * Apre/chiude il menu al click sul toggle, lo chiude su click esterno e su
 * ESC. Le voci "Profilo" ed "Esci" sono link diretti.
 */
(function () {
  "use strict";

  var dropdown = document.querySelector("[data-user-menu]");
  if (!dropdown) {
    return;
  }

  var toggle = document.getElementById("user-menu-toggle");
  var menu = document.getElementById("user-menu");

  function setOpen(open) {
    if (!menu) { return; }
    menu.classList.toggle("is-open", open);
    if (toggle) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Chiudi menu utente" : "Apri menu utente");
    }
  }

  if (toggle && menu) {
    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      setOpen(!menu.classList.contains("is-open"));
    });
  }

  // Il click su una voce del menu (link) lo chiude automaticamente.
  if (menu) {
    menu.addEventListener("click", function (event) {
      var link = event.target.closest("a");
      if (link && link.getAttribute("href") !== "#") {
        setOpen(false);
      }
    });
  }

  // Chiude il menu su click fuori dal dropdown.
  document.addEventListener("click", function (event) {
    if (dropdown && !dropdown.contains(event.target)) {
      setOpen(false);
    }
  });

  // Chiude il menu con il tasto ESC.
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      setOpen(false);
    }
  });
})();

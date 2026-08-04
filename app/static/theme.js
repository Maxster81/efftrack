/* ------------------------------------------------------------
 * Effort Tracking — toggle tema dark/light.
 *
 * Due sole modalità (dark / light), nessun rilevamento automatico
 * del sistema. La preferenza è salvata in localStorage con chiave
 * `theme-preference` e riapplicata al caricamento della pagina.
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  var STORAGE_KEY = "theme-preference";
  var root = document.documentElement;

  /**
   * Legge la preferenza salvata. Default: "light".
   * @returns {string} "dark" | "light"
   */
  function getStoredTheme() {
    var value = null;
    try {
      value = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      // localStorage non disponibile (privacy mode): ignora, default light.
    }
    return value === "dark" ? "dark" : "light";
  }

  /**
   * Applica il tema all'elemento <html> aggiornando data-theme e l'icona.
   * @param {string} theme - "dark" | "light"
   */
  function applyTheme(theme) {
    var isDark = theme === "dark";
    if (isDark) {
      root.setAttribute("data-theme", "dark");
    } else {
      root.removeAttribute("data-theme");
    }

    // Aggiorna il pulsante toggle (icona + label accessibile).
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.setAttribute("aria-label", isDark ? "Passa al tema chiaro" : "Passa al tema scuro");
      btn.setAttribute("title", isDark ? "Tema scuro attivo — passa al chiaro" : "Tema chiaro attivo — passa allo scuro");
      var icon = document.getElementById("theme-toggle-icon");
      if (icon) {
        icon.textContent = isDark ? "☀️" : "🌙";
      }
    }
  }

  /**
   * Alterna il tema corrente e salva la preferenza.
   */
  function toggleTheme() {
    var next = getStoredTheme() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {
      // localStorage non disponibile: il toggle resta attivo solo per la sessione.
    }
    applyTheme(next);
  }

  // Inizializzazione: applica il tema salvato al primo caricamento.
  applyTheme(getStoredTheme());

  // Collega il toggle al pulsante nell'header.
  var btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", toggleTheme);
  }
})();
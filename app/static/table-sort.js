/* ------------------------------------------------------------
 * Effort Tracking — ordinamento tabella (client-side).
 *
 * Gli header con classe .sortable e attributo data-sort-key sono
 * cliccabili: ad ogni click le righe del tbody vengono ordinate in
 * base al valore data-sort della colonna corrispondente.
 * - data-sort-type="number" → confronto numerico (es. colonna Record).
 * - altrimenti → confronto stringa (localeCompare, case-insensitive).
 * Il dato di ordinamento delle celle è esposto via data-sort (in
 * particolare per le date si usa il timestamp ISO, non la stringa
 * formattata, così l'ordinamento lessicografico è corretto).
 * Aggiorna aria-sort sull'header e l'indicatore ▲/▼.
 * JavaScript vanilla, nessuna dipendenza esterna.
 * ------------------------------------------------------------ */
(function () {
  "use strict";

  var table = document.getElementById("users-table");
  if (!table || !table.tHead || !table.tBodies[0]) {
    return;
  }

  var tbody = table.tBodies[0];
  var headerRow = table.tHead.rows[0];
  var headerCells = headerRow ? headerRow.cells : [];
  var headers = Array.prototype.filter.call(
    headerCells,
    function (cell) {
      return cell.hasAttribute("data-sort-key");
    }
  );

  var currentKey = null;
  var currentDirection = 1; // 1 = crescente, -1 = decrescente

  function indexOfHeader(header) {
    for (var i = 0; i < headerCells.length; i++) {
      if (headerCells[i] === header) {
        return i;
      }
    }
    return -1;
  }

  function readSortValue(cell) {
    return cell ? (cell.getAttribute("data-sort") || "") : "";
  }

  function sortRows(header, direction) {
    var col = indexOfHeader(header);
    var type = header.getAttribute("data-sort-type") || "string";
    if (col < 0) {
      return;
    }

    var rows = Array.prototype.slice.call(tbody.rows);
    rows.sort(function (a, b) {
      var aVal = readSortValue(a.cells[col]);
      var bVal = readSortValue(b.cells[col]);
      var cmp;
      if (type === "number") {
        var na = parseFloat(aVal) || 0;
        var nb = parseFloat(bVal) || 0;
        cmp = na - nb;
      } else {
        cmp = aVal.localeCompare(bVal, undefined, { sensitivity: "base" });
      }
      return cmp * direction;
    });

    rows.forEach(function (row) {
      tbody.appendChild(row);
    });
  }

  function setIndicator(header, text) {
    var indicator = header.querySelector(".sort-indicator");
    if (indicator) {
      indicator.textContent = text;
    }
  }

  function updateHeaderState() {
    headers.forEach(function (header) {
      var key = header.getAttribute("data-sort-key");
      if (key === currentKey) {
        header.setAttribute(
          "aria-sort",
          currentDirection === 1 ? "ascending" : "descending"
        );
        setIndicator(header, currentDirection === 1 ? "▲" : "▼");
      } else {
        header.setAttribute("aria-sort", "none");
        setIndicator(header, "");
      }
    });
  }

  function onHeaderClick(header) {
    var key = header.getAttribute("data-sort-key");
    if (currentKey === key) {
      currentDirection = -currentDirection;
    } else {
      currentKey = key;
      currentDirection = 1;
    }
    sortRows(header, currentDirection);
    updateHeaderState();
  }

  headers.forEach(function (header) {
    header.addEventListener("click", function () {
      onHeaderClick(header);
    });
    // Accessibilità: tastiera replica il click sugli header ordinabili.
    header.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onHeaderClick(header);
      }
    });
    header.setAttribute("tabindex", "0");
  });
})();

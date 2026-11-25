

document.addEventListener("DOMContentLoaded", function () {
  /* Mobile dashboard sidebar ------------------------------------------ */
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const sidebarToggle = document.getElementById("sidebarToggle");

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("show");
  }

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      if (backdrop) backdrop.classList.toggle("show");
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  /* Mobile public navigation ------------------------------------------ */
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }

  /* Flash messages ----------------------------------------------------- */
  document.querySelectorAll(".flash").forEach(function (flash) {
    const close = flash.querySelector(".flash-close");
    if (close) {
      close.addEventListener("click", function () { flash.remove(); });
    }
    window.setTimeout(function () {
      flash.style.transition = "opacity .3s, transform .3s";
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-6px)";
      window.setTimeout(function () { flash.remove(); }, 320);
    }, 7000);
  });

  /* Confirmation for destructive actions ------------------------------- */
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      if (!window.confirm(el.getAttribute("data-confirm"))) {
        event.preventDefault();
        event.stopPropagation();
      }
    });
  });

  /* Tiny client-side table search -------------------------------------- */
  document.querySelectorAll("[data-table-filter]").forEach(function (input) {
    const table = document.querySelector(input.getAttribute("data-table-filter"));
    if (!table) return;
    input.addEventListener("input", function () {
      const term = input.value.toLowerCase().trim();
      table.querySelectorAll("tbody tr").forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  });

  /* Auto-submit filter selects ----------------------------------------- */
  document.querySelectorAll("[data-auto-submit]").forEach(function (select) {
    select.addEventListener("change", function () {
      if (select.form) select.form.submit();
    });
  });
});

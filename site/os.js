/* Franchetti Raw Converter Pro — pagina Linux e macOS
   Tab dei comandi, copia negli appunti, comparsa degli elementi. */
(function () {
  "use strict";

  /* --- Tab dei comandi --------------------------------------------------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-lx-tab]"));
  var panels = Array.prototype.slice.call(document.querySelectorAll("[data-lx-panel]"));

  function mostra(nome) {
    tabs.forEach(function (tab) {
      var attivo = tab.getAttribute("data-lx-tab") === nome;
      tab.classList.toggle("is-active", attivo);
      tab.setAttribute("aria-selected", attivo ? "true" : "false");
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-lx-panel") !== nome;
    });
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      mostra(tab.getAttribute("data-lx-tab"));
    });
  });

  /* --- Copia negli appunti ---------------------------------------------- */
  function testoDi(pulsante) {
    var modo = pulsante.getAttribute("data-lx-copy");
    if (modo === "active") {
      var visibile = panels.filter(function (p) { return !p.hidden; })[0];
      return visibile ? visibile.textContent : "";
    }
    var nodo = modo ? document.querySelector(modo) : null;
    return nodo ? nodo.textContent : "";
  }

  function conferma(pulsante) {
    if (!pulsante._testoOriginale) pulsante._testoOriginale = pulsante.innerHTML;
    pulsante.classList.add("is-done");
    pulsante.textContent = "Copiato";
    window.setTimeout(function () {
      pulsante.classList.remove("is-done");
      pulsante.innerHTML = pulsante._testoOriginale;
    }, 1800);
  }

  function copia(testo, pulsante) {
    if (!testo) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(testo).then(function () {
        conferma(pulsante);
      }).catch(function () {
        vecchioMetodo(testo, pulsante);
      });
      return;
    }
    vecchioMetodo(testo, pulsante);
  }

  function vecchioMetodo(testo, pulsante) {
    var area = document.createElement("textarea");
    area.value = testo;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      conferma(pulsante);
    } catch (e) {
      /* niente: l'utente può selezionare il testo a mano */
    }
    document.body.removeChild(area);
  }

  Array.prototype.slice.call(document.querySelectorAll("[data-lx-copy]")).forEach(function (pulsante) {
    pulsante.addEventListener("click", function () {
      copia(testoDi(pulsante), pulsante);
    });
  });

  /* --- Comparsa graduale (solo se app.js non l'ha già impostata) --------- */
  if (document.documentElement.classList.contains("js-reveal")) return;

  var ridotto = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var elementi = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));
  if (ridotto || !("IntersectionObserver" in window) || !elementi.length) return;

  document.documentElement.classList.add("js-reveal");
  elementi.forEach(function (el) {
    el.style.opacity = "0";
    el.style.transform = "translateY(14px)";
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
  });

  var osservatore = new IntersectionObserver(function (voci) {
    voci.forEach(function (voce) {
      if (!voce.isIntersecting) return;
      voce.target.style.opacity = "1";
      voce.target.style.transform = "none";
      osservatore.unobserve(voce.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

  elementi.forEach(function (el) { osservatore.observe(el); });
})();

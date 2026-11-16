/* Interazioni minime: ombra della barra allo scroll e comparsa progressiva.
   Se lo script non parte, la pagina resta completamente leggibile: le classi
   che nascondono gli elementi vengono aggiunte solo da qui. */
(function () {
  "use strict";

  var nav = document.getElementById("nav");
  var onScroll = function () {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 24);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var items = Array.prototype.slice.call(document.querySelectorAll("[data-reveal]"));

  if (prefersReduced || !("IntersectionObserver" in window)) return;

  document.documentElement.classList.add("js-reveal");

  var reveal = function (el, delay) {
    el.style.transitionDelay = (delay || 0) + "ms";
    el.classList.add("is-visible");
  };

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      var parent = el.parentElement;
      var siblings = parent ? Array.prototype.slice.call(parent.children).filter(function (c) {
        return c.hasAttribute && c.hasAttribute("data-reveal");
      }) : [];
      var index = siblings.indexOf(el);
      reveal(el, index > 0 ? Math.min(index * 70, 350) : 0);
      observer.unobserve(el);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

  /* Tutto ciò che è già stato superato (salto a un'ancora, ritorno alla pagina,
     stampa) va mostrato subito: altrimenti resterebbe invisibile per sempre. */
  var revealPassed = function () {
    var limit = window.innerHeight * 0.92;
    items = items.filter(function (el) {
      if (el.classList.contains("is-visible")) return false;
      var rect = el.getBoundingClientRect();
      if (rect.top >= limit) return true;
      reveal(el, 0);
      observer.unobserve(el);
      return false;
    });
  };

  window.addEventListener("scroll", revealPassed, { passive: true });
  window.addEventListener("hashchange", revealPassed);
  window.addEventListener("pageshow", revealPassed);
  window.addEventListener("beforeprint", function () {
    items.forEach(function (el) { reveal(el, 0); });
  });

  for (var j = 0; j < items.length; j++) observer.observe(items[j]);
  revealPassed();
})();

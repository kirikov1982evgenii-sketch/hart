/** Яндекс.Метрика — ID в config.js (HART_YANDEX_METRIKA_ID при сборке). */
(function (global) {
  const id = String(global.SITE_CONFIG?.yandexMetrikaId || "").replace(/\D/g, "");
  if (!id) return;

  (function (m, e, t, r, i, k, a) {
    m[i] =
      m[i] ||
      function () {
        (m[i].a = m[i].a || []).push(arguments);
      };
    m[i].l = 1 * new Date();
    for (k = 0; k < e.scripts.length; k++) {
      if (e.scripts[k].src === r) return;
    }
    a = e.createElement(t);
    a.async = 1;
    a.src = r;
    e.head.appendChild(a);
  })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

  global.ym(id, "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: false,
  });
})(window);

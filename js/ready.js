/** Запуск после DOM (не пропускает событие, если страница уже готова). */
(function (global) {
  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }
  global.HartReady = { onReady };
})(window);

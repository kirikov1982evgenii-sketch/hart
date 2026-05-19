/** Счётчик просмотров главной (API на PythonAnywhere). */
(function (global) {
  const STORAGE = "hart_view_hit";

  function apiBase() {
    return (global.SITE_CONFIG?.paymentApiUrl || "").replace(/\/$/, "");
  }

  function fmt(n) {
    const lang = global.HartI18n?.getLang?.() || document.documentElement.lang || "ru";
    try {
      return Number(n).toLocaleString(lang === "ru" ? "ru-RU" : "en-US");
    } catch {
      return String(n);
    }
  }

  function paint(total) {
    const el = document.getElementById("stat-views");
    if (el) el.textContent = fmt(total);
    const og = document.querySelector('meta[property="og:description"]');
    if (og && total > 0) {
      const base = og.getAttribute("data-base-desc") || og.content;
      if (!og.getAttribute("data-base-desc")) og.setAttribute("data-base-desc", base);
      const views = global.HartI18n?.t?.("stat.views_count", { n: fmt(total) }) || `${fmt(total)} просмотров`;
      og.content = `${base} · ${views}`;
    }
  }

  async function fetchViews() {
    const base = apiBase();
    if (!base) return null;
    const r = await fetch(`${base}/api/views`, { credentials: "omit" });
    if (!r.ok) return null;
    const j = await r.json();
    return j.ok ? j.total : null;
  }

  async function hit(page) {
    const base = apiBase();
    if (!base) return null;
    const r = await fetch(`${base}/api/views/hit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "omit",
      body: JSON.stringify({ page: page || "index" }),
    });
    if (!r.ok) return null;
    const j = await r.json();
    return j.ok ? j.total : null;
  }

  async function init(page) {
    const key = `${STORAGE}_${page || "index"}`;
    let total = null;
    try {
      if (!sessionStorage.getItem(key)) {
        total = await hit(page);
        if (total != null) sessionStorage.setItem(key, "1");
      }
    } catch {
      /* private mode */
    }
    if (total == null) total = await fetchViews();
    if (total != null) paint(total);
  }

  global.HartViews = { init, fmt };
})(window);

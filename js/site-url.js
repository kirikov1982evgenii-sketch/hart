/** Публичный адрес сайта из config.js */
(function (global) {
  function base() {
    const u = (global.SITE_CONFIG?.siteUrl || global.location?.origin || "").replace(/\/$/, "");
    if (u && !u.startsWith("http://localhost") && !u.startsWith("http://127.0.0.1")) {
      return u;
    }
    if (global.location?.origin && !global.location.origin.startsWith("file:")) {
      return global.location.origin + global.location.pathname.replace(/\/[^/]*$/, "").replace(/\/$/, "");
    }
    return u || "";
  }

  function pretty() {
    return base().replace(/^https?:\/\//, "");
  }

  function path(page) {
    const b = base();
    if (!page) return b + "/";
    const p = page.startsWith("/") ? page : "/" + page;
    return b + p;
  }

  function setCanonical() {
    const page = global.location?.pathname?.split("/").pop() || "index.html";
    const url = page === "index.html" || !page ? base() + "/" : path(page);
    let link = document.querySelector('link[rel="canonical"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "canonical";
      document.head.appendChild(link);
    }
    link.href = url;
  }

  function mountShare(elId) {
    const el = document.getElementById(elId);
    if (!el) return;
    const url = base() + "/";
    const label = pretty();
    el.innerHTML = `
      <div class="site-share">
        <span class="site-share-label">Сайт клуба</span>
        <a class="site-share-url" href="${url}" target="_blank" rel="noopener">${label}</a>
        <button type="button" class="btn btn-outline btn-sm site-share-copy" data-url="${url}">Копировать</button>
      </div>`;
    el.querySelector(".site-share-copy")?.addEventListener("click", async (e) => {
      const u = e.currentTarget.getAttribute("data-url") || url;
      try {
        await navigator.clipboard.writeText(u);
        e.currentTarget.textContent = "Скопировано";
        setTimeout(() => {
          e.currentTarget.textContent = "Копировать";
        }, 2000);
      } catch {
        prompt("Ссылка:", u);
      }
    });
  }

  global.HartSiteUrl = { base, pretty, path, setCanonical, mountShare };
})(window);

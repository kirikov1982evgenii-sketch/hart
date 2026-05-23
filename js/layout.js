/** Шапка, подвал, язык и регион. */
(function () {
  const cfg = () => window.SITE_CONFIG || {};
  const brand = () => cfg().brand || "Клуб знаний";
  const accent = () => cfg().accent || "HART";

  function t(key) {
    return window.HartI18n?.t?.(key) || key;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function langOptions() {
    const langs = window.HartI18n?.languages?.() || [["en", "English"]];
    const cur = window.HartI18n?.getLang?.() || "en";
    return langs
      .map(
        ([code, name]) =>
          `<option value="${code}"${code === cur ? " selected" : ""}>${escapeHtml(name)}</option>`
      )
      .join("");
  }

  function mountHeader() {
    const el = document.getElementById("site-header");
    if (!el) return;
    const logged = window.HartSession?.isLoggedIn?.();
    const email = logged ? window.HartSession.getEmail() : "";
    const region = window.HartI18n?.getRegion?.() || "intl";
    el.innerHTML = `
      <header class="site-header">
        <a href="index.html" class="logo-link">
          <span class="logo-brand">${brand()}</span>
          <span class="logo-accent">${accent()}</span>
        </a>
        <button type="button" class="nav-toggle" id="nav-toggle" aria-expanded="false" aria-label="${t("nav.menu")}">☰</button>
        <nav class="site-nav" id="site-nav">
          <a href="index.html" data-i18n="nav.catalog">Catalog</a>
          <a href="cabinet.html" data-i18n="nav.cabinet">Account</a>
          <a href="support.html" data-i18n="nav.support">Support</a>
        </nav>
        <div class="header-controls">
          <label class="sr-only" data-i18n="lang.label">Language</label>
          <select id="lang-select" class="header-select" aria-label="Language">${langOptions()}</select>
          <select id="region-select" class="header-select" aria-label="Region">
            <option value="ru"${region === "ru" ? " selected" : ""}>${t("region.ru")}</option>
            <option value="intl"${region !== "ru" ? " selected" : ""}>${t("region.intl")}</option>
          </select>
        </div>
        <div class="header-user">
          ${
            logged
              ? `<span class="user-email">${escapeHtml(email)}</span>
                 <button type="button" class="btn-ghost btn-sm" id="btn-logout" data-i18n="nav.logout">Log out</button>`
              : `<a href="cabinet.html" class="btn-gold btn-sm" data-i18n="nav.login">Sign in</a>`
          }
        </div>
      </header>`;
    document.getElementById("lang-select")?.addEventListener("change", (e) => {
      window.HartI18n?.setLang?.(e.target.value);
      mountHeader();
      mountFooter();
    });
    document.getElementById("region-select")?.addEventListener("change", (e) => {
      window.HartI18n?.setRegion?.(e.target.value);
      mountHeader();
    });
    document.getElementById("btn-logout")?.addEventListener("click", () => {
      window.HartSession?.clearSession?.();
      location.href = "index.html";
    });
    const toggle = document.getElementById("nav-toggle");
    const nav = document.getElementById("site-nav");
    const header = el.querySelector(".site-header");
    toggle?.addEventListener("click", () => {
      const open = header.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav?.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        header.classList.remove("nav-open");
        toggle?.setAttribute("aria-expanded", "false");
      });
    });
    window.HartI18n?.applyDom?.(el);
  }

  function mountFooter() {
    const el = document.getElementById("site-footer");
    if (!el) return;
    el.innerHTML = `
      <footer class="site-footer">
        <p class="footer-brand">${brand()} <span>${accent()}</span></p>
        <p class="footer-tagline">${cfg().tagline || ""}</p>
        <p>
          <a href="support.html" data-i18n="nav.support">Support</a> ·
          <a href="${cfg().telegramBot || "https://t.me/uportbot"}" target="_blank" rel="noopener">@uportbot</a>
        </p>
        <p class="footer-copy" data-i18n="footer.copy">© ${new Date().getFullYear()}</p>
      </footer>`;
    window.HartI18n?.applyDom?.(el);
  }

  async function boot() {
    mountHeader();
    mountFooter();
    if (window.HartI18n && !window.HartI18n.ready) {
      try {
        await Promise.race([
          window.HartI18n.init(),
          new Promise((_, reject) => setTimeout(() => reject(new Error("i18n timeout")), 4000)),
        ]);
        mountHeader();
        mountFooter();
      } catch {
        /* шапка уже показана */
      }
    }
  }

  const run = window.HartReady?.onReady || ((fn) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  });
  run(boot);
  window.addEventListener("hart:lang", () => {
    mountHeader();
    mountFooter();
  });
})();

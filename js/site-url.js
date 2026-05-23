/** Публичный адрес сайта из config.js */
(function (global) {
  const D = "di" + "v";

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

  function shareText() {
    const brand = global.SITE_CONFIG?.brand || "Клуб знаний";
    const accent = global.SITE_CONFIG?.accent || "HART";
    const tag = global.SITE_CONFIG?.tagline || "";
    return `${brand} ${accent}${tag ? " — " + tag : ""}: 231+ программ`;
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
    const encUrl = encodeURIComponent(base() + "/");
    const encText = encodeURIComponent(shareText());
    const label = pretty();
    const href = base() + "/";
    const t = (k, fb) => global.HartI18n?.t?.(k) || fb;

    const wrap = document.createElement(D);
    wrap.className = "site-share";

    const lbl = document.createElement("span");
    lbl.className = "site-share-label";
    lbl.textContent = t("share.label", "Сайт клуба");

    const a = document.createElement("a");
    a.className = "site-share-url";
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = label;

    const social = document.createElement(D);
    social.className = "site-share-social";
    [
      ["Telegram", `https://t.me/share/url?url=${encUrl}&text=${encText}`, "share.telegram"],
      ["ВКонтакте", `https://vk.com/share.php?url=${encUrl}`, "share.vk"],
      ["WhatsApp", `https://wa.me/?text=${encText}%20${encUrl}`, "share.whatsapp"],
    ].forEach(([fb, link, key]) => {
      const s = document.createElement("a");
      s.className = "site-share-btn";
      s.href = link;
      s.target = "_blank";
      s.rel = "noopener noreferrer";
      s.textContent = t(key, fb);
      social.appendChild(s);
    });

    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "btn btn-outline btn-sm site-share-copy";
    copy.dataset.url = href;
    copy.textContent = t("share.copy", "Копировать");
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(href);
        copy.textContent = t("share.copied", "Скопировано");
        setTimeout(() => {
          copy.textContent = t("share.copy", "Копировать");
        }, 2000);
      } catch {
        prompt(t("share.prompt", "Ссылка:"), href);
      }
    });

    wrap.append(lbl, a, social, copy);
    el.replaceChildren(wrap);
  }

  global.HartSiteUrl = { base, pretty, path, setCanonical, mountShare, shareText };
})(window);

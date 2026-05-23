/** SEO: meta-теги, hreflang ru/en, обновление при смене языка. */
(function (global) {
  const HREFLANGS = ["ru", "en"];

  function baseUrl() {
    if (global.HartSiteUrl?.base) return global.HartSiteUrl.base().replace(/\/$/, "");
    const o = global.location?.origin || "";
    return o && !o.startsWith("file:") ? o : "https://hart-club.ru";
  }

  function pagePath(pageId, courseId) {
    if (pageId === "index") return "/";
    if (pageId === "course" && courseId) {
      return `/course.html?id=${encodeURIComponent(courseId)}`;
    }
    const map = { support: "/support.html", pay: "/pay.html" };
    return map[pageId] || "/";
  }

  function urlForLang(pageId, lang, courseId) {
    const path = pagePath(pageId, courseId);
    const u = new URL(path === "/" ? "" : path.replace(/^\//, ""), baseUrl() + "/");
    if (lang === "en") u.searchParams.set("lang", "en");
    if (pageId === "index" && lang === "ru") return baseUrl() + "/";
    return u.href;
  }

  function fixIndexUrl(href, pageId) {
    if (pageId !== "index") return href;
    const u = new URL(href);
    if (u.pathname.endsWith("index.html")) u.pathname = "/";
    return u.href;
  }

  function setMeta(attr, key, value) {
    let el = document.querySelector(`meta[${attr}="${key}"]`);
    if (!el) {
      el = document.createElement("meta");
      el.setAttribute(attr, key);
      document.head.appendChild(el);
    }
    el.setAttribute("content", value);
  }

  function setLink(rel, hreflang, href) {
    const sel = `link[rel="${rel}"][hreflang="${hreflang}"]`;
    let el = document.querySelector(sel);
    if (!el) {
      el = document.createElement("link");
      el.rel = rel;
      el.hreflang = hreflang;
      document.head.appendChild(el);
    }
    el.href = href;
  }

  function t(key, vars) {
    return global.HartI18n?.t?.(key, vars) || key;
  }

  function applyHreflang(pageId, courseId) {
    HREFLANGS.forEach((hl) => {
      let href = urlForLang(pageId, hl, courseId);
      href = fixIndexUrl(href, pageId);
      setLink("alternate", hl, href);
    });
    const def = fixIndexUrl(urlForLang(pageId, "ru", courseId), pageId);
    setLink("alternate", "x-default", def);
  }

  function applyMeta(title, description, pageUrl) {
    document.title = title;
    document.documentElement.lang = global.HartI18n?.getLang?.() === "ru" ? "ru" : "en";
    setMeta("name", "description", description);
    setMeta("property", "og:title", title);
    setMeta("property", "og:description", description);
    setMeta("property", "og:url", pageUrl);
    setMeta("property", "og:locale", document.documentElement.lang === "ru" ? "ru_RU" : "en_US");
    setMeta("name", "twitter:title", title);
    setMeta("name", "twitter:description", description);
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = pageUrl;
  }

  function applyPage(pageId) {
    const lang = global.HartI18n?.getLang?.() || "ru";
    const courseId = null;
    const pageUrl = fixIndexUrl(urlForLang(pageId, lang, courseId), pageId);
    const title = t(`seo.${pageId}.title`);
    const description = t(`seo.${pageId}.description`);
    applyMeta(title, description, pageUrl);
    applyHreflang(pageId, courseId);
  }

  function applyCourse(course) {
    if (!course) return;
    const lang = global.HartI18n?.getLang?.() || "ru";
    const pageId = "course";
    const courseId = course.id || "";
    const pageUrl = urlForLang(pageId, lang, courseId);
    const title = t("seo.course.title", { title: course.title });
    const descRaw = (course.desc || "").slice(0, 120);
    const description =
      lang === "en"
        ? t("seo.course.description_en", { title: course.title, desc: descRaw })
        : t("seo.course.description", { title: course.title, desc: descRaw });
    applyMeta(title, description, pageUrl);
    applyHreflang(pageId, courseId);
  }

  function bindLangRefresh(pageId) {
    global.addEventListener("hart:lang", () => {
      if (pageId === "course" && global.__hartSeoCourse) {
        applyCourse(global.__hartSeoCourse);
      } else {
        applyPage(pageId);
      }
    });
  }

  function init(pageId) {
    const run = () => {
      if (pageId === "course") {
        applyMeta(
          t("seo.course.pending_title"),
          t("seo.course.pending_description"),
          fixIndexUrl(urlForLang("course", global.HartI18n?.getLang?.() || "ru", new URLSearchParams(global.location.search).get("id") || ""), "course"),
        );
        applyHreflang("course", new URLSearchParams(global.location.search).get("id") || "");
      } else {
        applyPage(pageId);
      }
      bindLangRefresh(pageId);
    };
    if (global.HartI18n?.ready) run();
    else global.HartI18n?.init?.().then(run).catch(run);
  }

  global.HartSeo = {
    init,
    applyPage,
    applyCourse,
    setCourse(course) {
      global.__hartSeoCourse = course;
      applyCourse(course);
    },
  };
})(window);

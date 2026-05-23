/** Мультиязычность: выбор языка и автоопределение по стране/браузеру. */
(function (global) {
  const STORAGE_LANG = "hart_lang";
  const STORAGE_REGION = "hart_region";
  let catalog = null;
  let lang = "ru";
  let ready = false;

  const COUNTRY_LANG = {
    RU: "ru", BY: "ru", KZ: "ru", UA: "uk", US: "en", GB: "en", CA: "en",
    AU: "en", DE: "de", AT: "de", CH: "de", FR: "fr", ES: "es", MX: "es",
    AR: "es", PT: "pt", BR: "pt", IT: "it", PL: "pl", TR: "tr", CN: "zh",
    TW: "zh", JP: "ja", KR: "ko", SA: "ar", AE: "ar", IN: "hi", NL: "nl",
    CZ: "cs", RO: "ro", HU: "hu", SE: "sv", DK: "da", FI: "fi", GR: "el",
    IL: "he", TH: "th", VN: "vi", ID: "id", MY: "ms", IR: "fa", BD: "bn",
    RS: "sr", HR: "hr", SK: "sk", BG: "bg", LT: "lt", LV: "lv", EE: "et",
    GE: "ka", AM: "hy", AZ: "az", UZ: "uz",
  };

  const CIS = new Set(["RU", "BY", "KZ", "AM", "AZ", "KG", "MD", "TJ", "TM", "UZ"]);

  function browserLang() {
    const raw = (navigator.language || "ru").toLowerCase();
    const code = raw.split("-")[0];
    if (catalog && catalog[code]) return code;
    if (raw.startsWith("zh")) return catalog?.zh ? "zh" : "ru";
    if (catalog?.[code]) return code;
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    if (/Moscow|Europe\/(Minsk|Samara)|Asia\/(Almaty|Yekaterinburg)/.test(tz)) return "ru";
    return catalog?.en ? "en" : "ru";
  }

  async function detectCountry() {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 3500);
      const r = await fetch("https://ipapi.co/country_code/", { signal: ctrl.signal });
      clearTimeout(t);
      if (!r.ok) return null;
      return (await r.text()).trim().toUpperCase();
    } catch {
      return null;
    }
  }

  function regionFromCountry(cc) {
    if (!cc) {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
      if (/Moscow|Europe\/(Minsk|Samara|Volgograd)|Asia\/(Almaty|Yekaterinburg)/.test(tz)) {
        return "ru";
      }
      return "intl";
    }
    return CIS.has(cc) ? "ru" : "intl";
  }

  function langFromCountry(cc) {
    if (!cc) return browserLang();
    return COUNTRY_LANG[cc] || browserLang();
  }

  function t(key, vars) {
    const pack = catalog?.[lang] || {};
    let s = pack[key];
    if (!s && getRegion() === "ru" && catalog?.ru) {
      s = catalog.ru[key];
    }
    if (!s) s = catalog?.en?.[key] || key;
    if (vars) {
      Object.keys(vars).forEach((k) => {
        s = s.replace(new RegExp(`\\{${k}\\}`, "g"), vars[k]);
      });
    }
    return s;
  }

  function applyDom(root) {
    const scope = root || document;
    document.documentElement.lang = lang;
    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const val = t(key);
      if (el.tagName === "INPUT" && el.hasAttribute("placeholder")) {
        el.placeholder = val;
      } else {
        el.textContent = val;
      }
    });
    scope.querySelectorAll("[data-i18n-html]").forEach((el) => {
      el.innerHTML = t(el.getAttribute("data-i18n-html"));
    });
  }

  function apply(opts) {
    const silent = opts && opts.silent;
    applyDom(opts && opts.root);
    if (!silent) {
      global.dispatchEvent(new CustomEvent("hart:lang", { detail: { lang } }));
    }
  }

  function setLang(code) {
    if (!catalog?.[code]) code = "en";
    lang = code;
    localStorage.setItem(STORAGE_LANG, code);
    apply();
  }

  function getLang() {
    return lang;
  }

  function getRegion() {
    return localStorage.getItem(STORAGE_REGION) || "ru";
  }

  function setRegion(r) {
    const region = r === "ru" ? "ru" : "intl";
    localStorage.setItem(STORAGE_REGION, region);
    if (region === "ru" && catalog?.ru && lang !== "ru") {
      lang = "ru";
      localStorage.setItem(STORAGE_LANG, "ru");
      applyDom();
      global.dispatchEvent(new CustomEvent("hart:lang", { detail: { lang } }));
    }
    global.dispatchEvent(new CustomEvent("hart:region", { detail: { region: getRegion() } }));
  }

  function languages() {
    return catalog?._meta?.languages || [["en", "English"]];
  }

  async function init() {
    if (ready) return { lang, region: getRegion() };
    const res = await fetch("data/i18n.json");
    if (!res.ok) throw new Error("i18n.json");
    catalog = await res.json();
    const saved = localStorage.getItem(STORAGE_LANG);
    lang = saved && catalog[saved] ? saved : browserLang();
    if (!saved) localStorage.setItem(STORAGE_LANG, lang);
    ready = true;
    apply();
    detectCountry()
      .then((cc) => {
        if (!localStorage.getItem(STORAGE_REGION)) {
          setRegion(regionFromCountry(cc));
        }
        if (!saved && cc) {
          const auto = langFromCountry(cc);
          if (catalog[auto]) setLang(auto);
        }
      })
      .catch(() => {});
    return { lang, region: getRegion() };
  }

  global.HartI18n = {
    init,
    t,
    setLang,
    getLang,
    getRegion,
    setRegion,
    languages,
    apply,
    applyDom,
    get ready() {
      return ready;
    },
  };
})(window);

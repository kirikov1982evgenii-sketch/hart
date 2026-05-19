/** Защита от open redirect и опасных ссылок в URL. */
(function (global) {
  function isSafeHttpUrl(url) {
    if (!url || typeof url !== "string") return false;
    try {
      const u = new URL(url.trim());
      if (u.protocol !== "http:" && u.protocol !== "https:") return false;
      if (!u.hostname || u.username || u.password) return false;
      const low = url.toLowerCase();
      if (
        low.includes("javascript:") ||
        low.includes("data:") ||
        low.includes("vbscript:")
      ) {
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  function safeCourseUrlFromParams(params) {
    const raw = params.get("url") || "";
    return isSafeHttpUrl(raw) ? raw.trim() : "";
  }

  global.MarketSecurity = { isSafeHttpUrl, safeCourseUrlFromParams };
})(typeof window !== "undefined" ? window : globalThis);

/** Токен администратора после входа по логину/паролю. */
(function (global) {
  const KEY_TOKEN = "hart_admin_token";
  const KEY_EXPIRES = "hart_admin_token_exp";

  const api = () =>
    (global.SITE_CONFIG?.paymentApiUrl || "http://127.0.0.1:8766").replace(/\/$/, "");

  function getToken() {
    const exp = parseInt(sessionStorage.getItem(KEY_EXPIRES) || "0", 10);
    if (exp && Date.now() > exp) {
      clearToken();
      return "";
    }
    return sessionStorage.getItem(KEY_TOKEN) || "";
  }

  function saveToken(token, ttlSec) {
    sessionStorage.setItem(KEY_TOKEN, token);
    sessionStorage.setItem(KEY_EXPIRES, String(Date.now() + (ttlSec || 28800) * 1000));
  }

  function clearToken() {
    sessionStorage.removeItem(KEY_TOKEN);
    sessionStorage.removeItem(KEY_EXPIRES);
  }

  function isAuthenticated() {
    return getToken().length > 20;
  }

  function authHeaders(extra) {
    const h = { ...(extra || {}) };
    const t = getToken();
    if (t) h["X-Admin-Token"] = t;
    return h;
  }

  async function login(login, password) {
    const r = await fetch(api() + "/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login: login.trim(), password }),
    });
    const data = await r.json();
    if (!data.ok) throw new Error(data.error || "Ошибка входа");
    saveToken(data.token, 28800);
    if (global.HartSession) {
      global.HartSession.saveSession(
        data.email,
        data.code,
        data.name || "Администратор",
        true
      );
    }
    return data;
  }

  function logout() {
    clearToken();
    if (global.HartSession) global.HartSession.clearSession();
  }

  global.HartAdminAuth = {
    api,
    getToken,
    saveToken,
    clearToken,
    isAuthenticated,
    authHeaders,
    login,
    logout,
  };
})(window);

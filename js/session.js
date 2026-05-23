/** Сессия пользователя: email + код доступа в sessionStorage. */
(function (global) {
  const KEY_EMAIL = "hart_user_email";
  const KEY_CODE = "hart_user_code";
  const KEY_NAME = "hart_user_name";

  const api = () =>
    (global.SITE_CONFIG?.paymentApiUrl || "http://127.0.0.1:8766").replace(/\/$/, "");

  function getEmail() {
    return (sessionStorage.getItem(KEY_EMAIL) || "").trim().toLowerCase();
  }

  function getCode() {
    return (sessionStorage.getItem(KEY_CODE) || "").trim().toUpperCase();
  }

  function getName() {
    return sessionStorage.getItem(KEY_NAME) || "";
  }

  function isLoggedIn() {
    return getEmail().includes("@") && getCode().startsWith("PAY-");
  }

  function isAdmin() {
    return sessionStorage.getItem("hart_user_admin") === "1";
  }

  function saveSession(email, code, name) {
    sessionStorage.setItem(KEY_EMAIL, email);
    sessionStorage.setItem(KEY_CODE, code);
    if (name) sessionStorage.setItem(KEY_NAME, name);
    sessionStorage.setItem("market_pay_email", email);
  }

  function clearSession() {
    [KEY_EMAIL, KEY_CODE, KEY_NAME, "market_pay_email"].forEach((k) =>
      sessionStorage.removeItem(k)
    );
  }

  async function login(email, name) {
    const em = email.trim().toLowerCase();
    const r = await fetch(api() + "/api/user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: em, name: (name || "").trim() }),
    });
    const data = await r.json();
    if (!data.ok) throw new Error(data.error || "Ошибка входа");
    saveSession(em, data.code, data.user?.name || name || "");
    return data;
  }

  async function fetchLibrary() {
    const email = getEmail();
    const code = getCode();
    if (!isLoggedIn()) return null;
    const r = await fetch(
      api() +
        "/api/library?email=" +
        encodeURIComponent(email) +
        "&code=" +
        encodeURIComponent(code)
    );
    return r.json();
  }

  function isLocalDev() {
    const h = global.location?.hostname || "";
    return h === "127.0.0.1" || h === "localhost" || global.SITE_CONFIG?.devMode === true;
  }

  /** Локально: вход через /api/dev/session (настоящий код PAY-…). */
  async function ensureDevLogin() {
    if (!isLocalDev()) return false;
    if (isLoggedIn()) return true;
    try {
      const r = await fetch(api() + "/api/dev/session");
      const data = await r.json();
      if (!data.ok) return false;
      saveSession(data.email, data.code, data.name || "Администратор");
      if (data.is_admin) sessionStorage.setItem("hart_user_admin", "1");
      return true;
    } catch {
      return false;
    }
  }

  async function hasCourseAccess(courseId) {
    const email = getEmail();
    const code = getCode();
    if (!isLoggedIn() || !courseId) return false;
    const r = await fetch(
      api() +
        "/api/access?email=" +
        encodeURIComponent(email) +
        "&code=" +
        encodeURIComponent(code) +
        "&course_id=" +
        encodeURIComponent(courseId)
    );
    const data = await r.json();
    return !!data.approved;
  }

  global.HartSession = {
    getEmail,
    getCode,
    getName,
    isLoggedIn,
    isAdmin,
    isLocalDev,
    saveSession,
    clearSession,
    login,
    ensureDevLogin,
    fetchLibrary,
    hasCourseAccess,
    api,
  };
})(window);

/** Оплата: RU 199 ₽ / INT $4.99 */
(function () {
  const params = new URLSearchParams(location.search);
  const courseId = (params.get("id") || "").slice(0, 80);
  let courseUrl =
    (window.MarketSecurity && window.MarketSecurity.safeCourseUrlFromParams(params)) || "";
  let courseTitle = (params.get("title") || "Курс").slice(0, 200);
  const cfg = window.SITE_CONFIG || {};
  const api = (cfg.paymentApiUrl || "http://127.0.0.1:8766").replace(/\/$/, "");

  function t(k, v) {
    return window.HartI18n?.t?.(k, v) || k;
  }
  function pr() {
    return window.HartRegion?.pricing?.() || { region: "ru", amount: 199, currency: "RUB" };
  }

  function ensureRuForPayment() {
    if (window.HartI18n?.getRegion?.() === "ru" && window.HartI18n?.getLang?.() !== "ru") {
      window.HartI18n.setLang("ru");
    }
  }

  let userEmail = sessionStorage.getItem("hart_user_email") || sessionStorage.getItem("market_pay_email") || "";
  let payCode = window.HartSession?.getCode?.() || "";
  let pollTimer = null;

  async function apiGet(path) {
    return (await fetch(api + path)).json();
  }

  async function apiPost(path, body) {
    return (
      await fetch(api + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
    ).json();
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  async function loadCourseMeta() {
    if (!courseId) return;
    try {
      const data = await (await fetch("data/resources.json")).json();
      const c = data.resources.find((r) => r.id === courseId);
      if (c) {
        courseTitle = c.title;
        if (window.MarketSecurity?.isSafeHttpUrl?.(c.url)) courseUrl = c.url;
      }
    } catch {
      /* ignore */
    }
  }

  function renderPreview() {
    const link = courseId ? `course.html?id=${encodeURIComponent(courseId)}` : "index.html";
    document.getElementById("course-preview").innerHTML = `
      <div class="pay-box" style="margin:1rem 0">
        <h3 style="font-family:var(--font-display)">${escapeHtml(courseTitle)}</h3>
        <p class="pay-hint"><a href="${link}">← ${t("card.more")}</a></p>
      </div>`;
  }

  async function checkCourseAccess() {
    if (!userEmail || !payCode || !courseId) return false;
    const res = await apiGet(
      "/api/access?email=" +
        encodeURIComponent(userEmail) +
        "&code=" +
        encodeURIComponent(payCode) +
        "&course_id=" +
        encodeURIComponent(courseId)
    );
    return !!res.approved;
  }

  function stepEmail() {
    document.getElementById("pay-root").innerHTML = `
      <div class="pay-box">
        <h2 style="color:var(--gold);font-family:var(--font-display)">${t("pay.step1")}</h2>
        <p>${t("pay.step1hint")}</p>
        <label>${t("cabinet.email")}</label>
        <input type="email" id="pay-email" class="input" value="${escapeHtml(userEmail)}">
        <button type="button" class="btn btn-gold" id="btn-email-next">${t("nav.login")} →</button>
        <p id="email-msg" class="form-msg"></p>
      </div>`;
    document.getElementById("btn-email-next").onclick = async () => {
      const em = document.getElementById("pay-email").value.trim().toLowerCase();
      const msg = document.getElementById("email-msg");
      if (!em.includes("@")) {
        msg.textContent = t("pay.err_email");
        msg.className = "form-msg err";
        return;
      }
      try {
        const data = await window.HartSession.login(em, "");
        userEmail = em;
        payCode = data.code;
        if (courseId && (await checkCourseAccess())) {
          showApproved();
          return;
        }
        stepPay();
      } catch (e) {
        msg.textContent = e.message;
        msg.className = "form-msg err";
      }
    };
  }

  function formatCard(num) {
    const d = String(num || cfg.payCard || "").replace(/\D/g, "");
    return d.replace(/(\d{4})(?=\d)/g, "$1 ").trim() || d;
  }

  function payDetailsHtml() {
    const p = pr();
    if (p.region === "ru") {
      const card = formatCard(cfg.payCard);
      return `<p><b>${t("pay.bank")}:</b> ${cfg.payBank || "Т-Банк"}</p>
        <p><b>${t("pay.card")}:</b> <code>${card}</code></p>
        ${cfg.payName ? `<p><b>${t("pay.recipient")}:</b> ${cfg.payName}</p>` : ""}
        <p class="pay-hint">${t("pay.card_hint", { amount: p.amount, code: payCode })}</p>`;
    }
    return `<p><b>${t("pay.paypal")}:</b> <code>${cfg.payPalEmail || "freelancerwok@mail.ru"}</code></p>
      <p class="pay-hint">${t("pay.usd_hint", { amount: p.amount, code: payCode })}</p>`;
  }

  function stepPay() {
    ensureRuForPayment();
    const p = pr();
    const priceStr = p.region === "ru" ? `${p.amount} ₽` : `$${p.amount}`;
    const bot = (cfg.telegramBotName || "uportbot").replace("@", "");
    document.getElementById("pay-root").innerHTML = `
      <div class="pay-box">
        <h2 style="color:var(--gold)">${t("pay.step2")} <span class="price-big">${priceStr}</span></h2>
        <p>${t("pay.email_line", { email: escapeHtml(userEmail), code: payCode })}</p>
        <div class="pay-details">${payDetailsHtml()}</div>
        <h3>${t("pay.step3")}</h3>
        <input type="file" id="receipt-file" class="input" accept="image/*,.pdf">
        <button type="button" class="btn btn-gold" id="btn-submit-claim">${t("pay.submit")}</button>
        <p id="claim-msg" class="form-msg"></p>
        <p class="pay-hint" style="margin-top:1rem">${t("pay.telegram", { bot })} — <a href="https://t.me/${bot}" target="_blank" rel="noopener">t.me/${bot}</a></p>
      </div>`;
    document.getElementById("btn-submit-claim").onclick = submitClaim;
  }

  async function submitClaim() {
    const msg = document.getElementById("claim-msg");
    const file = document.getElementById("receipt-file").files[0];
    if (!file) {
      msg.textContent = t("pay.err_receipt");
      msg.className = "form-msg err";
      return;
    }
    const b64 = await new Promise((res, rej) => {
      const r = new FileReader();
      r.onload = () => res(r.result);
      r.onerror = rej;
      r.readAsDataURL(file);
    });
    const res = await apiPost("/api/claim", {
      email: userEmail,
      code: payCode,
      region: pr().region,
      course_id: courseId,
      course_url: courseUrl,
      course_title: courseTitle,
      receipt_b64: b64,
    });
    if (!res.ok) {
      msg.textContent = res.error || t("pay.err_generic");
      msg.className = "form-msg err";
      return;
    }
    stepPending();
  }

  function stepPending() {
    document.getElementById("pay-root").innerHTML = `
      <div class="pay-box">
        <h2>${t("pay.pending")}</h2>
        <p>${t("pay.pendinghint")}</p>
        <button class="btn btn-gold" id="btn-check-status">${t("pay.check")}</button>
        <p id="status-msg" class="form-msg"></p>
      </div>`;
    document.getElementById("btn-check-status").onclick = checkAccess;
    pollTimer = setInterval(checkAccess, 15000);
    checkAccess();
  }

  async function checkAccess() {
    const msg = document.getElementById("status-msg");
    if (!msg) return;
    if (await checkCourseAccess()) {
      if (pollTimer) clearInterval(pollTimer);
      showApproved();
    } else {
      msg.textContent = t("pay.pending");
      msg.className = "form-msg err";
    }
  }

  function showApproved() {
    document.getElementById("pay-root").classList.add("hidden");
    document.getElementById("after-paid").classList.remove("hidden");
    document.getElementById("open-course-msg").textContent = t("pay.access_msg");
    document.getElementById("pay-approved-title").textContent = t("pay.access_title");
    document.getElementById("btn-open-course").textContent = t("pay.cabinet") + " →";
    document.getElementById("btn-open-course").href = "cabinet.html";
  }

  function refreshPayUi() {
    const after = document.getElementById("after-paid");
    if (after && !after.classList.contains("hidden")) {
      showApproved();
      return;
    }
    const root = document.getElementById("pay-root");
    if (!root || root.classList.contains("hidden")) return;
    if (document.getElementById("btn-submit-claim")) stepPay();
    else if (document.getElementById("btn-email-next")) stepEmail();
    else if (document.getElementById("btn-check-status")) stepPending();
  }

  async function apiOnline() {
    try {
      const r = await fetch(api + "/api/health", { method: "GET", signal: AbortSignal.timeout(8000) });
      const j = await r.json();
      return !!j.ok;
    } catch {
      return false;
    }
  }

  function stepTelegramOnly() {
    const bot = (cfg.telegramBotName || "uportbot").replace("@", "");
    const p = pr();
    const priceStr = p.region === "ru" ? `${p.amount} ₽` : `$${p.amount}`;
    document.getElementById("pay-root").innerHTML = `
      <div class="pay-box" style="border-color:var(--gold)">
        <h2 style="color:var(--gold);font-family:var(--font-display)">Оплата через Telegram</h2>
        <p>Сервер оплаты временно недоступен. Оплатите в боте — без карты для хостинга.</p>
        <p><b>Цена:</b> ${priceStr}</p>
        <div class="pay-details">${payDetailsHtml()}</div>
        <p class="pay-hint">В боте: /pay → email → перевод → фото чека</p>
        <a class="btn btn-gold btn-link" href="https://t.me/${bot}?start=pay" target="_blank" rel="noopener">Открыть @${bot}</a>
      </div>`;
  }

  async function init() {
    if (window.HartI18n && !window.HartI18n.ready) await window.HartI18n.init();
    ensureRuForPayment();
    const bc = document.querySelector(".breadcrumb");
    if (bc) {
      bc.innerHTML = `<a href="index.html">${t("nav.catalog")}</a> / ${t("pay.breadcrumb")}`;
    }
    await loadCourseMeta();
    renderPreview();
    if (!(await apiOnline())) {
      stepTelegramOnly();
      return;
    }
    if (window.HartSession?.isLoggedIn?.()) {
      userEmail = window.HartSession.getEmail();
      payCode = window.HartSession.getCode();
      if (courseId && (await checkCourseAccess())) {
        showApproved();
        return;
      }
      if (payCode) {
        stepPay();
        return;
      }
    }
    stepEmail();
  }

  window.addEventListener("hart:region", () => {
    ensureRuForPayment();
    refreshPayUi();
  });
  window.addEventListener("hart:lang", refreshPayUi);

  document.addEventListener("DOMContentLoaded", init);
})();

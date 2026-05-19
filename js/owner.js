(function () {
  const cfg = () => window.SITE_CONFIG || {};
  const api = () => (cfg().paymentApiUrl || "http://127.0.0.1:8766").replace(/\/$/, "");
  const OWNER = (cfg().ownerEmail || "freelancerwok@mail.ru").toLowerCase();

  function t(k) {
    return window.HartI18n?.t?.(k) || k;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function renderLogin() {
    document.getElementById("owner-root").innerHTML = `
      <div class="auth-card" style="max-width:420px;margin:0 auto">
        <h2 style="color:var(--gold);font-family:var(--font-display)">${t("owner.login")}</h2>
        <p class="pay-hint">${escapeHtml(OWNER)}</p>
        <label>PIN (.env.local → MARKET_OWNER_PIN)</label>
        <input type="password" id="owner-pin" class="input">
        <button class="btn btn-gold" id="btn-owner-in">${t("nav.login")}</button>
        <p id="owner-msg" class="form-msg"></p>
      </div>`;
    document.getElementById("btn-owner-in").onclick = () => {
      sessionStorage.setItem("hart_owner_pin", document.getElementById("owner-pin").value);
      loadDashboard();
    };
  }

  async function loadDashboard() {
    const root = document.getElementById("owner-root");
    const pin = sessionStorage.getItem("hart_owner_pin") || "";
    root.innerHTML = '<p class="empty">…</p>';
    try {
      const r = await fetch(
        api() + "/api/owner/dashboard?email=" + encodeURIComponent(OWNER),
        { headers: { "X-Owner-Pin": pin } }
      );
      const data = await r.json();
      if (!data.ok) {
        renderLogin();
        return;
      }
      const pending = data.pending || [];
      const rows = pending.length
        ? pending
            .map(
              (c) => `
          <div class="library-item">
            <div>
              <h3>${escapeHtml(c.course_title || "Course")}</h3>
              <p class="pay-hint">${escapeHtml(c.email)} · ${c.amount} ${c.currency} · <code>${escapeHtml(c.code)}</code></p>
            </div>
            <div>
              <button class="btn btn-gold btn-sm approve" data-id="${c.id}">${t("owner.approve")}</button>
              <button class="btn-ghost btn-sm reject" data-id="${c.id}">${t("owner.reject")}</button>
            </div>
          </div>`
            )
            .join("")
        : '<p class="library-empty">—</p>';
      root.innerHTML = `
        <div class="stats">
          <div class="stat"><b>${data.users_count || 0}</b><span>${t("owner.users")}</span></div>
          <div class="stat"><b>${pending.length}</b><span>${t("owner.pending")}</span></div>
          <div class="stat"><b>${data.approved_count || 0}</b><span>paid</span></div>
        </div>
        <p class="pay-hint" style="margin:1rem 0">
          <a href="mailto:${cfg().supportEmail}">${cfg().supportEmail}</a> ·
          <a href="${cfg().telegramBot}" target="_blank">Telegram</a>
        </p>
        <div class="cabinet-panel"><h2>${t("owner.pending")}</h2>${rows}</div>`;
      root.querySelectorAll(".approve").forEach((b) => {
        b.onclick = () => act(b.dataset.id, "approve", pin);
      });
      root.querySelectorAll(".reject").forEach((b) => {
        b.onclick = () => act(b.dataset.id, "reject", pin);
      });
    } catch (e) {
      root.innerHTML = `<p class="form-msg err">${escapeHtml(e.message)}</p>`;
    }
  }

  async function act(id, kind, pin) {
    await fetch(api() + (kind === "approve" ? "/api/approve" : "/api/reject"), {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Pin": pin },
      body: JSON.stringify({ claim_id: id }),
    });
    loadDashboard();
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await HartI18n.init();
    sessionStorage.getItem("hart_owner_pin") ? loadDashboard() : renderLogin();
  });
})();

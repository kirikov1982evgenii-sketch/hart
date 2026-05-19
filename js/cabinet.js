(function () {
  const price = () => window.HartRegion?.formatPrice?.() || "199 ₽";
  function t(k) {
    return window.HartI18n?.t?.(k) || k;
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function renderLogin() {
    const root = document.getElementById("cabinet-root");
    root.innerHTML = `
      <div class="cabinet-grid">
        <div class="auth-card">
          <h2 style="font-family:var(--font-display);color:var(--gold);margin-bottom:0.5rem">Вход</h2>
          <p class="pay-hint">Укажите email — он нужен для оплаты и хранения ваших курсов.</p>
          <label>Имя (необязательно)</label>
          <input type="text" id="cab-name" class="input" placeholder="Как к вам обращаться">
          <label>Email</label>
          <input type="email" id="cab-email" class="input" placeholder="you@mail.ru" required>
          <button type="button" class="btn btn-gold" id="btn-cab-login">Войти в кабинет</button>
          <p id="cab-msg" class="form-msg"></p>
        </div>
        <div class="cabinet-panel">
          <h2>Как это работает</h2>
          <ul class="learn-list">
            <li>Выберите курс в каталоге и изучите программу на сайте</li>
            <li>${t("cabinet.how2").replace("199", price())}</li>
            <li>После подтверждения курс появится здесь со ссылкой</li>
          </ul>
        </div>
      </div>`;
    document.getElementById("btn-cab-login").onclick = async () => {
      const msg = document.getElementById("cab-msg");
      const email = document.getElementById("cab-email").value.trim();
      const name = document.getElementById("cab-name").value.trim();
      if (!email.includes("@")) {
        msg.textContent = "Введите корректный email";
        msg.className = "form-msg err";
        return;
      }
      try {
        await window.HartSession.login(email, name);
        renderCabinet();
      } catch (e) {
        msg.textContent = e.message + ". Запустите start-site.bat.";
        msg.className = "form-msg err";
      }
    };
  }

  async function renderCabinet() {
    const root = document.getElementById("cabinet-root");
    const email = window.HartSession.getEmail();
    const name = window.HartSession.getName();
    root.innerHTML = '<p class="empty">Загрузка курсов…</p>';
    let lib;
    try {
      lib = await window.HartSession.fetchLibrary();
    } catch {
      lib = { ok: false };
    }
    if (!lib?.ok) {
      root.innerHTML = `<p class="form-msg err">Не удалось загрузить кабинет. Проверьте сервер оплат.</p>`;
      return;
    }
    const courses = lib.courses || [];
    const listHtml = courses.length
      ? courses
          .map(
            (c) => `
        <div class="library-item">
          <div>
            <h3>${escapeHtml(c.title || "Курс")}</h3>
            <p class="pay-hint">Оплачен · ${escapeHtml((c.approved_at || "").slice(0, 10))}</p>
          </div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
            ${c.course_id ? `<a class="btn btn-outline" href="course.html?id=${encodeURIComponent(c.course_id)}">Описание</a>` : ""}
            ${c.url ? `<a class="btn btn-gold" href="${escapeHtml(c.url)}" target="_blank" rel="noopener">Перейти к обучению →</a>` : ""}
          </div>
        </div>`
          )
          .join("")
      : `<p class="library-empty">Пока нет оплаченных курсов.<br><a href="index.html" class="gold">Выбрать программу в каталоге →</a></p>`;

    root.innerHTML = `
      <div class="cabinet-grid">
        <div class="auth-card">
          <h2 style="font-family:var(--font-display);color:var(--gold)">Профиль</h2>
          <p><b>${escapeHtml(name || "Участник")}</b></p>
          <p class="pay-hint">${escapeHtml(email)}</p>
          <p class="pay-hint">Код оплаты: <code>${escapeHtml(window.HartSession.getCode())}</code></p>
          <button type="button" class="btn-ghost" id="btn-cab-out" style="margin-top:1rem">Выйти</button>
        </div>
        <div class="cabinet-panel">
          <h2>Мои курсы (${courses.length})</h2>
          ${listHtml}
        </div>
      </div>`;
    document.getElementById("btn-cab-out").onclick = () => {
      window.HartSession.clearSession();
      location.reload();
    };
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await HartI18n.init();
    if (window.HartSession?.isLoggedIn?.()) renderCabinet();
    else renderLogin();
  });
})();

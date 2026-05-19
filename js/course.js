(function () {
  const params = new URLSearchParams(location.search);
  const courseId = params.get("id") || "";
  const price = window.SITE_CONFIG?.accessPrice || 199;

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  async function load() {
    const root = document.getElementById("course-root");
    const res = await fetch("data/resources.json");
    const data = await res.json();
    const course = data.resources.find((r) => r.id === courseId);
    if (!course) {
      root.innerHTML = '<p class="empty">Курс не найден. <a href="index.html">В каталог</a></p>';
      return;
    }
    document.title = course.title + " — Клуб знаний HART";
    const bc = document.getElementById("bc-title");
    if (bc) bc.textContent = course.title;

    let hasAccess = false;
    if (window.HartSession?.isLoggedIn?.()) {
      hasAccess = await window.HartSession.hasCourseAccess(courseId);
    }

    const modules = (course.modules || [])
      .map((m) => `<li>${escapeHtml(m)}</li>`)
      .join("");
    const learn = (course.learn || [])
      .map((l) => `<li>${escapeHtml(l)}</li>`)
      .join("");

    root.innerHTML = `
      <article class="course-hero">
        <span class="label-price">${price} ₽ · полный доступ</span>
        <h1>${escapeHtml(course.title)}</h1>
        <div class="course-meta-grid">
          <div class="meta-item"><b>Уровень</b><span>${escapeHtml(course.level || "—")}</span></div>
          <div class="meta-item"><b>Длительность</b><span>${escapeHtml(course.duration || "—")}</span></div>
          <div class="meta-item"><b>Формат</b><span>${escapeHtml(course.format || "—")}</span></div>
          <div class="meta-item"><b>Платформа</b><span>${escapeHtml(course.provider || "—")}</span></div>
        </div>
        <div class="tags" style="margin-top:1rem">${(course.tags || [])
          .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
          .join("")}</div>
      </article>

      <section class="course-section">
        <h2>О программе</h2>
        <p>${escapeHtml(course.about || course.desc || "")}</p>
      </section>

      <section class="course-section">
        <h2>Чему вы научитесь</h2>
        <ul class="learn-list">${learn}</ul>
      </section>

      <section class="course-section">
        <h2>Структура курса</h2>
        <ol class="module-list">${modules}</ol>
      </section>

      <section class="course-cta">
        ${
          hasAccess
            ? `<p class="pay-hint ok">У вас есть доступ к этому курсу</p>
               <a class="btn btn-gold" href="${escapeHtml(course.url)}" target="_blank" rel="noopener noreferrer">Открыть на ${escapeHtml(course.provider || "платформе")} →</a>
               <p class="pay-hint" style="margin-top:1rem"><a href="cabinet.html">Все курсы в кабинете</a></p>`
            : `<p>Оформите доступ за <span class="price-big">${price} ₽</span></p>
               <p class="pay-hint">После проверки оплаты ссылка появится в личном кабинете</p>
               <a class="btn btn-gold" style="display:inline-block;margin-top:1rem;min-width:220px" href="pay.html?id=${encodeURIComponent(course.id)}&title=${encodeURIComponent(course.title)}">Получить доступ · ${price} ₽</a>`
        }
      </section>
    `;
  }

  document.addEventListener("DOMContentLoaded", async () => {
    if (window.HartI18n) await HartI18n.init();
    load().catch(() => {
    document.getElementById("course-root").innerHTML =
      '<p class="empty">Ошибка загрузки</p>';
    });
  });
})();

(function () {
  const params = new URLSearchParams(location.search);
  const courseId = params.get("id") || "";
  const learnMode = params.get("learn") === "1";
  const price = window.SITE_CONFIG?.accessPrice || window.SITE_CONFIG?.priceRub || 199;

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function progressKey(lessonId) {
    return `hart_lesson_${courseId}_${lessonId}`;
  }

  function renderFacts(lesson) {
    const items = lesson.facts || [];
    return (
      '<dl class="facts-list">' +
      items
        .map(
          (f) =>
            `<dt>${escapeHtml(f.label || "")}</dt><dd>${escapeHtml(f.value || "")}</dd>`
        )
        .join("") +
      "</dl>"
    );
  }

  function renderPoints(lesson) {
    const pts = lesson.points || [];
    if (!pts.length) return "";
    return (
      '<ul class="lesson-points">' +
      pts.map((p) => `<li>${escapeHtml(p)}</li>`).join("") +
      "</ul>"
    );
  }

  function renderSteps(lesson) {
    const steps = lesson.steps || [];
    return (
      '<ol class="lesson-steps">' +
      steps
        .map(
          (s, i) =>
            `<li><b>${escapeHtml(s.title || "Шаг " + (i + 1))}</b><p>${escapeHtml(s.text || "")}</p></li>`
        )
        .join("") +
      "</ol>"
    );
  }

  function renderRichBody(text) {
    if (!text) return "";
    const blocks = text.split(/\n\n+/);
    return (
      '<div class="lesson-rich">' +
      blocks
        .map((block) => {
          const raw = block.trim();
          if (!raw) return "";
          if (raw.startsWith("---")) {
            return '<hr class="lesson-hr" />';
          }
          if (raw.startsWith("## ")) {
            return `<h3 class="lesson-h3">${escapeHtml(raw.slice(3).trim())}</h3>`;
          }
          if (raw.startsWith("### §") || raw.startsWith("### ")) {
            const t = raw.replace(/^###\s*/, "").trim();
            return `<h4 class="lesson-h4 lesson-section">${escapeHtml(t)}</h4>`;
          }
          if (/^\d+\.\s/m.test(raw)) {
            const items = raw
              .split(/\n/)
              .filter((x) => x.trim())
              .map((x) => `<li>${escapeHtml(x.replace(/^\d+\.\s*/, ""))}</li>`)
              .join("");
            return `<ol class="lesson-rich-list">${items}</ol>`;
          }
          const html = raw.replace(/\*\*([^*]+)\*\*/g, (_, s) => "<strong>" + escapeHtml(s) + "</strong>");
          const safe = html.includes("<strong>") ? html : escapeHtml(raw);
          return `<p>${safe}</p>`;
        })
        .join("") +
      "</div>"
    );
  }

  function renderTasks(lesson) {
    const tasks = lesson.tasks || [];
    return (
      '<ol class="task-list">' +
      tasks
        .map((t, i) => {
          const title = escapeHtml(t.title || "Задание " + (i + 1));
          const instr = escapeHtml(t.instruction || "");
          if (t.kind === "link" && t.url) {
            return `<li class="task-item"><b>${title}</b><p>${instr}</p><a class="btn btn-gold btn-sm" href="${escapeHtml(t.url)}" target="_blank" rel="noopener noreferrer">Открыть тренажёр →</a></li>`;
          }
          return `<li class="task-item"><b>${title}</b><p>${instr}</p><textarea class="task-input" rows="3" placeholder="Ваш ответ или заметки…" data-task="${i}"></textarea></li>`;
        })
        .join("") +
      "</ol>"
    );
  }

  function renderQuiz(lesson, lessonId) {
    const qs = lesson.questions || [];
    return (
      '<div class="quiz-wrap" data-lesson="' +
      escapeHtml(lessonId) +
      '">' +
      qs
        .map((q, qi) => {
          const opts = (q.options || [])
            .map(
              (o, oi) =>
                `<button type="button" class="quiz-opt" data-q="${qi}" data-o="${oi}">${escapeHtml(o)}</button>`
            )
            .join("");
          return `<div class="quiz-q" data-correct="${q.correct ?? 0}" data-explain="${escapeHtml(q.explain || "")}">
            <p class="quiz-title">${qi + 1}. ${escapeHtml(q.q || "")}</p>
            <div class="quiz-options">${opts}</div>
            <p class="quiz-feedback" aria-live="polite"></p>
          </div>`;
        })
        .join("") +
      '<p class="quiz-score pay-hint"></p></div>'
    );
  }

  function youtubeWatchUrl(id) {
    return "https://www.youtube.com/watch?v=" + encodeURIComponent(id);
  }

  function youtubeEmbedUrl(id) {
    return (
      "https://www.youtube-nocookie.com/embed/" +
      encodeURIComponent(id) +
      "?rel=0&modestbranding=1&playsinline=1"
    );
  }

  function rutubeWatchUrl(id) {
    return "https://rutube.ru/video/" + encodeURIComponent(id) + "/";
  }

  function rutubeEmbedUrl(id) {
    return "https://rutube.ru/play/embed/" + encodeURIComponent(id) + "/";
  }

  function renderVideo(lesson, title) {
    const rutube = (lesson.rutubeId || "").trim();
    const yt = (lesson.youtubeId || "").trim();
    if (!rutube && !yt) {
      return '<p class="form-msg err">Видео не настроено для этого курса.</p>';
    }
    let html = "";
    if (rutube) {
      html += `<p class="pay-hint ok">Плеер RuTube — обычно работает в России без VPN.</p>
        <div class="lesson-video lesson-video-rutube">
          <iframe src="${escapeHtml(rutubeEmbedUrl(rutube))}" title="${title}" allow="clipboard-write; autoplay" allowfullscreen loading="lazy"></iframe>
        </div>
        <p class="video-fallback"><a class="btn btn-gold btn-sm" href="${escapeHtml(rutubeWatchUrl(rutube))}" target="_blank" rel="noopener noreferrer">Открыть на RuTube</a></p>`;
    }
    if (yt) {
      html += `<p class="pay-hint" style="margin-top:1rem">YouTube — в РФ часто недоступен без VPN. Если ниже пусто — смотрите RuTube выше.</p>
        <div class="lesson-video lesson-video-yt">
          <iframe src="${escapeHtml(youtubeEmbedUrl(yt))}" title="${title}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe>
        </div>
        <p class="video-fallback"><a class="btn btn-outline btn-sm" href="${escapeHtml(youtubeWatchUrl(yt))}" target="_blank" rel="noopener noreferrer">Открыть на YouTube</a></p>`;
    }
    return html;
  }

  function renderVideoStage(lesson, title) {
    const rutube = (lesson.rutubeId || "").trim();
    const yt = (lesson.youtubeId || "").trim();
    if (!rutube && !yt) return "";
    const src = rutube ? rutubeEmbedUrl(rutube) : youtubeEmbedUrl(yt);
    const allow = rutube
      ? "clipboard-write; autoplay"
      : "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
    return `<div class="lesson-video"><iframe src="${escapeHtml(src)}" title="${title}" allow="${allow}" allowfullscreen loading="lazy"></iframe></div>`;
  }

  function doneKey(lessonId) {
    return `hart_done_${courseId}_${lessonId}`;
  }

  function isLessonDone(lessonId) {
    return localStorage.getItem(doneKey(lessonId)) === "1";
  }

  const LESSON_ICONS = {
    video:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6.5v11l9-5.5-9-5.5z" fill="currentColor"/></svg>',
    facts:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v5M12 8h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    quiz:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h14v3H5V5zm0 6h9v3H5v-3zm0 6h14v2H5v-2z" fill="currentColor"/></svg>',
    practice:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l4 4 10-10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    embed:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14L6 10l4-4M14 10l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    default:
      '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="2" fill="currentColor"/></svg>',
  };

  function lessonIconHtml(lesson) {
    const t = lesson.type || "";
    if (t === "lesson" || t === "video") return LESSON_ICONS.video;
    if (t === "facts") return LESSON_ICONS.facts;
    if (t === "quiz") return LESSON_ICONS.quiz;
    if (t === "practice") return LESSON_ICONS.practice;
    if (t === "embed") return LESSON_ICONS.embed;
    return LESSON_ICONS.default;
  }

  function lessonTypeLabel(lesson) {
    const t = lesson.type || "";
    const map = {
      lesson: "Видеоурок",
      video: "Видео",
      facts: "Справка",
      quiz: "Тест",
      practice: "Практика",
      embed: "Платформа",
      content: "Материал",
      steps: "Шаги",
    };
    return map[t] || "Урок";
  }

  function groupLessons(lessons) {
    const intro = [];
    const modules = [];
    const outro = [];
    lessons.forEach((lesson, idx) => {
      const item = { lesson, idx };
      const t = lesson.type || "";
      const id = String(lesson.id || "");
      if (t === "quiz" || t === "practice" || id.includes("checklist")) {
        outro.push(item);
      } else if (
        t === "lesson" ||
        t === "video" ||
        t === "content" ||
        t === "steps" ||
        id.includes("-mod-")
      ) {
        modules.push(item);
      } else {
        intro.push(item);
      }
    });
    const sections = [];
    if (intro.length) sections.push({ title: "Введение", items: intro });
    if (modules.length) sections.push({ title: "Модули обучения", items: modules });
    if (outro.length) sections.push({ title: "Итог и проверка", items: outro });
    if (!sections.length) sections.push({ title: "Программа", items: lessons.map((lesson, idx) => ({ lesson, idx })) });
    return sections;
  }

  function getLessonBody(lesson) {
    const title = escapeHtml(lesson.title || "Урок");
    if (lesson.type === "lesson") {
      let body = "";
      if (lesson.summary) {
        body += `<p class="lesson-summary">${escapeHtml(lesson.summary)}</p>`;
      }
      body += renderPoints(lesson);
      return body;
    }
    if (lesson.type === "facts") return renderFacts(lesson);
    if (lesson.type === "video") return renderVideo(lesson, title);
    if (lesson.type === "practice" && lesson.checklist) {
      return (
        '<ul class="lesson-checklist">' +
        lesson.checklist
          .map(
            (c) =>
              `<li><label><input type="checkbox" data-check="${escapeHtml(c)}"> ${escapeHtml(c)}</label></li>`
          )
          .join("") +
        "</ul>"
      );
    }
    if (lesson.type === "content" && lesson.body) return renderRichBody(lesson.body);
    if (lesson.type === "steps" && lesson.steps) return renderSteps(lesson);
    if (lesson.points && lesson.points.length) return renderPoints(lesson);
    if (lesson.type === "quiz" && lesson.questions) {
      return renderQuiz(lesson, lesson.id || "quiz");
    }
    if (lesson.type === "embed" && lesson.embedUrl) {
      const url = escapeHtml(lesson.embedUrl);
      return `<p class="pay-hint">${escapeHtml(lesson.hint || "Работайте с интерактивом ниже.")}</p>
        <div class="lesson-embed"><iframe src="${url}" title="${title}" loading="lazy" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe></div>`;
    }
    const paras = (lesson.body || "")
      .split(/\n\n+/)
      .map((p) => `<p>${escapeHtml(p.trim())}</p>`)
      .join("");
    return `<div class="lesson-text">${paras}</div>`;
  }

  function getLessonPractice(lesson) {
    if (!lesson.tasks || !lesson.tasks.length) return "";
    return "<h4 class=\"lesson-sub\">Практика</h4>" + renderTasks(lesson);
  }

  function resourceCard(href, title, sub) {
    return `<a class="learn-resource-card" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">
      <span class="learn-resource-icon" aria-hidden="true">↗</span>
      <div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(sub)}</span></div>
    </a>`;
  }

  function getLessonResources(lesson, course) {
    const cards = [];
    const rutube = (lesson.rutubeId || "").trim();
    const yt = (lesson.youtubeId || "").trim();
    if (rutube) {
      cards.push(resourceCard(rutubeWatchUrl(rutube), "Видео на RuTube", "Открыть в отдельной вкладке"));
    }
    if (yt) {
      cards.push(resourceCard(youtubeWatchUrl(yt), "YouTube", "Может потребоваться VPN в РФ"));
    }
    const partner = course.partnerUrl || course.url || "";
    if (partner) {
      cards.push(
        resourceCard(
          partner,
          course.provider || "Платформа партнёра",
          "Официальный сайт курса и сертификация"
        )
      );
    }
    if (!cards.length) {
      return '<p class="pay-hint">Для этого блока внешние ссылки не нужны — весь материал в разделе «Обзор».</p>';
    }
    return '<div class="learn-resources">' + cards.join("") + "</div>";
  }

  function flashPanel(el) {
    if (!el) return;
    el.classList.remove("is-active");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => el.classList.add("is-active"));
    });
  }

  function renderCourseLanding(course, opts) {
    const {
      fullAccess,
      showPlayer,
      lessonCount,
      modCount,
      quizCount,
      totalHours,
      accessBlock,
      price,
    } = opts;
    const provider = course.provider ? escapeHtml(course.provider) : "";
    const desc = (course.desc || "").trim().split("\n")[0] || (course.about || "").trim().split("\n")[0];
    const outcomes = (course.learn || []).slice(0, 5);
    const outcomesHtml = outcomes.length
      ? `<div class="course-landing-outcomes">
          <h2>Чему вы научитесь</h2>
          <ul class="course-outcomes-list">${outcomes.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>
        </div>`
      : "";

    const cta = !fullAccess
      ? `<div class="course-landing-cta">${accessBlock}</div>`
      : showPlayer
        ? `<div class="course-landing-cta"><a class="btn btn-gold" href="#hart-player">Начать обучение ↓</a><p class="pay-hint ok">Доступ открыт · ${lessonCount} блоков</p></div>`
        : `<div class="course-landing-cta">${accessBlock}</div>`;

    return `
      <article class="course-landing course-landing--hero">
        <span class="course-landing-badge">Онлайн-программа HART</span>
        <h1>${escapeHtml(course.title)}</h1>
        <div class="course-landing-stats">
          <span class="course-stat-pill"><strong>${escapeHtml(totalHours)}</strong> объём</span>
          <span class="course-stat-pill"><strong>${modCount}</strong> модулей</span>
          <span class="course-stat-pill"><strong>${lessonCount}</strong> блоков</span>
          ${quizCount ? `<span class="course-stat-pill"><strong>${quizCount}</strong> тест</span>` : ""}
          ${provider ? `<span class="course-stat-pill">${provider}</span>` : ""}
          <span class="course-stat-pill"><strong>${price} ₽</strong> доступ</span>
        </div>
        ${desc ? `<p class="course-landing-desc">${escapeHtml(desc)}</p>` : ""}
        ${outcomesHtml}
        ${cta}
      </article>`;
  }

  function pickDemoLessons(lessons) {
    const out = [];
    const seen = new Set();
    const want = (pred) => {
      const L = lessons.find((l) => pred(l) && !seen.has(l.id));
      if (L) {
        seen.add(L.id);
        out.push(L);
      }
    };
    want((l) => (l.type === "lesson" || l.type === "video") && (l.rutubeId || l.youtubeId));
    want((l) => l.type === "facts");
    want((l) => l.type === "content" || l.type === "steps" || (l.id && String(l.id).includes("-mod-")));
    return out.slice(0, 3);
  }

  function bindLessonInteractions(root) {
    root.querySelectorAll(".quiz-opt").forEach((btn) => {
      btn.onclick = () => {
        const block = btn.closest(".quiz-q");
        const correct = parseInt(block.dataset.correct, 10);
        const chosen = parseInt(btn.dataset.o, 10);
        const fb = block.querySelector(".quiz-feedback");
        block.querySelectorAll(".quiz-opt").forEach((b) => {
          b.disabled = true;
          b.classList.remove("ok", "bad");
        });
        if (chosen === correct) {
          btn.classList.add("ok");
          fb.textContent = "✓ Верно. " + (block.dataset.explain || "");
          fb.className = "quiz-feedback ok";
        } else {
          btn.classList.add("bad");
          block.querySelector(`.quiz-opt[data-o="${correct}"]`)?.classList.add("ok");
          fb.textContent = "✗ Неверно. " + (block.dataset.explain || "Повторите материал.");
          fb.className = "quiz-feedback err";
        }
        const wrap = btn.closest(".quiz-wrap");
        const total = wrap.querySelectorAll(".quiz-q").length;
        const done = wrap.querySelectorAll(".quiz-feedback.ok").length;
        const score = wrap.querySelector(".quiz-score");
        if (score) score.textContent = `Результат: ${done} из ${total}`;
      };
    });

    root.querySelectorAll(".lesson-checklist input").forEach((cb) => {
      const key = progressKey("chk_" + cb.dataset.check);
      if (localStorage.getItem(key) === "1") cb.checked = true;
      cb.onchange = () => localStorage.setItem(key, cb.checked ? "1" : "0");
    });

    root.querySelectorAll(".task-input").forEach((ta) => {
      const key = progressKey("task_" + ta.dataset.task);
      const saved = localStorage.getItem(key);
      if (saved) ta.value = saved;
      ta.oninput = () => localStorage.setItem(key, ta.value);
    });
  }

  function renderLearnShell(course, lessons, opts) {
    if (!lessons.length) return "";
    const demo = opts?.demo;
    const sections = groupLessons(lessons);
    const nav = [];
    let sidebarHtml = "";
    sections.forEach((sec) => {
      sidebarHtml += `<div class="learn-section-title">${escapeHtml(sec.title)}</div>`;
      sec.items.forEach(({ lesson, idx }) => {
        const lid = lesson.id || "u" + idx;
        const done = isLessonDone(lid) ? " is-done" : "";
        nav.push({ lesson, idx, lid });
        const i = nav.length - 1;
        sidebarHtml += `<button type="button" class="learn-item${i === 0 ? " is-active" : ""}${done}" data-nav="${i}" data-lesson-id="${escapeHtml(lid)}">
          <span class="learn-item-num">${i + 1}</span>
          <span class="learn-item-check" aria-hidden="true">${lessonIconHtml(lesson)}</span>
          <span class="learn-item-body">
            <span class="learn-item-title">${escapeHtml(lesson.title || "Урок")}</span>
            <span class="learn-item-meta">${escapeHtml(lessonTypeLabel(lesson))}${lesson.duration ? " · " + escapeHtml(lesson.duration) : ""}</span>
          </span>
        </button>`;
      });
    });

    const demoBanner = demo
      ? `<div class="learn-demo-banner"><span>Просмотр: ${nav.length} из ${course.lessons?.length || 0} уроков</span><a href="pay.html?id=${encodeURIComponent(course.id)}&title=${encodeURIComponent(course.title)}">Открыть полную программу · ${price} ₽</a></div>`
      : "";

    return `<section class="course-section" id="hart-player">
      ${demoBanner}
      <div class="learn-shell" id="hart-learn" data-demo="${demo ? "1" : "0"}">
        <div class="learn-sidebar-backdrop" id="learn-backdrop" aria-hidden="true"></div>
        <aside class="learn-sidebar" id="learn-sidebar">
          <div class="learn-sidebar-head">
            <h2>Содержание курса</h2>
            <div class="learn-progress-wrap">
              <div class="learn-progress-ring" id="learn-ring" style="--pct:0%"><span id="learn-pct">0%</span></div>
              <div class="learn-progress-text"><strong id="learn-progress-label">0 из ${nav.length}</strong> блоков завершено</div>
            </div>
          </div>
          <nav class="learn-curriculum" aria-label="Программа курса">${sidebarHtml}</nav>
        </aside>
        <main class="learn-main">
          <div class="learn-video-stage is-empty" id="learn-video-stage">
            <div class="learn-video-placeholder" id="learn-video-ph">
              <strong>${escapeHtml(course.title)}</strong>
              <span>Выберите урок или нажмите «Далее»</span>
            </div>
          </div>
          <div class="learn-lesson-head">
            <p class="learn-lesson-kicker" id="learn-lesson-kicker">Урок 1 из ${nav.length}</p>
            <h1 id="learn-lesson-title">—</h1>
            <button type="button" class="learn-complete-btn" id="learn-complete">Отметить пройденным</button>
          </div>
          <div class="learn-tabs" role="tablist">
            <button type="button" class="learn-tab is-active" data-tab="overview" role="tab">Обзор</button>
            <button type="button" class="learn-tab" data-tab="practice" role="tab" hidden id="learn-tab-practice">Практика</button>
            <button type="button" class="learn-tab" data-tab="quiz" role="tab" hidden id="learn-tab-quiz">Тест</button>
            <button type="button" class="learn-tab" data-tab="resources" role="tab">Ресурсы</button>
          </div>
          <div class="learn-panels">
            <div class="learn-panel is-active" data-panel="overview" id="learn-panel-overview"></div>
            <div class="learn-panel" data-panel="practice" id="learn-panel-practice"></div>
            <div class="learn-panel" data-panel="quiz" id="learn-panel-quiz"></div>
            <div class="learn-panel" data-panel="resources" id="learn-panel-resources"></div>
          </div>
          <footer class="learn-nav-bar">
            <button type="button" class="learn-nav-btn" id="learn-prev" disabled>← Назад</button>
            <button type="button" class="learn-nav-btn learn-nav-btn--primary" id="learn-next">Далее →</button>
          </footer>
        </main>
      </div>
      <button type="button" class="learn-toggle-sidebar" id="learn-toggle">Содержание</button>
    </section>`;
  }

  function initLearnPlayer(root, course, lessons) {
    const shell = root.querySelector("#hart-learn");
    if (!shell) return;

    const sections = groupLessons(lessons);
    const nav = [];
    sections.forEach((sec) => {
      sec.items.forEach((item) => nav.push(item));
    });
    if (!nav.length) return;

    let current = 0;
    const stage = root.querySelector("#learn-video-stage");
    const kickerEl = root.querySelector("#learn-lesson-kicker");
    const titleEl = root.querySelector("#learn-lesson-title");
    const completeBtn = root.querySelector("#learn-complete");
    const panelOverview = root.querySelector("#learn-panel-overview");
    const panelPractice = root.querySelector("#learn-panel-practice");
    const panelQuiz = root.querySelector("#learn-panel-quiz");
    const panelResources = root.querySelector("#learn-panel-resources");
    const tabPractice = root.querySelector("#learn-tab-practice");
    const tabQuiz = root.querySelector("#learn-tab-quiz");
    const prevBtn = root.querySelector("#learn-prev");
    const nextBtn = root.querySelector("#learn-next");
    const ring = root.querySelector("#learn-ring");
    const pctEl = root.querySelector("#learn-pct");
    const progressLabel = root.querySelector("#learn-progress-label");
    const items = root.querySelectorAll(".learn-item");

    function updateProgress() {
      const done = nav.filter(({ lesson }) => isLessonDone(lesson.id || "")).length;
      const pct = nav.length ? Math.round((done / nav.length) * 100) : 0;
      if (ring) ring.style.setProperty("--pct", pct + "%");
      if (pctEl) pctEl.textContent = pct + "%";
      if (progressLabel) progressLabel.textContent = `${done} из ${nav.length} блоков завершено`;
      items.forEach((btn) => {
        const id = btn.dataset.lessonId;
        btn.classList.toggle("is-done", isLessonDone(id));
      });
    }

    function setActiveTab(name) {
      root.querySelectorAll(".learn-tab").forEach((t) => {
        t.classList.toggle("is-active", t.dataset.tab === name && !t.hidden);
      });
      root.querySelectorAll(".learn-panel").forEach((p) => {
        p.classList.toggle("is-active", p.dataset.panel === name);
      });
    }

    function showLesson(index) {
      current = Math.max(0, Math.min(index, nav.length - 1));
      const { lesson } = nav[current];
      const lid = lesson.id || "u" + current;
      const title = lesson.title || "Урок";

      items.forEach((btn, i) => btn.classList.toggle("is-active", i === current));
      const activeBtn = items[current];
      activeBtn?.scrollIntoView({ block: "nearest", behavior: "smooth" });

      if (kickerEl) {
        kickerEl.textContent = `Урок ${current + 1} из ${nav.length} · ${lessonTypeLabel(lesson)}`;
      }
      if (titleEl) titleEl.textContent = title;

      const videoHtml = renderVideoStage(lesson, escapeHtml(title));
      if (stage) {
        if (videoHtml) {
          stage.classList.remove("is-empty");
          stage.innerHTML = videoHtml;
        } else {
          stage.classList.add("is-empty");
          stage.innerHTML = `<div class="learn-video-placeholder"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(lessonTypeLabel(lesson))}</span></div>`;
        }
      }

      if (panelOverview) panelOverview.innerHTML = getLessonBody(lesson);
      if (panelPractice) {
        const pr = getLessonPractice(lesson);
        panelPractice.innerHTML = pr || '<p class="pay-hint">Для этого блока отдельная практика не требуется — отметьте «Пройдено» после изучения обзора.</p>';
      }
      if (panelQuiz) {
        panelQuiz.innerHTML =
          lesson.type === "quiz" && lesson.questions
            ? renderQuiz(lesson, lid)
            : "";
      }
      if (panelResources) panelResources.innerHTML = getLessonResources(lesson, course);

      const hasPractice = !!(lesson.tasks && lesson.tasks.length);
      const hasQuiz = lesson.type === "quiz" && lesson.questions;
      if (tabPractice) tabPractice.hidden = !hasPractice;
      if (tabQuiz) tabQuiz.hidden = !hasQuiz;

      let activePanel = panelOverview;
      if (hasQuiz) {
        setActiveTab("quiz");
        activePanel = panelQuiz;
      } else {
        setActiveTab("overview");
      }
      flashPanel(activePanel);

      if (completeBtn) {
        const done = isLessonDone(lid);
        completeBtn.classList.toggle("is-done", done);
        completeBtn.textContent = done ? "✓ Пройдено" : "Отметить пройденным";
      }

      if (prevBtn) prevBtn.disabled = current === 0;
      if (nextBtn) {
        nextBtn.disabled = current >= nav.length - 1;
        nextBtn.textContent = current >= nav.length - 1 ? "Конец программы" : "Далее →";
      }

      bindLessonInteractions(root);
      updateProgress();
      history.replaceState(null, "", "#lesson-" + encodeURIComponent(lid));
    }

    root.querySelectorAll(".learn-tab").forEach((tab) => {
      tab.onclick = () => {
        if (!tab.hidden) {
          setActiveTab(tab.dataset.tab);
          const panel = root.querySelector(`.learn-panel[data-panel="${tab.dataset.tab}"]`);
          flashPanel(panel);
        }
      };
    });

    items.forEach((btn) => {
      btn.onclick = () => showLesson(parseInt(btn.dataset.nav, 10));
    });

    if (completeBtn) {
      completeBtn.onclick = () => {
        const lid = nav[current].lesson.id || "u" + current;
        const next = !isLessonDone(lid);
        if (next) localStorage.setItem(doneKey(lid), "1");
        else localStorage.removeItem(doneKey(lid));
        showLesson(current);
      };
    }

    if (prevBtn) prevBtn.onclick = () => showLesson(current - 1);
    if (nextBtn) {
      nextBtn.onclick = () => {
        if (current < nav.length - 1) {
          const lid = nav[current].lesson.id || "u" + current;
          localStorage.setItem(doneKey(lid), "1");
          showLesson(current + 1);
        }
      };
    }

    const sidebar = root.querySelector("#learn-sidebar");
    const backdrop = root.querySelector("#learn-backdrop");
    const toggle = root.querySelector("#learn-toggle");
    const closeSidebar = () => {
      sidebar?.classList.remove("is-open");
      backdrop?.classList.remove("is-open");
    };
    toggle?.addEventListener("click", () => {
      sidebar?.classList.toggle("is-open");
      backdrop?.classList.toggle("is-open");
    });
    backdrop?.addEventListener("click", closeSidebar);

    const hashRaw = location.hash.replace(/^#lesson-/, "");
    const hashId = hashRaw ? decodeURIComponent(hashRaw) : "";
    const startIdx = hashId ? nav.findIndex(({ lesson }) => (lesson.id || "") === hashId) : 0;
    showLesson(startIdx >= 0 ? startIdx : 0);

    document.addEventListener("keydown", (e) => {
      if (!shell.isConnected) return;
      if (e.target.closest("textarea, input, select")) return;
      if (e.key === "ArrowRight" && !nextBtn?.disabled) {
        e.preventDefault();
        nextBtn.click();
      }
      if (e.key === "ArrowLeft" && !prevBtn?.disabled) {
        e.preventDefault();
        prevBtn.click();
      }
    });
  }

  function renderPlayer(course, opts) {
    const lessons = course.lessons || [];
    if (!lessons.length) return "";
    const list = opts?.demo ? pickDemoLessons(lessons) : lessons;
    return renderLearnShell(course, list, opts);
  }

  async function load() {
    const root = document.getElementById("course-root");
    root.innerHTML = '<div class="course-loading">Загрузка программы курса…</div>';
    const res = await fetch("/api/course?id=" + encodeURIComponent(courseId));
    const data = await res.json();
    if (!data.ok || !data.course) {
      root.innerHTML =
        '<p class="form-msg err">Курс не найден или ошибка сервера. <a href="index.html">В каталог</a></p>';
      return;
    }
    const course = data.course;
    if (window.HartSeo?.setCourse) {
      window.HartSeo.setCourse(course);
    } else {
      document.title = course.title + " — Клуб знаний HART";
    }
    const bc = document.getElementById("bc-title");
    if (bc) bc.textContent = course.title;

    let hasAccess = false;
    let isAdmin = false;
    if (window.HartSession?.isLoggedIn?.()) {
      hasAccess = await window.HartSession.hasCourseAccess(courseId);
      isAdmin = window.HartSession.isAdmin?.() || false;
    }

    const modules = (course.modules || []).map((m) => `<li>${escapeHtml(m)}</li>`).join("");
    const learn = (course.learn || []).map((l) => `<li>${escapeHtml(l)}</li>`).join("");
    const partnerUrl = course.partnerUrl || course.url || "";
    const lessonCount = (course.lessons || []).length;
    const quizCount = (course.lessons || []).filter((l) => l.type === "quiz").length;
    const modCount = (course.lessons || []).filter(
      (l) => l.type === "lesson" || String(l.id || "").includes("-mod-")
    ).length;
    const totalHours = course.totalHours ? `${course.totalHours}+ ч` : course.duration || "—";

    const devFull = isLocalDev() || isAdmin || learnMode;
    const fullAccess = hasAccess || devFull;
    const showPlayer = fullAccess && (course.lessons?.length || 0) > 0;
    const showDemo = !fullAccess && course.lessons?.length;
    const playerHtml = showPlayer
      ? renderPlayer(course)
      : showDemo
        ? renderPlayer(course, { demo: true })
        : "";

    const accessBlock = fullAccess
      ? `<p class="pay-hint ok">${devFull ? "Режим проверки: все " + lessonCount + " блоков открыты" : "Доступ открыт"} · ${modCount} модулей + ${quizCount} тест</p>
         ${showPlayer ? `<a class="btn btn-gold" href="#hart-player">К материалам ↓</a>` : ""}
         ${partnerUrl ? `<p class="pay-hint" style="margin-top:1rem"><a href="${escapeHtml(partnerUrl)}" target="_blank" rel="noopener noreferrer">Доп. материалы: ${escapeHtml(course.provider || "партнёр")}</a></p>` : ""}
         <p class="pay-hint"><a href="cabinet.html">Все курсы в кабинете</a></p>`
      : showDemo
        ? `<p class="pay-hint">Ниже — начало справки и 2 модуля. Полностью: <b>${lessonCount} блоков</b>.</p>
           <a class="btn btn-gold" style="display:inline-block;margin-top:1rem" href="pay.html?id=${encodeURIComponent(course.id)}&title=${encodeURIComponent(course.title)}">Получить доступ · ${price} ₽</a>`
        : `<p>Оформите доступ за <span class="price-big">${price} ₽</span></p>
           <p class="pay-hint">${lessonCount} блоков: справка, модули, тест</p>
           <a class="btn btn-gold" style="display:inline-block;margin-top:1rem;min-width:220px" href="pay.html?id=${encodeURIComponent(course.id)}&title=${encodeURIComponent(course.title)}">Получить доступ · ${price} ₽</a>`;

    root.innerHTML =
      renderCourseLanding(course, {
        fullAccess,
        showPlayer,
        lessonCount,
        modCount,
        quizCount,
        totalHours,
        accessBlock,
        price,
      }) +
      playerHtml +
      (fullAccess && partnerUrl
        ? `<footer class="course-landing-footer"><p class="pay-hint"><a href="${escapeHtml(partnerUrl)}" target="_blank" rel="noopener noreferrer">Материалы ${escapeHtml(course.provider || "партнёра")} →</a> · <a href="cabinet.html">Личный кабинет</a></p></footer>`
        : "");

    if (showPlayer || showDemo) {
      const list = showDemo ? pickDemoLessons(course.lessons || []) : course.lessons || [];
      initLearnPlayer(root, course, list);
    } else {
      bindLessonInteractions(root);
    }

    if (learnMode && (showPlayer || showDemo)) {
      document.getElementById("hart-player")?.scrollIntoView({ behavior: "smooth" });
    }
  }

  function isLocalDev() {
    const h = location.hostname;
    return h === "127.0.0.1" || h === "localhost" || window.SITE_CONFIG?.devMode === true;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const boot = async () => {
      if (isLocalDev() && window.HartSession?.ensureDevLogin) {
        await window.HartSession.ensureDevLogin();
      }
      await load();
    };
    boot().catch((e) => {
      document.getElementById("course-root").innerHTML =
        '<p class="form-msg err">Ошибка: ' +
        (e.message || "загрузка") +
        ". Запустите start-site.bat в этой папке.</p>";
    });
  });
})();

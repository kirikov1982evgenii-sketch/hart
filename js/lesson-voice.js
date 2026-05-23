/**
 * Видеорежим урока: слайды + озвучка (Web Speech API, русский голос если есть).
 */
(function (global) {
  let voicesReady = false;

  function stripMd(text) {
    return (text || "")
      .replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/^#+\s*/gm, "")
      .replace(/^---\s*/gm, "")
      .replace(/`/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function bodyToSlides(body) {
    if (!body) return [];
    const parts = body.split(/\n---\n+|\n\n(?=### )/);
    const slides = [];
    for (const part of parts) {
      const raw = part.trim();
      if (!raw) continue;
      let title = "";
      const h = raw.match(/^###\s*(.+?)$/m) || raw.match(/^##\s*(.+?)$/m);
      if (h) title = stripMd(h[1]);
      const speech = stripMd(raw);
      if (speech.length < 12) continue;
      slides.push({
        title: title || "Слайд",
        speech: speech.slice(0, 4000),
        html: raw,
      });
    }
    if (!slides.length && body.trim()) {
      slides.push({ title: "Урок", speech: stripMd(body).slice(0, 4000), html: body });
    }
    return slides;
  }

  function factsToSlides(facts) {
    const slides = [{ title: "Справка о программе", speech: "Краткая справка о программе. Слушайте факты по порядку.", html: "" }];
    (facts || []).forEach((f, i) => {
      const label = f.label || "Пункт " + (i + 1);
      const value = f.value || "";
      slides.push({
        title: label,
        speech: `${label}. ${value}`,
        html: `<p><b>${label}</b></p><p>${value}</p>`,
      });
    });
    return slides;
  }

  function pickRuVoice() {
    const list = speechSynthesis.getVoices();
    return (
      list.find((v) => /ru-RU|ru_RU/i.test(v.lang) && /google|microsoft|irina|pavel|dmitri/i.test(v.name)) ||
      list.find((v) => v.lang && v.lang.toLowerCase().startsWith("ru")) ||
      list[0] ||
      null
    );
  }

  function loadVoices() {
    return new Promise((resolve) => {
      const v = pickRuVoice();
      if (v) {
        voicesReady = true;
        resolve(v);
        return;
      }
      speechSynthesis.onvoiceschanged = () => {
        voicesReady = true;
        resolve(pickRuVoice());
      };
      setTimeout(() => resolve(pickRuVoice()), 500);
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function renderCinema(lessonId, slides, extraHtml) {
    const data = encodeURIComponent(JSON.stringify(slides));
    return (
      `<div class="lesson-cinema" data-lesson="${escapeHtml(lessonId)}" data-slides="${data}">
        <div class="cinema-screen">
          <p class="cinema-badge">▶ Видеоурок с озвучкой</p>
          <h4 class="cinema-title"></h4>
          <div class="cinema-body"></div>
        </div>
        <div class="cinema-progress-wrap"><div class="cinema-progress-bar"></div></div>
        <div class="cinema-controls">
          <button type="button" class="btn btn-gold btn-sm cinema-play">▶ Озвучка</button>
          <button type="button" class="btn btn-outline btn-sm cinema-pause" disabled>⏸ Пауза</button>
          <button type="button" class="btn btn-outline btn-sm cinema-prev">◀</button>
          <button type="button" class="btn btn-outline btn-sm cinema-next">▶</button>
          <span class="cinema-counter">1 / ${slides.length}</span>
          <label class="cinema-rate-label">Скорость <input type="range" class="cinema-rate" min="0.75" max="1.35" step="0.05" value="1"></label>
        </div>
        <p class="pay-hint cinema-hint">Озвучка в браузере (русский голос Windows/Chrome). Можно слушать без чтения экрана.</p>
        <details class="cinema-transcript-wrap"><summary>Показать текст слайда</summary><div class="cinema-transcript"></div></details>
        ${extraHtml || ""}
      </div>`
    );
  }

  function formatSlideHtml(raw, renderRich) {
    if (!raw) return "<p>—</p>";
    if (renderRich) return renderRich(raw);
    return "<p>" + escapeHtml(stripMd(raw)) + "</p>";
  }

  function initCinema(el, renderRich) {
    if (!el || el.dataset.cinemaInit === "1") return;
    let slides = [];
    try {
      slides = JSON.parse(decodeURIComponent(el.dataset.slides || "%5B%5D"));
    } catch {
      slides = [];
    }
    if (!slides.length) return;
    el.dataset.cinemaInit = "1";

    let idx = 0;
    let speaking = false;
    let voice = null;
    let rate = 1;

    const titleEl = el.querySelector(".cinema-title");
    const bodyEl = el.querySelector(".cinema-body");
    const counterEl = el.querySelector(".cinema-counter");
    const barEl = el.querySelector(".cinema-progress-bar");
    const transcriptEl = el.querySelector(".cinema-transcript");
    const btnPlay = el.querySelector(".cinema-play");
    const btnPause = el.querySelector(".cinema-pause");
    const btnPrev = el.querySelector(".cinema-prev");
    const btnNext = el.querySelector(".cinema-next");
    const rateInput = el.querySelector(".cinema-rate");

    function showSlide(i) {
      idx = Math.max(0, Math.min(slides.length - 1, i));
      const s = slides[idx];
      titleEl.textContent = s.title || "Слайд " + (idx + 1);
      bodyEl.innerHTML = formatSlideHtml(s.html, renderRich);
      if (transcriptEl) transcriptEl.innerHTML = "<p>" + escapeHtml(s.speech) + "</p>";
      counterEl.textContent = idx + 1 + " / " + slides.length;
      barEl.style.width = ((idx + 1) / slides.length) * 100 + "%";
    }

    function stopSpeech() {
      speechSynthesis.cancel();
      speaking = false;
      btnPlay.disabled = false;
      btnPause.disabled = true;
    }

    function speakCurrent(autonext) {
      stopSpeech();
      const s = slides[idx];
      if (!s.speech) return;
      const u = new SpeechSynthesisUtterance(s.speech);
      u.lang = "ru-RU";
      u.rate = rate;
      if (voice) u.voice = voice;
      u.onstart = () => {
        speaking = true;
        btnPlay.disabled = true;
        btnPause.disabled = false;
      };
      u.onend = () => {
        speaking = false;
        btnPlay.disabled = false;
        btnPause.disabled = true;
        if (autonext && idx < slides.length - 1) {
          showSlide(idx + 1);
          setTimeout(() => speakCurrent(true), 400);
        }
      };
      u.onerror = () => {
        speaking = false;
        btnPlay.disabled = false;
      };
      speechSynthesis.speak(u);
    }

    btnPlay.onclick = async () => {
      if (!voicesReady) voice = await loadVoices();
      speakCurrent(false);
    };
    btnPause.onclick = () => stopSpeech();
    btnPrev.onclick = () => {
      stopSpeech();
      showSlide(idx - 1);
    };
    btnNext.onclick = () => {
      stopSpeech();
      showSlide(idx + 1);
    };
    rateInput.oninput = () => {
      rate = parseFloat(rateInput.value) || 1;
    };

    const btnAll = document.createElement("button");
    btnAll.type = "button";
    btnAll.className = "btn btn-outline btn-sm cinema-all";
    btnAll.textContent = "▶▶ Весь урок";
    btnAll.onclick = async () => {
      if (!voicesReady) voice = await loadVoices();
      showSlide(0);
      speakCurrent(true);
    };
    el.querySelector(".cinema-controls").appendChild(btnAll);

    showSlide(0);
    loadVoices();
  }

  function initAll(root, renderRich) {
    root.querySelectorAll(".lesson-cinema").forEach((el) => initCinema(el, renderRich));
  }

  global.HartCinema = {
    bodyToSlides,
    factsToSlides,
    renderCinema,
    initAll,
    stripMd,
  };

  if (typeof speechSynthesis !== "undefined") {
    loadVoices();
  }
})(window);

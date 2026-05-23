let DATA = { categories: [], resources: [], meta: {} };
let activeCat = "all";
let query = "";

async function load() {
  const res = await fetch("/api/catalog");
  if (!res.ok) throw new Error("catalog: " + res.status);
  const payload = await res.json();
  DATA = payload.meta ? payload : { categories: payload.categories || [], resources: payload.resources || payload, meta: payload.meta || {} };
  const n = DATA.resources.length;
  const nc = DATA.resources.filter((r) => r.cat === "courses").length;
  document.getElementById("stat-total").textContent = n;
  document.getElementById("stat-courses").textContent = nc;
  document.getElementById("stat-cats").textContent = DATA.categories.length;
  const heroCount = document.getElementById("hero-count");
  if (heroCount) heroCount.textContent = n + "+";
  const tag = document.getElementById("hero-tagline");
  if (tag && DATA.meta?.tagline) tag.textContent = DATA.meta.tagline;
  renderChips();
  renderCategories();
  initCatalogSearch();
}

function t(key) {
  return window.HartI18n?.t?.(key) || key;
}

function priceLabel() {
  return window.HartRegion?.formatPrice?.() || "199 ₽";
}

function renderChips() {
  const el = document.getElementById("chips");
  el.innerHTML =
    `<button class="chip active" data-cat="all">${t("chip.all")}</button>` +
    DATA.categories
      .map(
        (c) =>
          `<button class="chip" data-cat="${c.id}">${c.icon} ${c.name}</button>`
      )
      .join("");
  el.querySelectorAll(".chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      el.querySelectorAll(".chip").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeCat = btn.dataset.cat;
      renderCategories();
    });
  });
}

function matchResource(r) {
  if (activeCat !== "all" && r.cat !== activeCat) return false;
  if (!query) return true;
  const blob = `${r.title} ${r.desc} ${r.about || ""} ${(r.tags || []).join(" ")} ${r.provider || ""}`.toLowerCase();
  return blob.includes(query);
}

function renderCategories() {
  const root = document.getElementById("catalog");
  if (!root) return;
  root.innerHTML = "";
  let filtered = DATA.resources.filter(matchResource);
  filtered = [...filtered].sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0));
  if (!filtered.length) {
    root.innerHTML = '<p class="empty">' + t("empty.search") + "</p>";
    return;
  }
  const cats =
    activeCat === "all"
      ? DATA.categories
      : DATA.categories.filter((c) => c.id === activeCat);
  for (const cat of cats) {
    const items = filtered.filter((r) => r.cat === cat.id);
    if (!items.length) continue;
    const block = document.createElement("section");
    block.className = "category-block";
    block.innerHTML = `
      <div class="cat-head">
        <h2>${cat.icon} ${cat.name} <span style="color:var(--muted);font-weight:400">(${items.length})</span></h2>
        <p class="cat-desc">${escapeHtml(cat.description)}</p>
      </div>
      <div class="grid" id="grid-${cat.id}"></div>
    `;
    root.appendChild(block);
    const grid = block.querySelector(".grid");
    for (const r of items) {
      const learn = (r.learn || []).slice(0, 2);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <span class="label-price">${r.featured ? "★ HART" : priceLabel()} · ${t("card.access")}</span>
        <div class="card-meta">
          <span>${escapeHtml(r.level || "")}</span>
          <span>${escapeHtml(r.duration || "")}</span>
          <span>${escapeHtml(r.provider || "")}</span>
        </div>
        <h3>${escapeHtml(r.title)}</h3>
        <p class="card-about">${escapeHtml((r.about || r.desc || "").split("\n")[0])}</p>
        ${learn.length ? `<ul class="learn-preview">${learn.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>` : ""}
        <div class="tags">${(r.tags || [])
          .slice(0, 4)
          .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
          .join("")}</div>
        <div class="card-actions">
          <a class="btn btn-outline" href="course.html?id=${encodeURIComponent(r.id)}">${t("card.more")}</a>
          <a class="btn btn-pay" href="pay.html?id=${encodeURIComponent(r.id)}&title=${encodeURIComponent(r.title)}">${t("card.buy")} · ${priceLabel()}</a>
        </div>
      `;
      grid.appendChild(card);
    }
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function initCatalogSearch() {
  const search = document.getElementById("search");
  if (!search || search.dataset.wired === "1") return;
  search.dataset.wired = "1";
  let debounce = null;
  search.addEventListener("input", (e) => {
    query = e.target.value.trim().toLowerCase();
    clearTimeout(debounce);
    debounce = setTimeout(renderCategories, 120);
  });
}

function showCatalogSkeleton() {
  const root = document.getElementById("catalog");
  if (!root) return;
  root.innerHTML =
    '<div class="catalog-loading" aria-busy="true">' +
    Array.from({ length: 6 }, () => '<div class="skeleton-card"></div>').join("") +
    "</div>";
}

function initScrollTop() {
  const btn = document.getElementById("scroll-top");
  if (!btn) return;
  const onScroll = () => {
    const show = window.scrollY > 400;
    btn.hidden = !show;
    btn.classList.toggle("visible", show);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  onScroll();
}

async function bootCatalog() {
  showCatalogSkeleton();
  await load();
  const sp = document.getElementById("stat-price");
  if (sp) sp.textContent = window.HartRegion?.formatPrice?.() || "199 ₽";
  if (window.HartI18n && !window.HartI18n.ready) {
    window.HartI18n.init()
      .then(() => {
        renderChips();
        renderCategories();
        if (sp) sp.textContent = window.HartRegion?.formatPrice?.() || "199 ₽";
      })
      .catch(() => {});
  }
}

function startCatalogPage() {
  bootCatalog().catch(() => {
    const root = document.getElementById("catalog");
    if (root) {
      root.innerHTML =
        '<p class="empty">Не удалось загрузить каталог. Запустите start-site.bat и обновите страницу (Ctrl+F5).</p>';
    }
  });
}

if (document.getElementById("catalog")) {
  const run = window.HartReady?.onReady || ((fn) => {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  });
  run(() => {
    initScrollTop();
    startCatalogPage();
  });
  window.addEventListener("hart:region", () => {
    const sp = document.getElementById("stat-price");
    if (sp) sp.textContent = window.HartRegion?.formatPrice?.() || "199 ₽";
    renderCategories();
  });
  window.addEventListener("hart:lang", () => {
    renderChips();
    renderCategories();
  });
}

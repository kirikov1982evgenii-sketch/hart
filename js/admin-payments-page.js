const api = (window.SITE_CONFIG?.paymentApiUrl || "http://127.0.0.1:8766").replace(/\/$/, "");

async function load() {
  const pin = document.getElementById("admin-pin").value;
  const msg = document.getElementById("admin-msg");
  const r = await fetch(api + "/api/pending", { headers: { "X-Admin-Pin": pin } });
  const data = await r.json();
  if (!data.ok) {
    msg.textContent = data.error || "Ошибка";
    msg.className = "form-msg err";
    return;
  }
  const list = document.getElementById("list");
  if (!data.claims.length) {
    list.innerHTML = '<p class="pay-hint">Нет заявок на проверке.</p>';
    return;
  }
  list.innerHTML = data.claims
    .map(
      (c) => `
        <div class="pay-box" style="margin-bottom:1rem">
          <p><b>${c.email}</b> · <code>${c.code}</code></p>
          <p>${(c.course_title || "").slice(0, 80)}</p>
          <p class="pay-hint">Чек: ${c.has_receipt ? "прикреплён" : "нет"} · ID: ${c.id}</p>
          <button class="btn-primary approve" data-id="${c.id}" style="margin-top:0.5rem;width:auto;padding:0.5rem 1rem">Подтвердить</button>
          <button class="btn-ghost reject" data-id="${c.id}" style="margin-left:0.5rem">Отклонить</button>
        </div>`
    )
    .join("");
  list.querySelectorAll(".approve").forEach((btn) => {
    btn.onclick = () => act(btn.dataset.id, "approve");
  });
  list.querySelectorAll(".reject").forEach((btn) => {
    btn.onclick = () => act(btn.dataset.id, "reject");
  });
}

async function act(id, kind) {
  const pin = document.getElementById("admin-pin").value;
  const msg = document.getElementById("admin-msg");
  const path = kind === "approve" ? "/api/approve" : "/api/reject";
  const r = await fetch(api + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Admin-Pin": pin },
    body: JSON.stringify({ claim_id: id }),
  });
  const data = await r.json();
  msg.textContent = data.ok ? "Готово" : data.error || "Ошибка";
  msg.className = data.ok ? "form-msg ok" : "form-msg err";
  if (data.ok) load();
}

document.getElementById("btn-load").onclick = load;

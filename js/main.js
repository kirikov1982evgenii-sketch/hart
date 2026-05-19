/** Вход, оплата 199 ₽, затем каталог. */
let currentProfile = null;

function $(id) {
  return document.getElementById(id);
}

function show(el, on) {
  if (el) el.classList.toggle("hidden", !on);
}

function setMsg(id, text, ok) {
  const el = $(id);
  if (!el) return;
  el.textContent = text;
  el.className = ok ? "form-msg ok" : "form-msg err";
}

async function refreshUI() {
  const gate = $("gate");
  const paid = $("paid-content");
  const userBar = $("user-bar");
  let session;
  try {
    session = await MarketAuth.getSession();
  } catch (e) {
    $("config-warn").classList.remove("hidden");
    $("config-warn").textContent =
      "⚠️ Создайте config.js из config.example.js и подключите Supabase (см. НАСТРОЙКА-ВХОД.md).";
    show(gate, true);
    show(paid, false);
    return;
  }

  if (!session) {
    currentProfile = null;
    show(gate, true);
    show(paid, false);
    show(userBar, false);
    return;
  }

  currentProfile = await MarketAuth.getProfile();
  const email = session.user.email || session.user.phone || "аккаунт";
  $("user-email").textContent = email;
  show(userBar, true);

  if (MarketPay.hasAccess(currentProfile)) {
    show(gate, false);
    show(paid, true);
    if (!window.__catalogLoaded) {
      window.__catalogLoaded = true;
      await loadCatalog();
    }
    return;
  }

  show(gate, true);
  show(paid, false);
  $("pay-wall").innerHTML = MarketPay.paymentBlock(currentProfile);
  const btn = $("btn-paid");
  if (btn) {
    btn.onclick = async () => {
      try {
        await MarketAuth.markPaymentPending();
        setMsg("pay-msg", "Спасибо! Проверим перевод и откроем доступ.", true);
        await refreshUI();
      } catch (err) {
        setMsg("pay-msg", err.message, false);
      }
    };
  }
}

function switchTab(tab) {
  document.querySelectorAll(".auth-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.tab === tab);
  });
  document.querySelectorAll(".auth-panel").forEach((p) => {
    p.classList.toggle("hidden", p.dataset.panel !== tab);
  });
}

function wireAuth() {
  switchTab("login");

  document.querySelectorAll(".auth-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  $("form-login")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    setMsg("login-msg", "Вход…", true);
    try {
      await MarketAuth.signInEmail(
        $("login-email").value.trim(),
        $("login-pass").value
      );
      setMsg("login-msg", "Готово", true);
      await refreshUI();
    } catch (err) {
      setMsg("login-msg", err.message, false);
    }
  });

  $("form-register")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const p1 = $("reg-pass").value;
    const p2 = $("reg-pass2").value;
    if (p1 !== p2) {
      setMsg("reg-msg", "Пароли не совпадают", false);
      return;
    }
    if (p1.length < 6) {
      setMsg("reg-msg", "Пароль минимум 6 символов", false);
      return;
    }
    setMsg("reg-msg", "Регистрация…", true);
    try {
      await MarketAuth.signUpEmail(
        $("reg-email").value.trim(),
        p1,
        $("reg-phone").value.trim()
      );
      setMsg(
        "reg-msg",
        "Письмо с подтверждением отправлено на почту. После клика по ссылке войдите.",
        true
      );
    } catch (err) {
      setMsg("reg-msg", err.message, false);
    }
  });

  $("form-magic")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    setMsg("magic-msg", "Отправляем ссылку…", true);
    try {
      await MarketAuth.signInMagicLink($("magic-email").value.trim());
      setMsg("magic-msg", "Ссылка для входа отправлена на почту.", true);
    } catch (err) {
      setMsg("magic-msg", err.message, false);
    }
  });

  $("form-phone")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const phone = $("phone-num").value.trim();
    setMsg("phone-msg", "Отправляем SMS…", true);
    try {
      await MarketAuth.signInPhoneOtp(phone);
      $("phone-step2").classList.remove("hidden");
      $("phone-verify")?.addEventListener("click", async () => {
        try {
          await MarketAuth.verifyPhoneOtp(phone, $("phone-code").value.trim());
          setMsg("phone-msg", "Вход выполнен", true);
          await refreshUI();
        } catch (err) {
          setMsg("phone-msg", err.message, false);
        }
      });
    } catch (err) {
      setMsg(
        "phone-msg",
        err.message + " (SMS: включите Phone в Supabase + Twilio trial)",
        false
      );
    }
  });

  $("btn-logout")?.addEventListener("click", async () => {
    await MarketAuth.signOut();
    window.__catalogLoaded = false;
    await refreshUI();
  });
}

async function loadCatalog() {
  if (typeof load === "function") await load();
}

document.addEventListener("DOMContentLoaded", () => {
  wireAuth();
  MarketAuth.onAuthChange(() => refreshUI());
  refreshUI();
});

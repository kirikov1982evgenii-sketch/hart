document.addEventListener("DOMContentLoaded", async () => {
  if (window.HartI18n && !window.HartI18n.ready) await window.HartI18n.init();
  const c = window.SITE_CONFIG || {};
  const em = c.supportEmail || "freelancerwok@mail.ru";
  const mail = document.getElementById("support-mail");
  if (mail) {
    mail.href = "mailto:" + em;
    mail.textContent = em;
  }
  const tg = document.getElementById("support-tg");
  if (tg) {
    tg.href = c.telegramBot || "https://t.me/uportbot";
    tg.textContent = c.telegramBotName || "@uportbot";
  }
});

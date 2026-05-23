/** Оплата 199 ₽ — перевод на карту. */
(function (global) {
  const cfg = () => global.SITE_CONFIG || {};

  function price() {
    return cfg().accessPrice || cfg().priceRub || 199;
  }

  function formatCard(num) {
    const d = String(num || cfg().payCard || "").replace(/\D/g, "");
    return d.replace(/(\d{4})(?=\d)/g, "$1 ").trim() || d;
  }

  function paymentBlock(profile) {
    const c = cfg();
    const code = profile?.payment_code || "PAY-XXXXXXXX";
    const p = price();
    const pending =
      profile?.payment_status === "pending"
        ? '<p class="pay-pending">⏳ Ожидаем подтверждение перевода (обычно до 24 ч).</p>'
        : "";
    return `
      <div class="pay-box">
        <h2>Доступ к каталогу — <span class="price">${p} ₽</span></h2>
        <p>Один раз. Все программы каталога, поиск и фильтры.</p>
        <div class="pay-details">
          <p><b>Банк:</b> ${c.payBank || "Т-Банк"}</p>
          <p><b>Номер карты:</b> <code>${formatCard(c.payCard)}</code></p>
          ${c.payName ? `<p><b>Получатель:</b> ${c.payName}</p>` : ""}
          <p><b>Сумма:</b> <code>${p} ₽</code></p>
          <p><b>Комментарий к переводу:</b> <code>${code}</code></p>
        </div>
        <p class="pay-hint">Укажите код <code>${code}</code> в комментарии — так мы быстрее подтвердим оплату.</p>
        <button type="button" class="btn-primary" id="btn-paid">Я оплатил ${p} ₽</button>
        <p id="pay-msg" class="pay-msg"></p>
        ${pending}
      </div>
    `;
  }

  function hasAccess(profile) {
    return profile && (profile.paid === true || profile.payment_status === "paid");
  }

  global.MarketPay = { price, paymentBlock, hasAccess };
})(window);

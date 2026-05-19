/** Регион оплаты: РФ/СНГ 199 ₽ или мир $4.99 */
(function (global) {
  const cfg = () => global.SITE_CONFIG || {};

  function pricing() {
    const region = global.HartI18n?.getRegion?.() || "intl";
    if (region === "ru") {
      return {
        region: "ru",
        amount: cfg().priceRub || 199,
        currency: "RUB",
        symbol: "₽",
        label: global.HartI18n?.t?.("region.ru") || "199 ₽",
      };
    }
    return {
      region: "intl",
      amount: cfg().priceUsd || 4.99,
      currency: "USD",
      symbol: "$",
      label: global.HartI18n?.t?.("region.intl") || "$4.99",
    };
  }

  function formatPrice() {
    const p = pricing();
    if (p.region === "ru") return `${p.amount} ${p.symbol}`;
    return `${p.symbol}${p.amount}`;
  }

  global.HartRegion = { pricing, formatPrice };
})(window);

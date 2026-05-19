/** Регистрация и вход: Supabase Auth (бесплатный тариф). */
(function (global) {
  const cfg = () => global.SITE_CONFIG || {};
  let sb = null;

  function client() {
    if (!sb) {
      const c = cfg();
      if (!c.supabaseUrl || !c.supabaseAnonKey || c.supabaseUrl.includes("ВАШ")) {
        throw new Error("Настройте config.js (скопируйте из config.example.js)");
      }
      sb = global.supabase.createClient(c.supabaseUrl, c.supabaseAnonKey);
    }
    return sb;
  }

  async function getSession() {
    const { data } = await client().auth.getSession();
    return data.session;
  }

  async function getProfile() {
    const session = await getSession();
    if (!session) return null;
    const { data, error } = await client()
      .from("profiles")
      .select("*")
      .eq("id", session.user.id)
      .maybeSingle();
    if (error) throw error;
    return data;
  }

  async function signUpEmail(email, password, phone) {
    const { data, error } = await client().auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: window.location.origin + window.location.pathname,
        data: { phone: phone || "" },
      },
    });
    if (error) throw error;
    if (phone && data.user) {
      await client()
        .from("profiles")
        .update({ phone, updated_at: new Date().toISOString() })
        .eq("id", data.user.id);
    }
    return data;
  }

  async function signInEmail(email, password) {
    const { data, error } = await client().auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  }

  async function signInMagicLink(email) {
    const { data, error } = await client().auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin + window.location.pathname },
    });
    if (error) throw error;
    return data;
  }

  async function signInPhoneOtp(phone) {
    const { data, error } = await client().auth.signInWithOtp({ phone });
    if (error) throw error;
    return data;
  }

  async function verifyPhoneOtp(phone, token) {
    const { data, error } = await client().auth.verifyOtp({
      phone,
      token,
      type: "sms",
    });
    if (error) throw error;
    return data;
  }

  async function signOut() {
    await client().auth.signOut();
  }

  async function markPaymentPending() {
    const session = await getSession();
    if (!session) throw new Error("Войдите в аккаунт");
    const { error } = await client()
      .from("profiles")
      .update({
        payment_status: "pending",
        updated_at: new Date().toISOString(),
      })
      .eq("id", session.user.id);
    if (error) throw error;
  }

  async function onAuthChange(cb) {
    client().auth.onAuthStateChange((_event, session) => cb(session));
  }

  global.MarketAuth = {
    client,
    getSession,
    getProfile,
    signUpEmail,
    signInEmail,
    signInMagicLink,
    signInPhoneOtp,
    verifyPhoneOtp,
    signOut,
    markPaymentPending,
    onAuthChange,
  };
})(window);

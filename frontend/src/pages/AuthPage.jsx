import { useEffect, useState } from "react";
import { ArrowLeft, Leaf, LockKeyhole, Mail, UserRound } from "lucide-react";
import api, { TOKEN_KEY } from "../services/api";

export default function AuthPage({ onAuthenticated }) {
  const resetToken = new URLSearchParams(window.location.search).get("reset_token") || "";
  const [mode, setMode] = useState(resetToken ? "reset" : "login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (resetToken) window.history.replaceState({}, "", window.location.pathname);
  }, [resetToken]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (mode === "register" && password !== confirmation) {
      setError("Your passwords do not match.");
      return;
    }
    if (mode === "reset" && password !== confirmation) {
      setError("Your passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "forgot") {
        const result = await api.post("/api/auth/forgot-password", { email });
        setMessage(result.message);
        return;
      }
      if (mode === "reset") {
        const result = await api.post("/api/auth/reset-password", { token: resetToken, new_password: password });
        setMessage(result.message);
        window.history.replaceState({}, "", window.location.pathname);
        setMode("login");
        setPassword("");
        setConfirmation("");
        return;
      }

      const endpoint = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const body = mode === "register" ? { full_name: fullName, email, password } : { email, password };
      const session = await api.post(endpoint, body);
      localStorage.setItem(TOKEN_KEY, session.access_token);
      onAuthenticated(session.user);
    } catch (requestError) {
      setError(requestError.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function changeMode(nextMode) {
    setMode(nextMode);
    setError("");
    setMessage("");
    setPassword("");
    setConfirmation("");
  }

  const isRegistration = mode === "register";
  const title = mode === "forgot" ? "Reset your password" : mode === "reset" ? "Choose a new password" : isRegistration ? "Create your account" : "Welcome back";
  const description = mode === "forgot"
    ? "We’ll send a secure reset link if an account matches your email."
    : mode === "reset" ? "Choose a strong password to secure your account."
      : isRegistration ? "Start building healthier habits, one step at a time." : "Sign in to continue your health journey.";

  return (
    <main className="journey-auth-page">
      <section className="journey-auth-brand">
        <div className="journey-auth-logo"><span><Leaf size={24} /></span><div><strong>NutriPath</strong><small>HEALTHIER EVERY DAY</small></div></div>
        <div className="journey-auth-pitch">
          <span className="tracker-eyebrow">A HEALTHIER YOU, AT YOUR PACE</span>
          <h1>Your journey.<br />Your way forward.</h1>
          <p>Build a thoughtful plan around your life, and celebrate progress that feels right for you.</p>
        </div>
        <div className="journey-auth-note"><span>✦</span><p>Real progress is personal. We’ll help you make a plan that respects yours.</p></div>
      </section>

      <section className="journey-auth-main">
        <form className="journey-auth-card" onSubmit={submit}>
          <div className="journey-auth-mobile-logo"><Leaf size={21} /> NutriPath</div>
          {mode !== "login" && mode !== "register" && <button className="journey-auth-back" type="button" onClick={() => changeMode("login")}><ArrowLeft size={15} /> Back to sign in</button>}
          <span className="tracker-eyebrow">{isRegistration ? "GET STARTED" : mode === "login" ? "YOUR HEALTH SPACE" : "ACCOUNT SUPPORT"}</span>
          <h2>{title}</h2>
          <p className="journey-auth-description">{description}</p>

          {isRegistration && <label className="journey-auth-field"><span>Full name</span><div><UserRound size={17} /><input autoComplete="name" value={fullName} onChange={event => setFullName(event.target.value)} minLength="2" maxLength="120" placeholder="Your name" required /></div></label>}
          {mode !== "reset" && <label className="journey-auth-field"><span>Email address</span><div><Mail size={17} /><input type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} maxLength="320" placeholder="you@example.com" required /></div></label>}
          {mode !== "forgot" && <label className="journey-auth-field"><span>{mode === "reset" ? "New password" : "Password"}</span><div><LockKeyhole size={17} /><input type="password" autoComplete={isRegistration || mode === "reset" ? "new-password" : "current-password"} value={password} onChange={event => setPassword(event.target.value)} minLength="10" maxLength="128" placeholder="At least 10 characters" required /></div><small>Use at least 10 characters.</small></label>}
          {(isRegistration || mode === "reset") && <label className="journey-auth-field"><span>Confirm password</span><div><LockKeyhole size={17} /><input type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} minLength="10" maxLength="128" placeholder="Enter your password again" required /></div></label>}
          {mode === "login" && <button type="button" className="journey-auth-forgot" onClick={() => changeMode("forgot")}>Forgot password?</button>}
          {error && <p className="journey-auth-error" role="alert">{error}</p>}
          {message && <p className="journey-auth-success" role="status">{message}</p>}
          <button type="submit" className="journey-auth-submit" disabled={loading}>{loading ? "Please wait…" : mode === "register" ? "Create account" : mode === "forgot" ? "Send reset link" : mode === "reset" ? "Update password" : "Sign in"}</button>
          {mode === "login" || mode === "register" ? <p className="journey-auth-switch">{isRegistration ? "Already have an account?" : "New to NutriPath?"}<button type="button" onClick={() => changeMode(isRegistration ? "login" : "register")}>{isRegistration ? "Sign in" : "Create account"}</button></p> : null}
          <p className="journey-auth-privacy">Your health information is private to your account.</p>
        </form>
      </section>
    </main>
  );
}

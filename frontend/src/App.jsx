
import { useEffect, useState } from "react";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import MealPlanner from "./pages/MealPlanner";
import WeightJourney from "./pages/WeightJourney";
import HealthCoach from "./pages/HealthCoach";
import DailyMealTracker from "./features/daily-meals/DailyMealTracker";
import AuthPage from "./pages/AuthPage";
import Onboarding from "./pages/Onboarding";
import WelcomePage from "./pages/WelcomePage";
import api, { TOKEN_KEY } from "./services/api";

export default function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [user, setUser] = useState(null);
  const [journey, setJourney] = useState("checking");
  const [authMode, setAuthMode] = useState("login");
  const [startupMessage, setStartupMessage] = useState("");

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setJourney(new URLSearchParams(window.location.search).has("reset_token") ? "auth" : "welcome");
      return () => { active = false; };
    }

    api.get("/api/auth/me")
      .then(authenticatedUser => {
        if (!active) return;
        setUser(authenticatedUser);
        setJourney(authenticatedUser.onboarding_completed ? "app" : "onboarding");
      })
      .catch(error => {
        if (!active) return;
        if (error.status === 401) localStorage.removeItem(TOKEN_KEY);
        else setStartupMessage(error.message);
        setJourney("auth");
      });

    return () => { active = false; };
  }, []);

  function onAuthenticated(authenticatedUser) {
    setStartupMessage("");
    setUser(authenticatedUser);
    setJourney(authenticatedUser.onboarding_completed ? "app" : "onboarding");
  }

  function openAuth(mode) {
    setAuthMode(mode);
    setJourney("auth");
  }

  function onOnboardingComplete(profile) {
    setUser(profile.user);
    setJourney("app");
    setActivePage("Dashboard");
  }

  async function logout() {
    try {
      await api.post("/api/auth/logout", {});
    } catch (error) {
      if (error.status !== 401) setStartupMessage(error.message);
    } finally {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
      setJourney("welcome");
      setActivePage("Dashboard");
    }
  }

  const pages = {
    Dashboard: <Dashboard user={user} setActivePage={setActivePage} />,
    "Daily Meal Tracker": <DailyMealTracker userId={user?.id} />,
    "Meal Planner": <MealPlanner userId={user?.id} setActivePage={setActivePage} />,
    "Weight Journey": <WeightJourney user={user} onUserUpdate={setUser} />,
    "Health Coach": <HealthCoach user={user} setActivePage={setActivePage} />
  };

  if (journey === "checking") return <div className="tracker-loading" role="status">Preparing your NutriPath space…</div>;
  if (journey === "welcome") return <WelcomePage onGetStarted={() => openAuth("register")} onSignIn={() => openAuth("login")} />;
  if (journey === "auth") return <><AuthPage initialMode={authMode} onAuthenticated={onAuthenticated} />{startupMessage && <p className="journey-startup-message" role="alert">{startupMessage}</p>}</>;
  if (journey === "onboarding") return <Onboarding user={user} onComplete={onOnboardingComplete} onLogout={logout} />;

  return (
    <Layout
      activePage={activePage}
      setActivePage={setActivePage}
      onLogout={logout}
      user={user}
    >
      {pages[activePage]}
    </Layout>
  );
}

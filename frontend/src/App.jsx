
import { useState } from "react";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import MealPlanner from "./pages/MealPlanner";
import WeightJourney from "./pages/WeightJourney";
import HealthCoach from "./pages/HealthCoach";

export default function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const pages = {
    Dashboard: <Dashboard />,
    "Meal Planner": <MealPlanner />,
    "Weight Journey": <WeightJourney />,
    "Health Coach": <HealthCoach />
  };

  return (
    <Layout
      activePage={activePage}
      setActivePage={setActivePage}
    >
      {pages[activePage]}
    </Layout>
  );
}

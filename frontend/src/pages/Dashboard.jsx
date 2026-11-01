
import {
  Flame, Weight, Droplets, Footprints,
  Sparkles, Clock, ArrowUpRight
} from "lucide-react";
import StatCard from "../components/StatCard";

const meals = [
  { time: "08:30 AM", name: "Breakfast", detail: "Oats, banana and milk", calories: 320, emoji: "🥣" },
  { time: "01:00 PM", name: "Lunch", detail: "Rice, vegetables and dal", calories: 450, emoji: "🥗" },
  { time: "04:30 PM", name: "Evening snack", detail: "Apple and almonds", calories: 180, emoji: "🍎" }
];

export default function Dashboard() {
  return (
    <>
      <div className="welcome-row">
        <div>
          <span className="eyebrow">YOUR PERSONAL HEALTH SPACE</span>
          <h1>Good morning! <span>🌿</span></h1>
          <p>Every healthy choice brings you closer to your goals.</p>
        </div>
        <div className="date-pill">November 2026</div>
      </div>

      <section className="hero-banner">
        <div>
          <span className="hero-tag">
            <Sparkles size={14} /> YOUR DAILY MOTIVATION
          </span>
          <h2>Healthy habits.<br />Happier you.</h2>
          <p>Consistency matters more than perfection. Keep moving forward!</p>
          <button className="primary-button"
            onClick={() => window.scrollTo({ top: 500, behavior: "smooth" })}>
            Explore your progress <ArrowUpRight size={17} />
          </button>
        </div>
        <div className="hero-art">🥑</div>
      </section>

      <div className="section-heading">
        <div>
          <h2>Your daily overview</h2>
          <p>Here is how your health journey is progressing.</p>
        </div>
        <span className="today-label">TODAY</span>
      </div>

      <div className="stats-grid">
        <StatCard title="Calories consumed" value="950" unit="kcal"
          note="Daily goal: 1,800 kcal" icon={Flame}
          color="orange" progress={53} />
        <StatCard title="Current weight" value="65.4" unit="kg"
          note="Sample target: 60 kg" icon={Weight} color="green" />
        <StatCard title="Water intake" value="1.5" unit="L"
          note="Daily goal: 2.5 litres" icon={Droplets}
          color="blue" progress={60} />
        <StatCard title="Steps walked" value="4,250" unit="steps"
          note="Daily goal: 8,000 steps" icon={Footprints}
          color="purple" progress={53} />
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>Today's food journal</h3>
              <p>Your recorded meals and nutrition</p>
            </div>
            <span className="today-label">3 MEALS</span>
          </div>

          <div className="meal-list">
            {meals.map(meal => (
              <div className="meal-row" key={meal.name}>
                <div className="food-emoji">{meal.emoji}</div>
                <div className="meal-info">
                  <strong>{meal.name}</strong>
                  <span>{meal.detail}</span>
                  <small><Clock size={12} /> {meal.time}</small>
                </div>
                <strong className="meal-calories">{meal.calories} kcal</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel goal-panel">
          <div className="panel-heading">
            <div>
              <h3>Daily calorie goal</h3>
              <p>Your nutrition progress</p>
            </div>
            <Flame className="orange-text" />
          </div>

          <div className="calorie-circle">
            <div>
              <strong>950</strong>
              <span>of 1,800 kcal</span>
            </div>
          </div>

          <div className="calorie-remaining">
            <strong>850 kcal</strong>
            <span>Remaining today</span>
          </div>
        </section>
      </div>

      <section className="recommendation">
        <Sparkles size={24} />
        <div>
          <strong>Your NutriPath tip of the day</strong>
          <p>Include a variety of vegetables and fruits in your meals for balanced nutrition.</p>
        </div>
      </section>
    </>
  );
}

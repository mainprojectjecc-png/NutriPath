
import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight, CalendarDays, Clock, Droplets, Flame, Footprints,
  Scale, Sparkles, Target, TrendingDown, Weight
} from "lucide-react";
import api from "../services/api";
import { getNutritionData } from "../services/nutrition";

function todayKey() {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
}

function buildInsight(meals, totals, goal, water) {
  if (!meals.length) return "Your nutrition insights will appear as you add meals to your food journal.";
  if (totals.protein < 40) return `You’ve logged ${Math.round(totals.protein)}g of protein today. Consider a protein-rich choice such as dal, paneer, tofu or curd.`;
  if (goal && totals.calories > goal.calorieGoal) return `You’re ${Math.round(totals.calories - goal.calorieGoal)} kcal above your daily goal. Your food journal is a guide, not a judgment.`;
  if (water < goal?.waterGoal) return `You’ve logged ${Math.round(water)} ml of water. Keep your water tracker up to date to follow your hydration.`;
  return `Your log includes ${Math.round(totals.protein)}g protein and ${Math.round(totals.carbs)}g carbohydrates. Keep tracking consistently to see your personal patterns.`;
}

function DashboardWeightChart({ journey }) {
  if (!journey) return <p className="dashboard-not-logged">Your weight chart will appear once your journey loads.</p>;
  const records = [
    { weight_kg: journey.goal.starting_weight_kg, measured_on: journey.goal.start_date, id: "start" },
    ...journey.weight_history
  ].sort((a, b) => a.measured_on.localeCompare(b.measured_on) || (a.id === "start" ? -1 : b.id === "start" ? 1 : a.id - b.id));
  const allWeights = [...records.map(point => point.weight_kg), journey.goal.target_weight_kg];
  const min = Math.min(...allWeights);
  const max = Math.max(...allWeights);
  const padding = Math.max((max - min) * .18, 1);
  const upper = max + padding;
  const range = max - min + padding * 2 || 1;
  const points = records.map((point, index) => ({
    ...point,
    x: records.length === 1 ? 300 : 25 + index / (records.length - 1) * 550,
    y: 18 + (upper - point.weight_kg) / range * 132
  }));
  const targetY = 18 + (upper - journey.goal.target_weight_kg) / range * 132;
  const path = points.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" ");

  return <div className="dashboard-weight-chart-wrap">
    <svg viewBox="0 0 600 180" role="img" aria-label="Recorded weight trend with starting weight and target">
      {[0, 1, 2].map(index => <line key={index} x1="20" x2="580" y1={28 + index * 54} y2={28 + index * 54} stroke="#edf2ee" strokeDasharray="3 5" />)}
      <line x1="20" x2="580" y1={targetY} y2={targetY} stroke="#e5a84c" strokeDasharray="5 5" />
      <text x="575" y={Math.max(14, targetY - 5)} textAnchor="end" fill="#bc8432" fontSize="10">Target {journey.goal.target_weight_kg} kg</text>
      {points.length > 1 && <path d={path} fill="none" stroke="#16845c" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
      {points.map((point, index) => <g key={point.id}><circle cx={point.x} cy={point.y} r="4" fill={point.id === "start" ? "#fff" : "#16845c"} stroke="#16845c" strokeWidth="2"><title>{point.id === "start" ? "Starting" : index === points.length - 1 ? "Current and recorded" : "Recorded"} weight: {point.weight_kg} kg</title></circle>{index === 0 || index === points.length - 1 ? <text x={point.x} y={Math.min(172, point.y + 18)} textAnchor={index === 0 ? "start" : "end"} fill="#73877a" fontSize="9">{point.id === "start" ? "Start" : new Date(`${point.measured_on}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text> : null}</g>)}
    </svg>
    <div className="dashboard-weight-chart-legend"><span><i /> Starting / recorded weight</span><span><i className="dashboard-target-line" /> Target</span></div>
  </div>;
}

export default function Dashboard({ user, setActivePage }) {
  const [journey, setJourney] = useState(null);
  const [mealData, setMealData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getNutritionData(user.id)
      .then(data => { if (active) setMealData(data); })
      .catch(loadError => { if (active) setError(loadError.message || "Your food journal could not be loaded."); });
    api.get("/api/journey")
      .then(data => { if (active) setJourney(data); })
      .catch(loadError => { if (active) setError(loadError.message || "Your journey summary could not be loaded."); });
    return () => { active = false; };
  }, [user.id]);

  const date = todayKey();
  const meals = useMemo(() => mealData?.meals.filter(meal => meal.date === date) || [], [mealData, date]);
  const totals = useMemo(() => meals.reduce((sum, meal) => ({
    calories: sum.calories + meal.calories,
    protein: sum.protein + meal.protein,
    carbs: sum.carbs + meal.carbs,
    fats: sum.fats + meal.fats
  }), { calories: 0, protein: 0, carbs: 0, fats: 0 }), [meals]);
  const water = mealData?.waterByDate[date] || 0;
  const calorieGoal = mealData?.calorieGoal || 2000;
  const waterGoal = mealData?.waterGoal || 2500;
  const firstName = user.full_name.split(" ")[0] || "there";
  const mealCount = new Set(meals.map(meal => meal.mealType)).size;

  return <>
    <div className="welcome-row">
      <div><span className="eyebrow">YOUR PERSONAL HEALTH SPACE</span><h1>Welcome back, {firstName} <span>🌿</span></h1><p>Your journey is yours. Let’s see how you’re doing today.</p></div>
      <div className="date-pill"><CalendarDays size={15} />{new Date().toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</div>
    </div>

    {journey && <section className="dashboard-journey-banner">
      <div className="dashboard-journey-copy"><span><Sparkles size={14} /> YOUR WEIGHT JOURNEY</span><h2>{journey.goal.journey_progress_percent}% of your goal, one day at a time.</h2><p>{journey.goal.current_weight_kg} kg now · {journey.goal.target_weight_kg} kg target · {journey.goal.remaining_weight_kg} kg to go</p><div className="dashboard-journey-track"><i style={{ width: `${journey.goal.journey_progress_percent}%` }} /></div><button type="button" onClick={() => setActivePage("Weight Journey")}>View my journey <ArrowUpRight size={15} /></button></div>
      <div className="dashboard-journey-ring" style={{ "--progress": `${journey.goal.journey_progress_percent * 3.6}deg` }}><strong>{journey.goal.journey_progress_percent}%</strong></div>
    </section>}

    {error && <p className="dashboard-data-error" role="alert">{error}</p>}

    <div className="section-heading"><div><h2>Your daily overview</h2><p>A snapshot of your logged nutrition and journey.</p></div><span className="today-label">TODAY</span></div>
    <div className="stats-grid">
      <div className="stat-card"><div className="stat-top"><div><p className="muted">Calories consumed</p><h2>{Math.round(totals.calories).toLocaleString()} <small>kcal</small></h2></div><div className="stat-icon orange"><Flame /></div></div><div className="progress-track"><div className="progress-fill orange" style={{ width: `${Math.min(totals.calories / calorieGoal * 100, 100)}%` }} /></div><span className="stat-note">{calorieGoal.toLocaleString()} kcal daily goal</span></div>
      <div className="stat-card"><div className="stat-top"><div><p className="muted">Current weight</p><h2>{journey ? journey.goal.current_weight_kg : "—"} <small>kg</small></h2></div><div className="stat-icon green"><Weight /></div></div><span className="stat-note">{journey ? `Target ${journey.goal.target_weight_kg} kg` : "Your journey profile"}</span><button className="dashboard-card-link" type="button" onClick={() => setActivePage("Weight Journey")}>View weight journey <ArrowUpRight size={13} /></button></div>
      <div className="stat-card"><div className="stat-top"><div><p className="muted">Water intake</p><h2>{(water / 1000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "")} <small>L</small></h2></div><div className="stat-icon blue"><Droplets /></div></div><div className="progress-track"><div className="progress-fill blue" style={{ width: `${Math.min(water / waterGoal * 100, 100)}%` }} /></div><span className="stat-note">{(waterGoal / 1000).toFixed(1)} L daily goal</span></div>
      <div className="stat-card"><div className="stat-top"><div><p className="muted">Exercise</p><h2 className="dashboard-exercise-title">Not logged</h2></div><div className="stat-icon purple"><Footprints /></div></div><span className="stat-note">{journey?.profile.exercise_preferences ? `Preference: ${journey.profile.exercise_preferences}` : "No exercise entries recorded"}</span></div>
    </div>

    <div className="dashboard-grid dashboard-meal-summary-grid">
      <section className="panel"><div className="panel-heading"><div><h3>Today’s food journal</h3><p>Your actual logged meals and nutrition</p></div><span className="today-label">{mealCount} {mealCount === 1 ? "MEAL" : "MEALS"}</span></div>
        {meals.length ? <div className="meal-list">{meals.slice(-5).reverse().map(meal => <div className="meal-row" key={meal.id}><div className="food-emoji">{meal.emoji}</div><div className="meal-info"><strong>{meal.foodName}</strong><span>{meal.mealType} · {meal.quantity} × {meal.servingLabel}</span><small><Clock size={12} /> Logged today</small></div><strong className="meal-calories">{Math.round(meal.calories)} kcal</strong></div>)}</div> : <div className="dashboard-empty-log"><span>🥗</span><p>No meals logged today yet.</p><button type="button" onClick={() => setActivePage("Daily Meal Tracker")}>Open food journal <ArrowUpRight size={14} /></button></div>}
        <div className="dashboard-macro-summary"><span><strong>{Math.round(totals.protein)}g</strong> protein</span><span><strong>{Math.round(totals.carbs)}g</strong> carbs</span><span><strong>{Math.round(totals.fats)}g</strong> fats</span></div>
      </section>
      <section className="panel goal-panel"><div className="panel-heading"><div><h3>Daily calorie goal</h3><p>From your meal tracker entries</p></div><Flame className="orange-text" /></div><div className="calorie-circle" style={{ background: `conic-gradient(#16845c ${Math.min(totals.calories / calorieGoal * 360, 360)}deg, #e9f2e9 0deg)` }}><div><strong>{Math.round(totals.calories)}</strong><span>of {calorieGoal.toLocaleString()} kcal</span></div></div><div className="calorie-remaining"><strong>{Math.max(0, calorieGoal - Math.round(totals.calories))} kcal</strong><span>remaining today</span></div><button className="dashboard-card-link dashboard-center-link" type="button" onClick={() => setActivePage("Daily Meal Tracker")}>Update food journal <ArrowUpRight size={13} /></button></section>
    </div>

    <div className="dashboard-grid dashboard-weight-row">
      <section className="panel"><div className="panel-heading"><div><h3>Weight progress</h3><p>Starting, recorded and target weight</p></div><Scale className="orange-text" /></div><DashboardWeightChart journey={journey} /></section>
      <section className="panel"><div className="panel-heading"><div><h3>Your journey milestones</h3><p>Achievements from recorded progress</p></div><Target className="orange-text" /></div>{journey?.achievements.length ? <div className="dashboard-milestones">{journey.achievements.slice(-3).reverse().map(item => <div key={item.code}><span><TrendingDown size={15} /></span><div><strong>{item.title}</strong><small>{item.description}</small></div><CheckIcon /></div>)}</div> : <p className="dashboard-not-logged">Your first milestone will appear when you begin recording progress.</p>}<button className="dashboard-card-link" type="button" onClick={() => setActivePage("Weight Journey")}>View all milestones <ArrowUpRight size={13} /></button></section>
    </div>
    <section className="panel dashboard-insight dashboard-insight-full"><div className="panel-heading"><div><h3>Nutrition insights</h3><p>Based on your logged data</p></div><Sparkles className="orange-text" /></div><p>{buildInsight(meals, totals, { calorieGoal, waterGoal }, water)}</p><small>Rule-based observation of today’s logged food · Not medical advice</small></section>
  </>;
}

function CheckIcon() {
  return <span className="dashboard-milestone-check">✓</span>;
}

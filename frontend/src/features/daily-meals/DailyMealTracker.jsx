import { useEffect, useMemo, useState } from "react";
import { Activity, CalendarDays, ChevronLeft, ChevronRight, Droplets, Flame, Plus, Sparkles, Target, Trash2 } from "lucide-react";
import MealFoodModal from "./MealFoodModal";
import MealHistoryCalendar from "./MealHistoryCalendar";
import NutritionChart from "./NutritionChart";
import { mealTypes } from "./foodCatalog";
import {
  addFoodEntry,
  addWaterEntry,
  getNutritionData,
  removeFoodEntry,
  saveNutritionSettings
} from "../../services/nutrition";

function dateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function shiftDate(value, amount) {
  const date = new Date(`${value}T12:00:00`);
  date.setDate(date.getDate() + amount);
  return dateKey(date);
}

function formatNutrient(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function getInsight(totals, calorieGoal, meals, selectedDate) {
  const dayMeals = meals.filter(meal => meal.date === selectedDate);
  if (!dayMeals.length) return "Start by logging a meal. Your personalized nutrition insights will appear here as your food journal fills in.";
  if (totals.calories > calorieGoal) return `You’re ${Math.round(totals.calories - calorieGoal)} kcal over your daily goal so far. A gentle walk and a balanced next meal can help you stay on track.`;
  if (totals.protein < 40) return `You’ve logged ${Math.round(totals.protein)}g of protein so far. Add dal, paneer, curd, tofu or eggs to a meal to support your daily protein intake.`;
  if (totals.fats > 70) return `Your logged fats are at ${Math.round(totals.fats)}g. Consider a lighter cooking method or a fruit-and-curd snack for your next choice.`;
  if (totals.calories < calorieGoal * 0.45) return `You’ve logged ${Math.round(totals.calories)} of ${calorieGoal} kcal. Keep logging meals through the day for a clearer picture of your nutrition.`;
  return `A balanced day so far: ${Math.round(totals.protein)}g protein, ${Math.round(totals.carbs)}g carbs and ${Math.round(totals.fats)}g fats across ${dayMeals.length} logged ${dayMeals.length === 1 ? "food" : "foods"}. Keep it up!`;
}

export default function DailyMealTracker({ userId = "guest" }) {
  const today = dateKey(new Date());
  const [data, setData] = useState(null);
  const [selectedDate, setSelectedDate] = useState(today);
  const [modalMealType, setModalMealType] = useState(null);
  const [chartPeriod, setChartPeriod] = useState("week");
  const [waterAmount, setWaterAmount] = useState("250");
  const [editingGoal, setEditingGoal] = useState(false);
  const [goalInput, setGoalInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [waterSaving, setWaterSaving] = useState(false);
  const [goalSaving, setGoalSaving] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getNutritionData(userId)
      .then(result => { if (active) { setData(result); setError(""); } })
      .catch(loadError => { if (active) setError(loadError.message || "Could not load your saved meal tracker data."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [userId, loadAttempt]);

  const dayMeals = useMemo(() => data ? data.meals.filter(meal => meal.date === selectedDate) : [], [data, selectedDate]);
  const totals = useMemo(() => dayMeals.reduce((total, meal) => ({
    calories: total.calories + meal.calories,
    protein: total.protein + meal.protein,
    carbs: total.carbs + meal.carbs,
    fats: total.fats + meal.fats
  }), { calories: 0, protein: 0, carbs: 0, fats: 0 }), [dayMeals]);
  const water = data?.waterByDate[selectedDate] || 0;

  if (loading) return <div className="tracker-loading" role="status">Loading your meal tracker…</div>;
  if (!data) return <div className="journey-load-error" role="alert"><h2>Food journal unavailable</h2><p>{error}</p><button className="journey-primary-button" type="button" onClick={() => setLoadAttempt(value => value + 1)}>Try again</button></div>;

  async function addFood(food) {
    const savedFood = await addFoodEntry(food, selectedDate);
    setData(current => ({ ...current, meals: [...current.meals, savedFood] }));
    setError("");
    setModalMealType(null);
  }

  async function removeFood(id) {
    try {
      await removeFoodEntry(id);
      setData(current => ({ ...current, meals: current.meals.filter(meal => meal.id !== id) }));
      setError("");
    } catch (removeError) {
      setError(removeError.message || "The food entry could not be removed.");
    }
  }

  async function addWater(event) {
    event.preventDefault();
    const amount = Number(waterAmount);
    if (!Number.isFinite(amount) || amount <= 0 || amount > 3000) {
      setError("Enter a water amount between 1 and 3,000 ml.");
      return;
    }
    setWaterSaving(true);
    try {
      await addWaterEntry(selectedDate, amount);
      setData(current => ({ ...current, waterByDate: { ...current.waterByDate, [selectedDate]: water + amount } }));
      setError("");
    } catch (waterError) {
      setError(waterError.message || "Your water intake could not be saved.");
    } finally {
      setWaterSaving(false);
    }
  }

  async function addQuickWater(amount) {
    setWaterAmount(String(amount));
    setWaterSaving(true);
    try {
      await addWaterEntry(selectedDate, amount);
      setData(current => ({ ...current, waterByDate: { ...current.waterByDate, [selectedDate]: water + amount } }));
      setError("");
    } catch (waterError) {
      setError(waterError.message || "Your water intake could not be saved.");
    } finally {
      setWaterSaving(false);
    }
  }

  async function saveGoal(event) {
    event.preventDefault();
    const goal = Number(goalInput);
    if (!Number.isFinite(goal) || goal < 500 || goal > 10000) {
      setError("Your calorie goal must be between 500 and 10,000 kcal.");
      return;
    }
    setGoalSaving(true);
    try {
      const settings = await saveNutritionSettings({ ...data, calorieGoal: goal });
      setData(current => ({ ...current, ...settings }));
      setError("");
      setEditingGoal(false);
    } catch (goalError) {
      setError(goalError.message || "Your calorie goal could not be saved.");
    } finally {
      setGoalSaving(false);
    }
  }

  const selectedDateObject = new Date(`${selectedDate}T12:00:00`);
  const isToday = selectedDate === today;
  const calorieProgress = Math.min(totals.calories / data.calorieGoal * 100, 100);
  const insight = getInsight(totals, data.calorieGoal, data.meals, selectedDate);

  return (
    <div className="daily-tracker">
      <div className="tracker-page-heading">
        <div>
          <span className="tracker-eyebrow">YOUR NUTRITION JOURNAL</span>
          <h1>Daily Meal Tracker</h1>
          <p>Small, mindful choices add up. See how your day is nourishing you.</p>
        </div>
        <div className="tracker-date-navigator">
          <button type="button" className="tracker-icon-button" aria-label="Previous day" onClick={() => setSelectedDate(shiftDate(selectedDate, -1))}><ChevronLeft size={19} /></button>
          <label className="tracker-date-picker"><CalendarDays size={17} /><input type="date" value={selectedDate} onChange={event => event.target.value && setSelectedDate(event.target.value)} aria-label="Choose tracker date" /></label>
          <button type="button" className="tracker-icon-button" aria-label="Next day" onClick={() => setSelectedDate(shiftDate(selectedDate, 1))}><ChevronRight size={19} /></button>
          {!isToday && <button type="button" className="tracker-today-button" onClick={() => setSelectedDate(today)}>Today</button>}
        </div>
      </div>

      {error && <div className="tracker-error" role="alert">{error}<button type="button" aria-label="Dismiss error" onClick={() => setError("")}>×</button></div>}

      <section className="tracker-summary">
        <div className="tracker-summary-copy">
          <span className="tracker-summary-kicker"><Activity size={14} /> {isToday ? "TODAY'S NUTRITION" : selectedDateObject.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" }).toUpperCase()}</span>
          <h2>{Math.round(totals.calories).toLocaleString()} <small>kcal</small></h2>
          <p>of {data.calorieGoal.toLocaleString()} kcal daily goal</p>
          <div className="tracker-goal-progress"><span style={{ width: `${calorieProgress}%` }} /></div>
          <span className="tracker-summary-remaining">{Math.max(0, data.calorieGoal - Math.round(totals.calories)).toLocaleString()} kcal remaining</span>
        </div>
        <div className="tracker-summary-ring" style={{ "--progress": `${calorieProgress * 3.6}deg` }} aria-label={`${Math.round(calorieProgress)} percent of calorie goal`}>
          <div><Flame size={19} /><strong>{Math.round(calorieProgress)}%</strong><span>of goal</span></div>
        </div>
        <button type="button" className="tracker-edit-goal" onClick={() => { setGoalInput(String(data.calorieGoal)); setEditingGoal(!editingGoal); }}><Target size={15} /> Edit goal</button>
        {editingGoal && <form className="tracker-goal-form" onSubmit={saveGoal}><label htmlFor="tracker-calorie-goal">Daily goal (kcal)</label><input id="tracker-calorie-goal" type="number" min="500" max="10000" value={goalInput} onChange={event => setGoalInput(event.target.value)} /><button type="submit" disabled={goalSaving}>{goalSaving ? "Saving…" : "Save"}</button></form>}
      </section>

      <div className="tracker-macro-grid">
        {[["Protein", totals.protein, "g", "protein"], ["Carbohydrates", totals.carbs, "g", "carbs"], ["Fats", totals.fats, "g", "fats"]].map(([label, amount, unit, kind]) => (
          <div className={`tracker-macro-card tracker-macro-${kind}`} key={label}><span>{label}</span><strong>{formatNutrient(amount)}<small>{unit}</small></strong><div><i style={{ width: `${Math.min(amount / (kind === "protein" ? 100 : kind === "carbs" ? 300 : 100) * 100, 100)}%` }} /></div><small>From your logged foods</small></div>
        ))}
      </div>

      <section className="tracker-meals-section">
        <div className="tracker-section-heading"><div><h2>Your meals</h2><p>Log what you eat to keep your nutrition on track.</p></div><span>{dayMeals.length} {dayMeals.length === 1 ? "food" : "foods"} logged</span></div>
        <div className="tracker-meal-grid">
          {mealTypes.map(mealType => {
            const meals = dayMeals.filter(meal => meal.mealType === mealType);
            const calories = meals.reduce((sum, meal) => sum + meal.calories, 0);
            return <section className="tracker-meal-card" key={mealType}>
              <div className="tracker-meal-heading"><div className={`tracker-meal-icon tracker-meal-icon-${mealType.toLowerCase()}`}>{mealType === "Breakfast" ? "☀️" : mealType === "Lunch" ? "🥗" : mealType === "Snacks" ? "🍎" : "🌙"}</div><div><h3>{mealType}</h3><span>{Math.round(calories)} kcal</span></div><button type="button" className="tracker-add-button" aria-label={`Add food to ${mealType}`} onClick={() => setModalMealType(mealType)}><Plus size={17} /><span>Add food</span></button></div>
              {meals.length ? <div className="tracker-food-list">{meals.map(meal => <div className="tracker-logged-food" key={meal.id}><span className="tracker-logged-emoji">{meal.emoji}</span><div className="tracker-logged-copy"><strong>{meal.foodName}</strong><small>{formatNutrient(meal.quantity)} × {meal.servingLabel} · {Math.round(meal.servingGrams * meal.quantity)} g</small></div><div className="tracker-logged-nutrition"><strong>{Math.round(meal.calories)} kcal</strong><small>P {formatNutrient(meal.protein)} · C {formatNutrient(meal.carbs)} · F {formatNutrient(meal.fats)}g</small></div><button type="button" className="tracker-remove-button" aria-label={`Remove ${meal.foodName}`} onClick={() => removeFood(meal.id)}><Trash2 size={15} /></button></div>)}</div> : <p className="tracker-meal-empty">Nothing logged yet. Add a food to get started.</p>}
            </section>;
          })}
        </div>
      </section>

      <div className="tracker-insights-row">
        <section className="tracker-panel tracker-water-panel">
          <div className="tracker-panel-heading"><div><h2>Water intake</h2><p>Stay hydrated, one glass at a time</p></div><span className="tracker-water-icon"><Droplets size={19} /></span></div>
          <div className="tracker-water-totals"><strong>{(water / 1000).toFixed(2).replace(/0+$/, "").replace(/\.$/, "")}<small> L</small></strong><span>of {(data.waterGoal / 1000).toFixed(1)} L goal</span></div>
          <div className="tracker-water-track"><span style={{ width: `${Math.min(water / data.waterGoal * 100, 100)}%` }} /></div>
          <form className="tracker-water-form" onSubmit={addWater}><label className="tracker-sr-only" htmlFor="tracker-water-amount">Water amount in millilitres</label><input id="tracker-water-amount" type="number" min="1" max="3000" step="50" value={waterAmount} onChange={event => setWaterAmount(event.target.value)} /><span>ml</span><button type="submit" disabled={waterSaving}>{waterSaving ? "Saving…" : <><Plus size={15} /> Log water</>}</button></form>
          <div className="tracker-water-presets"><span>Quick add</span>{[150, 250, 500].map(amount => <button type="button" key={amount} disabled={waterSaving} onClick={() => addQuickWater(amount)}>{amount} ml</button>)}</div>
        </section>
        <section className="tracker-panel tracker-insight-panel"><div className="tracker-panel-heading"><div><h2>Nutrition insights</h2><p>Personalized from your logged foods</p></div><span className="tracker-insight-icon"><Sparkles size={18} /></span></div><div className="tracker-insight-message">{insight}</div><span className="tracker-insight-footnote">Based on your entries for {isToday ? "today" : selectedDateObject.toLocaleDateString(undefined, { month: "short", day: "numeric" })} · Not medical advice</span></section>
      </div>

      <div className="tracker-history-grid">
        <NutritionChart meals={data.meals} calorieGoal={data.calorieGoal} period={chartPeriod} onPeriodChange={setChartPeriod} />
        <MealHistoryCalendar meals={data.meals} selectedDate={selectedDate} onSelectDate={setSelectedDate} />
      </div>
      <p className="tracker-data-note">Your food and water logs are saved to your NutriPath account. Nutrition values are estimates and may vary by recipe and preparation.</p>
      {modalMealType && <MealFoodModal mealType={modalMealType} onClose={() => setModalMealType(null)} onAdd={addFood} />}
    </div>
  );
}
